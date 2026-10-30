import re
from datetime import date, datetime

FORMATS = [
    "%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
    "%d/%m/%Y", "%d-%m-%Y", "%d %b, %Y", "%d %B, %Y",
]

# Words that would otherwise count as a "skill match" on almost any listing.
STOPWORDS = {
    "a", "an", "and", "or", "of", "the", "in", "on", "for", "to", "with", "at",
    "by", "is", "are", "year", "yr", "st", "nd", "rd", "th",
}


def parse_date(s):
    """Return a date, or None if it can't be parsed (e.g. 'Rolling')."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    # ISO datetimes such as 2026-10-30T10:00:00Z / 2026-10-30 23:59:00
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for f in FORMATS:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


def label(score):
    return "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"


def next_steps(opp):
    return ["Review details", "Check eligibility", "Prepare documents", "Apply before deadline"]


def _as_list(v):
    """Profiles come from the network: tolerate None / a bare string / mixed types."""
    if v is None:
        return []
    if isinstance(v, (list, tuple, set)):
        return [str(x) for x in v if x]
    return [str(v)]


def _words(text):
    return {w for w in re.findall(r"\b\w+\b", text.lower()) if w not in STOPWORDS}


def score(profile, opp, today=None):
    today = today or date.today()

    # 1. Opportunity text -> standalone words (word match, not substring: fixes the "c" bug)
    raw_text = " ".join([
        str(opp.get("title", "")), str(opp.get("organizer", "")),
        str(opp.get("eligibility", "")), " ".join(map(str, opp.get("skills", []) or [])),
        str(opp.get("type", "")),
    ])
    text_words = _words(raw_text)

    # 2. Profile -> standalone words
    profile_strings = (
        _as_list(profile.get("skills"))
        + _as_list(profile.get("interests"))
        + _as_list(profile.get("branch"))
    )
    profile_words = _words(" ".join(profile_strings))

    # 3. 20 points per keyword match, capped at 60
    hits = len(profile_words & text_words)
    pts = min(hits * 20, 60)

    # 4. Location
    loc = str(opp.get("location", "")).lower()
    my_loc = str(profile.get("location") or "").lower().strip()
    if my_loc and my_loc in loc:
        pts += 15
    elif any(w in loc for w in ("remote", "india", "global", "online")):
        pts += 8

    # 5. Deadline (unparseable / missing -> kept, but gets no urgency points)
    d = parse_date(opp.get("deadline"))
    days = None
    if d:
        days = (d - today).days
        if days < 0:
            return None  # expired
        pts += 25 if days <= 7 else 15 if days <= 30 else 5

    return min(pts, 100), days


def rank(profile, opps, kind=None):
    out = []
    for o in opps:
        if not isinstance(o, dict):
            continue
        if kind and o.get("type") != kind:
            continue
        r = score(profile, o)
        if r is None:
            continue
        s, days = r
        out.append({**o, "match_score": s, "match": label(s), "days_left": days, "next_steps": next_steps(o)})

    # Highest score first; ties -> closest deadline first
    return sorted(out, key=lambda x: (-x["match_score"], x["days_left"] if x["days_left"] is not None else 9999))
