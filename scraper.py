import hashlib
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 20


# ─── Platform detection ────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    if "myworkdayjobs.com" in url:
        return "workday"
    if "oraclecloud.com" in url or "fa.ocs." in url:
        return "oracle"
    if "taleo.net" in url or ".tal.net" in url:
        return "taleo"
    if "eightfold.ai" in url:
        return "eightfold"
    return "generic"


# ─── Workday ───────────────────────────────────────────────────────────────────

def _workday_api_url(url: str) -> str:
    """
    https://nomura.wd3.myworkdayjobs.com/Students
    → https://nomura.wd3.myworkdayjobs.com/wday/cxs/nomura/Students/jobs
    """
    parsed = urlparse(url)
    host = parsed.netloc                   # e.g. nomura.wd3.myworkdayjobs.com
    company = host.split(".")[0]           # e.g. nomura
    board = parsed.path.strip("/")         # e.g. Students
    return f"https://{host}/wday/cxs/{company}/{board}/jobs"


def scrape_workday(url: str) -> dict:
    api_url = _workday_api_url(url)
    try:
        resp = requests.post(
            api_url,
            json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        host = urlparse(url).netloc
        jobs = [
            {
                "id": j.get("externalPath", ""),
                "title": j.get("title", ""),
                "location": j.get("locationsText", ""),
                "url": f"https://{host}{j.get('externalPath', '')}",
                "posted": j.get("postedOnDate", ""),
            }
            for j in data.get("jobPostings", [])
        ]
        return {"platform": "workday", "jobs": jobs, "error": None}
    except Exception as exc:
        return {"platform": "workday", "jobs": [], "error": str(exc)}


# ─── Generic (hash-based) ──────────────────────────────────────────────────────

def _extract_text(html: str) -> str:
    """Strip scripts/styles and return visible text."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "meta"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def scrape_generic(url: str) -> dict:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        text = _extract_text(resp.text)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return {"platform": "generic", "hash": content_hash, "error": None}
    except Exception as exc:
        return {"platform": "generic", "hash": None, "error": str(exc)}


# ─── Main entry point ──────────────────────────────────────────────────────────

def check_site(company: str, url: str) -> dict:
    platform = detect_platform(url)
    print(f"  [{platform.upper()}] {company}")
    time.sleep(1.5)                        # Be polite — small delay between requests
    if platform == "workday":
        return scrape_workday(url)
    else:
        # Oracle HCM, Taleo, Eightfold and custom sites all fall back to hash comparison.
        # They are often JS-rendered so we can't parse individual jobs,
        # but we CAN detect when the page content changes.
        return scrape_generic(url)


def is_internship(title: str, keywords: list) -> bool:
    """Return True if the job title matches any internship keyword."""
    if not keywords:
        return True
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)
