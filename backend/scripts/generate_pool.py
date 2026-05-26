"""
Generate a pool of deals locally and save to backend/pool/*.ndjson.

Run: python -m scripts.generate_pool --count 50 --concurrency 2
Requires ANTHROPIC_API_KEY in env. Commit the resulting backend/pool/ dir.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Make sibling modules importable when run as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator import generate_complete_deal, _OutputTokenLimiter, _model_output_tpm
from random_config import generate_random_config

POOL_DIR = Path(__file__).parent.parent / "pool"


async def main(count: int, concurrency: int) -> None:
    POOL_DIR.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    limiter = _OutputTokenLimiter(_model_output_tpm())
    done = [0]
    failed = [0]
    start = time.time()

    async def worker(i: int) -> None:
        async with sem:
            cfg = generate_random_config({})
            label = f"[{i+1}/{count}] {cfg['industry']} / {cfg['deal_size']} / {cfg['complexity']}"
            print(f"{label}  …", flush=True)
            try:
                result = await generate_complete_deal(cfg, external_limiter=limiter)
                deal_id = result["deal_id"]
                metadata = result["metadata"]
                events = result["events"]
                metadata["filename"] = f"pool_{deal_id}.ndjson"
                with open(POOL_DIR / f"pool_{deal_id}.ndjson", "w") as f:
                    f.write(json.dumps(metadata) + "\n")
                    for ev in events:
                        f.write(json.dumps(ev) + "\n")
                done[0] += 1
                elapsed = time.time() - start
                print(
                    f"  ✓ {label} → {len(events)} events  "
                    f"({done[0]+failed[0]}/{count} in {elapsed:.0f}s)",
                    flush=True,
                )
            except Exception as e:
                failed[0] += 1
                print(f"  ✗ {label} FAILED: {e}", flush=True)

    await asyncio.gather(*[worker(i) for i in range(count)])

    elapsed = time.time() - start
    pool_count = len(list(POOL_DIR.glob("*.ndjson")))
    print(
        f"\nDone in {elapsed:.0f}s. "
        f"Generated {done[0]}, failed {failed[0]}. Pool dir total: {pool_count}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(main(args.count, args.concurrency))
