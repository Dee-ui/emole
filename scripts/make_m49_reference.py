"""make_m49_reference.py: turn the UN M49 region list into data/reference/un_m49.csv.

You do NOT need to run this for a normal build. Its output (un_m49.csv) is committed,
so the build works offline. Run it only if the UN changes its regions and you want
to refresh the file.

Where the data comes from
  The UN Statistics Division publishes the M49 standard (which country sits in which
  region) at https://unstats.un.org/unsd/methodology/m49/ but offers no stable file
  link, because its download buttons are made by JavaScript. The open-source package
  "un-m49" (MIT licence, by Titus Wormer) holds the same list as code, so we read that.

What it writes (one row per country or area that has an ISO code)
  iso3, m49_code, name, continent, m49_subregion, intermediate_region, subregion
  "subregion" is the most specific level: the intermediate region when M49 has one
  (Nigeria -> Western Africa), otherwise the M49 subregion (Egypt -> Northern Africa).

Run:  python scripts/make_m49_reference.py
      python scripts/make_m49_reference.py --file path/to/index.js   (use a saved copy)
"""
import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "reference" / "un_m49.csv"
URL = "https://raw.githubusercontent.com/wooorm/un-m49/main/index.js"
# A name is written in 'single quotes', or in "double quotes" when it holds an
# apostrophe ("Lao People's Democratic Republic"). Both forms must match, or those
# countries silently go missing (this happened on the first run: North Korea and Laos).
ENTRY = re.compile(r"\{\s*type:\s*(\d),\s*name:\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"),"
                   r"\s*code:\s*'(\d{3})'"
                   r"(?:,\s*iso3166:\s*'([A-Z]{3})')?(?:,\s*parent:\s*'(\d{3})')?\s*\}")


def parse(text: str) -> list:
    rows = []
    for m in ENTRY.finditer(text):
        name = (m[2] if m[2] is not None else m[3]).replace("\\'", "'")
        rows.append({"type": int(m[1]), "name": name, "code": m[4], "iso3": m[5], "parent": m[6]})
    expected = len(re.findall(r"\btype:\s*\d", text))
    if len(rows) != expected:
        sys.exit(f"Parsed {len(rows)} entries but the file has {expected}: check the pattern.")
    return rows


def build(rows: list) -> list:
    by_code = {r["code"]: r for r in rows}
    out = []
    for r in rows:
        if r["type"] != 4 or not r["iso3"]:
            continue
        level = {1: "", 2: "", 3: ""}
        parent = r["parent"]
        while parent and parent in by_code:
            p = by_code[parent]
            if p["type"] in level:
                level[p["type"]] = p["name"]
            parent = p["parent"]
        out.append({"iso3": r["iso3"], "m49_code": r["code"], "name": r["name"],
                    "continent": level[1], "m49_subregion": level[2],
                    "intermediate_region": level[3],
                    "subregion": level[3] or level[2]})
    return sorted(out, key=lambda x: x["iso3"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="read a saved copy of un-m49's index.js instead of downloading")
    args = ap.parse_args()
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        resp = requests.get(URL, timeout=60, headers={"User-Agent": "EmoleDataBuild/0.1"})
        resp.raise_for_status()
        text = resp.text
    rows = build(parse(text))
    if len(rows) < 240:
        sys.exit(f"Only {len(rows)} countries parsed: the package format may have changed.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    print(f"Wrote {len(rows)} countries and areas to {OUT}")
    print(f"Source fingerprint (sha256, first 16): {digest}  (record it in docs/DATA.md)")


if __name__ == "__main__":
    main()
