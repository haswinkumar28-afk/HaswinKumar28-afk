from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import store
from rank import rank

load_dotenv()

VALID_KINDS = {"internship", "hackathon", "scholarship"}

app = FastAPI()

# The frontend sends no cookies/credentials, so credentials stay off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "CampusCopilot Backend is running!"}


@app.get("/health")
def health():
    # The frontend polls this to decide whether to show "FastAPI Connected".
    return {"ok": True}


@app.post("/search")
def search(
    profile: dict,
    live: bool = Query(False),
    kind: Optional[str] = Query(None),
):
    if kind in (None, "", "all"):
        kind = None
    elif kind not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {sorted(VALID_KINDS)} or 'all'")

    source, warning = "cache", None

    if live:
        # Imported lazily so a missing `tinyfish` package doesn't stop the whole
        # server from starting, and so the real error is reported (not swallowed).
        try:
            from fetch import fetch_all
            opportunities = fetch_all()
        except ImportError as e:
            raise HTTPException(status_code=503, detail=f"Live scan unavailable (import failed): {e}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Live scan failed: {type(e).__name__}: {e}")

        print(f"[search] TinyFish returned {len(opportunities)} items")
        if opportunities:
            source = "live"
        else:
            warning = "Live scan returned no results (check TINYFISH_API_KEY / server logs); showing cached results."
            opportunities = store.load()
    else:
        opportunities = store.load()

    results = rank(profile, opportunities, kind)
    return {"count": len(results), "results": results, "source": source, "warning": warning}
