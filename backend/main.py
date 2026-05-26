"""
FastAPI application for Ycrest Mock Deal Generator.
6 endpoints: POST /generate-stream, POST /generate-series-stream, POST /bulk-generate-stream, GET /deals, GET /deals/{id}, DELETE /deals/{id}
"""

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
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
    TokenUsage,
)
from generator import generate_complete_deal, _OutputTokenLimiter, _model_output_tpm
from file_handler import write_deal, read_deal, list_deal_files, delete_deal, find_deal_file
from random_config import generate_random_config, series_to_generate_config
from pool_loader import load_pool, pool_size
from pool_substitution import substitute_deal
import random as _random

# Load environment variables from .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Ycrest Mock Deal Generator",
    description="Generate synthetic B2B sales deals with LLM",
    version="1.0.0"
)

# CORS: allow all origins in production (Ycrest and frontend can be deployed anywhere).
# Set ALLOWED_ORIGINS to a comma-separated list to restrict (e.g. "https://myapp.up.railway.app").
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_allow_all = _raw_origins.strip() == "*"
_origins = ["*"] if _allow_all else [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key auth — all /api/* routes require X-API-Key header matching API_KEY env var.
_API_KEY = os.getenv("API_KEY", "")

async def require_api_key(request: Request):
    if not _API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")
    if request.headers.get("X-API-Key") != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

api = APIRouter(prefix="/api", dependencies=[Depends(require_api_key)])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Pool-serving mode: when USE_POOL=true, bulk-generate-stream serves pre-generated
# deals from backend/pool/ with light substitution instead of calling Claude.
_USE_POOL = os.getenv("USE_POOL", "false").lower() == "true"
_POOL_PACE_MS = int(os.getenv("POOL_PACE_MS", "200"))
if _USE_POOL:
    load_pool()
    logger.info(f"Pool mode ENABLED. Loaded {pool_size()} deals.")

@api.post("/generate-stream")
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
                },
                "token_usage": deal_result.get('token_usage'),
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

@api.post("/generate-series-stream")
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
                "deal": {"metadata": deal_result['metadata'], "events": deal_result['events']},
                "token_usage": deal_result.get('token_usage'),
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

@api.post("/generate", response_model=GenerateResponse)
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
            ),
            token_usage=deal_result.get('token_usage'),
        )

    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@api.get("/deals", response_model=DealsListResponse)
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

@api.get("/deals/{deal_id}", response_model=DealResponse)
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

@api.delete("/deals/{deal_id}", response_model=SuccessResponse)
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

@api.post("/bulk-generate-stream")
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

    async def run_pool_bulk():
        pool = load_pool()
        if not pool:
            await queue.put({"type": "bulk_complete", "total": count, "completed": 0, "failed": count})
            return
        overrides = request.overrides or {}
        completed = 0
        failed = 0
        for i in range(count):
            deal_number = i + 1
            await queue.put({"type": "deal_start", "deal_number": deal_number, "total": count})
            try:
                source = _random.choice(pool)
                new_deal = substitute_deal(
                    source,
                    vendor_company=overrides.get("vendor_company"),
                    ae_name=overrides.get("ae_name"),
                    se_name=overrides.get("se_name"),
                    industry=overrides.get("industry"),
                    deal_size=overrides.get("deal_size"),
                    customer_company=overrides.get("company_name"),
                )
                filename = await write_deal(
                    new_deal["metadata"]["deal_id"],
                    new_deal["metadata"],
                    new_deal["events"],
                )
                completed += 1
                await queue.put({
                    "type": "deal_complete",
                    "deal_number": deal_number,
                    "total": count,
                    "completed": completed,
                    "deal_id": new_deal["metadata"]["deal_id"],
                    "filename": filename,
                })
            except Exception as e:
                failed += 1
                logger.error(f"Pool deal {deal_number} failed: {e}")
                await queue.put({
                    "type": "deal_error",
                    "deal_number": deal_number,
                    "total": count,
                    "message": str(e),
                })
            if _POOL_PACE_MS > 0:
                await asyncio.sleep(_POOL_PACE_MS / 1000.0)
        await queue.put({"type": "bulk_complete", "total": count, "completed": completed, "failed": failed})

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

    if _USE_POOL and pool_size() > 0:
        asyncio.create_task(run_pool_bulk())
    else:
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


@api.get("/pool/status")
async def pool_status():
    """Diagnostic: is pool mode on, and how many deals are loaded?"""
    return {
        "use_pool": _USE_POOL,
        "pool_size": pool_size(),
        "pool_pace_ms": _POOL_PACE_MS,
    }


app.include_router(api)


@app.get("/")
async def root():
    return {"message": "Ycrest Mock Deal Generator API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
