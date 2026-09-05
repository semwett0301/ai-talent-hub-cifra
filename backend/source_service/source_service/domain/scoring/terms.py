"""URL vocabulary that is about *neither* entity in particular — both rule sets read it.

Anything specific to one entity lives with that entity: `ARTICLE_PATH_TERMS` in
`article/rules/scoring.py`, `HUB_TERMS` and `DATE_LIKE_RE` in `hub/rules/scoring.py`.
"""

import re

# Sections and utility pages: a penalty for an article, a penalty for a hub.
SECTION_OR_JUNK_TERMS = (
    "/tag/",
    "/tags/",
    "/category/",
    "/categories/",
    "/author/",
    "/authors/",
    "/search",
    "/calendar",
    "/contacts",
    "/contact",
    "/about",
    "/products",
    "/services",
    "/catalog",
    "/vacanc",
    "/career",
    "/login",
    "/privacy",
    "/terms",
    "/newsletter",
    "/subscription",
    "/subscribe",
    "/feed",
    "/taxonomy/",
    "/events",
    "/event/",
)
# Article-shaped URL markers: a bonus for an article, a penalty for a hub.
DATE_IN_PATH_RE = re.compile(r"/(20\d{2})[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])(?:/|$)")
NUMERIC_ID_RE = re.compile(r"/(?:\d{5,})(?:/|\.html?$|$)", re.IGNORECASE)
LONG_SLUG_RE = re.compile(r"/[a-zа-я0-9][a-zа-я0-9_-]{18,}(?:/|\.html?$|$)", re.IGNORECASE)
