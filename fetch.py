import json
import re
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from tinyfish import TinyFish, CompleteEvent

from sources import SOURCES
import store

# Load TINYFISH_API_KEY from .env before TinyFish initializes
load_dotenv()


def _to_list(result):
    """TinyFish result can be dict, list or JSON string. Pull out the list."""
    if isinstance(result, str):
        # Strip markdown fences (```json ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result.strip(), flags=re.IGNORECASE)
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[fetch] JSON parse error: {e} | raw: {cleaned[:300]}")
            return []

    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        if isinstance(result.get("opportunities"), list):
            return result["opportunities"]
        for v in result.values():
            if isinstance(v, list):
                return v
    return []


def run_source(src):
    # Client creation is inside the try so a missing/invalid key only fails
    # this source instead of crashing the whole request with a 500.
    try:
        client = TinyFish()  # reads TINYFISH_API_KEY from environment
        with client.agent.stream(url=src["url"], goal=src["goal"]) as stream:
            for event in stream:
                if isinstance(event, CompleteEvent):
                    items = [i for i in _to_list(event.result_json) if isinstance(i, dict)]
                    for it in items:
                        it["type"] = src["type"]
                        it["source_url"] = src["url"]
                    return items
    except Exception as e:
        print(f"[fetch] {src['url']} failed: {type(e).__name__}: {e}")
    return []


def _dedupe(items):
    seen, out = set(), []
    for it in items:
        key = (str(it.get("apply_url") or "").strip() or str(it.get("title") or "").strip().lower())
        if key and key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def fetch_all():
    if not SOURCES:
        return []
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        results = list(pool.map(run_source, SOURCES))
    items = _dedupe([i for r in results for i in r])
    if items:  # only overwrite the cache if we actually got something
        store.save(items)
    return items
