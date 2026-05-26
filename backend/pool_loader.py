"""
Load pre-generated pool of deals from backend/pool/ into memory on startup.
Pool files are NDJson: line 1 metadata, lines 2+ events (same format as deals/).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

POOL_DIR = Path(__file__).parent / "pool"
_pool: List[Dict[str, Any]] = []


def load_pool(force: bool = False) -> List[Dict[str, Any]]:
    """Load all pool .ndjson files into memory. Idempotent unless force=True."""
    global _pool
    if _pool and not force:
        return _pool
    _pool = []
    if not POOL_DIR.exists():
        logger.warning(f"Pool dir {POOL_DIR} does not exist; pool serving disabled")
        return _pool

    for fp in sorted(POOL_DIR.glob("*.ndjson")):
        try:
            with open(fp) as f:
                lines = [ln for ln in f.read().splitlines() if ln.strip()]
            if not lines:
                continue
            metadata = json.loads(lines[0])
            events = [json.loads(ln) for ln in lines[1:]]
            _pool.append({"metadata": metadata, "events": events})
        except Exception as e:
            logger.error(f"Failed to load pool file {fp.name}: {e}")

    logger.info(f"Loaded {len(_pool)} pool deals from {POOL_DIR}")
    return _pool


def pool_size() -> int:
    return len(_pool) if _pool else 0
