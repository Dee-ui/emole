"""fetch.py: download the source files politely and keep dated copies in data/raw/.

File names carry the download date, for example
    data/raw/owid_air-passengers-carried__2026-11-08.csv
    data/raw/wb_IS.AIR.DPRT__2026-11-08.json
    data/raw/wb_countries__2026-11-08.json
A file that is already there is reused, so a second build makes no downloads.
Pass --refresh to the build script to download fresh copies (old ones are kept,
the newest one is used).
"""
import datetime as dt
import json
import re
import time
from pathlib import Path

import requests

from emole import config

_DATE = re.compile(r"__(\d{4}-\d{2}-\d{2})\.(csv|json)$")


class DownloadError(RuntimeError):
    """A source could not be downloaded after several tries."""


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT})
    return s


def get(url: str, session: requests.Session = None) -> requests.Response:
    """GET with a few retries and a pause between them. Raises DownloadError with a
    plain message (including the HTTP status) if it never works."""
    session = session or _session()
    last = ""
    for attempt in range(1, config.HTTP_RETRIES + 1):
        try:
            resp = session.get(url, timeout=config.HTTP_TIMEOUT_SEC)
            if resp.status_code == 200:
                return resp
            last = f"HTTP {resp.status_code}"
            if resp.status_code in (400, 401, 403, 404):
                break                                   # retrying will not help
        except requests.RequestException as e:
            last = type(e).__name__
        time.sleep(2 * attempt)
    raise DownloadError(f"Could not download {url} ({last}). Check your internet connection "
                        "and open the link in a browser to see whether the source moved.")


def raw_path(name: str, ext: str, day: dt.date = None, raw_dir: Path = None) -> Path:
    raw_dir = Path(raw_dir or config.RAW_DIR)
    return raw_dir / f"{name}__{(day or dt.date.today()).isoformat()}.{ext}"


def latest_raw(name: str, ext: str, raw_dir: Path = None):
    """The newest downloaded copy of a source, or None."""
    raw_dir = Path(raw_dir or config.RAW_DIR)
    found = []
    for p in raw_dir.glob(f"{name}__*.{ext}"):
        m = _DATE.search(p.name)
        if m and p.name[: -len(m.group(0))] == name:
            found.append((m.group(1), p))
    return max(found)[1] if found else None


def download_date(path: Path) -> str:
    m = _DATE.search(Path(path).name)
    return m.group(1) if m else ""


def owid_name(slug: str) -> str:
    return f"owid_{slug}"


def wb_name(code: str) -> str:
    return f"wb_{code}"


def fetch_owid(slug: str, refresh: bool = False, offline: bool = False, raw_dir: Path = None) -> Path:
    name = owid_name(slug)
    existing = latest_raw(name, "csv", raw_dir)
    if existing and not refresh:
        return existing
    if offline:
        if existing:
            return existing
        raise DownloadError(f"No saved copy of OWID chart '{slug}' in data/raw and --offline was given.")
    resp = get(config.OWID_CSV_URL.format(slug=slug))
    # OWID's header casing and extra columns have changed over time (for example a lowercase
    # "entity,code,year" header, and a new "owid_region" metadata column), so this only checks
    # that the three key columns are present at the start, without caring about their case.
    if not resp.text.lstrip()[:20].lower().startswith("entity,code,year"):
        raise DownloadError(f"OWID chart '{slug}' did not return the expected CSV "
                            f"(first characters: {resp.text[:60]!r}).")
    path = raw_path(name, "csv", raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return path


def fetch_wb_indicator(code: str, refresh: bool = False, offline: bool = False,
                       raw_dir: Path = None) -> Path:
    """Every page of a World Bank indicator, saved as one JSON file:
    {"meta": {...first page's header...}, "records": [...all rows...]}"""
    name = wb_name(code)
    existing = latest_raw(name, "json", raw_dir)
    if existing and not refresh:
        return existing
    if offline:
        if existing:
            return existing
        raise DownloadError(f"No saved copy of World Bank indicator {code} and --offline was given.")
    session, records, meta, page, pages = _session(), [], None, 1, 1
    while page <= pages:
        url = config.WB_INDICATOR_URL.format(code=code, start=config.YEAR_MIN,
                                             end=config.YEAR_MAX, page=page)
        body = get(url, session).json()
        if not isinstance(body, list) or len(body) < 2 or body[1] is None:
            raise DownloadError(f"World Bank indicator {code} returned no data: {str(body)[:200]}")
        meta = meta or body[0]
        pages = int(body[0].get("pages", 1))
        records += body[1]
        page += 1
    path = raw_path(name, "json", raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"meta": meta, "records": records}), encoding="utf-8")
    return path


def fetch_wb_countries(refresh: bool = False, offline: bool = False, raw_dir: Path = None) -> Path:
    """The World Bank's list of economies AND aggregates, with region and income group.
    Used twice: to name each country's region and income group, and to recognise the
    World Bank's own group rows (which use 3-letter codes too, like WLD and SSF)."""
    name = "wb_countries"
    existing = latest_raw(name, "json", raw_dir)
    if existing and not refresh:
        return existing
    if offline:
        if existing:
            return existing
        raise DownloadError("No saved copy of the World Bank country list and --offline was given.")
    session, records, meta, page, pages = _session(), [], None, 1, 1
    while page <= pages:
        body = get(config.WB_COUNTRIES_URL.format(page=page), session).json()
        if not isinstance(body, list) or len(body) < 2 or body[1] is None:
            raise DownloadError(f"World Bank country list looks wrong: {str(body)[:200]}")
        meta = meta or body[0]
        pages = int(body[0].get("pages", 1))
        records += body[1]
        page += 1
    path = raw_path(name, "json", raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"meta": meta, "records": records}), encoding="utf-8")
    return path
