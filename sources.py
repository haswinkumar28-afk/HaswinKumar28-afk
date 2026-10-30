"""Pages TinyFish scans for live opportunities.

fetch.py does `from sources import SOURCES`, so this list MUST exist.
Each entry: type (hackathon | internship | scholarship), url, goal.
"""

_FIELDS = (
    "title, organizer, deadline (as YYYY-MM-DD; empty string if none), "
    "eligibility, skills (array of short strings), location, "
    "apply_url (absolute URL to apply or view the listing)"
)

_FORMAT = (
    "Return ONLY a valid JSON array of objects, no markdown and no commentary. "
    f"Each object must have exactly these keys: {_FIELDS}."
)

SOURCES = [
    {
        "type": "hackathon",
        "url": "https://devpost.com/hackathons",
        "goal": "List up to 5 currently open hackathons that are accepting submissions. " + _FORMAT,
    },
    {
        "type": "internship",
        "url": "https://internshala.com/internships/computer-science-internship",
        "goal": "List up to 5 computer-science internships that are currently open. " + _FORMAT,
    },
    {
        "type": "scholarship",
        "url": "https://scholarships.gov.in/",
        "goal": "List up to 5 scholarships open for applications right now. " + _FORMAT,
    },
]
