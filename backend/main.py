"""
FastAPI application for Ycrest Mock Deal Generator.
6 endpoints: POST /generate-stream, POST /generate-series-stream, POST /bulk-generate-stream, GET /deals, GET /deals/{id}, DELETE /deals/{id}
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
import os
from dotenv import load_dotenv

from models import (
    GenerateRequest,
    GenerateResponse,
    DealsListResponse,
    DealSummary,
    DealResponse,
    SuccessResponse,
    DealContent,
    BulkGenerateRequest,
    SeriesRequest,
)
from generator import generate_complete_deal, _OutputTokenLimiter, _model_output_tpm
from file_handler import write_deal, read_deal, list_deal_files, delete_deal, find_deal_file
from random_config import generate_random_config, series_to_generate_config

# Load environment variables from .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Ycrest Mock Deal Generator",
    description="Generate synthetic B2B sales deals with LLM",
    version="1.0.0"
)

# Add CORS middleware to allow frontend at http://localhost:5173 and 5174
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/generate-stream")
async def generate_deal_stream(request: GenerateRequest):
    """
    POST /api/generate-stream
    Generate a deal with Server-Sent Events progress updates.
    Emits: {type: "progress", step, message, progress} during generation
           {type: "complete", deal_id, filename, deal} on success
           {type: "error", message} on failure
    """
    config = request.model_dump()
    queue: asyncio.Queue = asyncio.Queue()

    async def run_generation():
        try:
            async def progress_callback(step: str, message: str, progress: int):
                await queue.put({"type": "progress", "step": step, "message": message, "progress": progress})

            deal_result = await generate_complete_deal(config, progress_callback)

            filename = await write_deal(
                deal_result['deal_id'],
                deal_result['metadata'],
                deal_result['events']
            )
            deal_result['metadata']['filename'] = filename

            await queue.put({
                "type": "complete",
                "deal_id": deal_result['deal_id'],
                "filename": filename,
                "deal": {
                    "metadata": deal_result['metadata'],
                    "events": deal_result['events']
                }
            })
        except Exception as e:
            logger.error(f"Stream generation failed: {str(e)}")
            await queue.put({"type": "error", "message": str(e)})

    asyncio.create_task(run_generation())

    async def event_stream():
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] in ("complete", "error"):
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/generate-series-stream")
async def generate_series_stream(request: SeriesRequest):
    """
    POST /api/generate-series-stream
    Convert series params to deal config, then generate with SSE progress.
    Same SSE contract as /api/generate-stream.
    """
    config = series_to_generate_config(request.model_dump())
    queue: asyncio.Queue = asyncio.Queue()

    async def run_generation():
        try:
            async def progress_callback(step: str, message: str, progress: int):
                await queue.put({"type": "progress", "step": step, "message": message, "progress": progress})

            deal_result = await generate_complete_deal(config, progress_callback)
            filename = await write_deal(
                deal_result['deal_id'], deal_result['metadata'], deal_result['events']
            )
            deal_result['metadata']['filename'] = filename
            await queue.put({
                "type": "complete",
                "deal_id": deal_result['deal_id'],
                "filename": filename,
                "deal": {"metadata": deal_result['metadata'], "events": deal_result['events']}
            })
        except Exception as e:
            logger.error(f"Series generation failed: {str(e)}")
            await queue.put({"type": "error", "message": str(e)})

    asyncio.create_task(run_generation())

    async def event_stream():
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] in ("complete", "error"):
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    )

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_deal(request: GenerateRequest):
    """
    POST /api/generate
    Generate a complete deal with 3-stage pipeline.

    Pydantic automatically validates the request body.
    Returns 422 if validation fails.
    """
    try:
        logger.info(f"Generating deal for {request.industry}")

        # Convert request to dict for generator
        config = request.model_dump()

        # Run 3-stage pipeline
        deal_result = await generate_complete_deal(config)

        # Write deal to disk and get filename
        filename = await write_deal(
            deal_result['deal_id'],
            deal_result['metadata'],
            deal_result['events']
        )

        # Update metadata with actual filename
        deal_result['metadata']['filename'] = filename

        logger.info(f"Successfully generated deal {deal_result['deal_id']}")

        return GenerateResponse(
            deal_id=deal_result['deal_id'],
            filename=filename,
            deal=DealContent(
                metadata=deal_result['metadata'],
                events=deal_result['events']
            )
        )

    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/deals", response_model=DealsListResponse)
async def list_deals():
    """
    GET /api/deals
    List all generated deals (newest first).
    Returns summary for each deal (no full events).
    """
    try:
        deals = await list_deal_files()
        return DealsListResponse(deals=deals)
    except Exception as e:
        logger.error(f"Failed to list deals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list deals: {str(e)}")

@app.get("/api/deals/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: str):
    """
    GET /api/deals/{deal_id}
    Get full deal object including all events.
    """
    try:
        # Find file containing deal_id
        filepath = find_deal_file(deal_id)

        # Read and parse
        deal_content = await read_deal(filepath)

        # Get filename from metadata
        filename = deal_content['metadata']['filename']

        return DealResponse(
            deal_id=deal_id,
            filename=filename,
            deal=DealContent(
                metadata=deal_content['metadata'],
                events=deal_content['events']
            )
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Deal not found")
    except Exception as e:
        logger.error(f"Failed to get deal {deal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get deal: {str(e)}")

@app.delete("/api/deals/{deal_id}", response_model=SuccessResponse)
async def delete_deal_endpoint(deal_id: str):
    """
    DELETE /api/deals/{deal_id}
    Delete a deal file.
    """
    try:
        await delete_deal(deal_id)
        return SuccessResponse(success=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Deal not found")
    except Exception as e:
        logger.error(f"Failed to delete deal {deal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete deal: {str(e)}")

@app.post("/api/bulk-generate-stream")
async def bulk_generate_stream(request: BulkGenerateRequest):
    """
    POST /api/bulk-generate-stream
    Generate N random deals with a shared rate limiter and bounded concurrency.
    SSE events:
      {type: "deal_start",    deal_number, total}
      {type: "deal_complete", deal_number, total, completed, deal_id, filename}
      {type: "deal_error",    deal_number, total, message}
      {type: "bulk_complete", total, completed, failed}
    """
    count = request.count
    queue: asyncio.Queue = asyncio.Queue()

    async def run_bulk():
        shared_limiter = _OutputTokenLimiter(_model_output_tpm())
        sem = asyncio.Semaphore(2)
        completed = [0]
        failed = [0]

        async def generate_one(deal_number: int):
            config = generate_random_config(request.overrides)
            await queue.put({"type": "deal_start", "deal_number": deal_number, "total": count})
            try:
                async with sem:
                    result = await generate_complete_deal(config, external_limiter=shared_limiter)
                filename = await write_deal(
                    result['deal_id'], result['metadata'], result['events']
                )
                result['metadata']['filename'] = filename
                completed[0] += 1
                await queue.put({
                    "type": "deal_complete",
                    "deal_number": deal_number,
                    "total": count,
                    "completed": completed[0],
                    "deal_id": result['deal_id'],
                    "filename": filename,
                })
            except Exception as e:
                failed[0] += 1
                logger.error(f"Bulk deal {deal_number} failed: {e}")
                await queue.put({
                    "type": "deal_error",
                    "deal_number": deal_number,
                    "total": count,
                    "message": str(e),
                })

        await asyncio.gather(*[generate_one(i + 1) for i in range(count)])
        await queue.put({"type": "bulk_complete", "total": count, "completed": completed[0], "failed": failed[0]})

    asyncio.create_task(run_bulk())

    async def event_stream():
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] == "bulk_complete":
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ycrest Mock Deal Generator API",
        "docs": "http://localhost:8000/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
