"""names.py: turn the places named in a question into exact database values, in code.

"How is Naija doing on electricity compared with West Africa and ECOWAS?"
  Naija        -> country iso3 'NGA' (Nigeria)
  West Africa  -> subregion = 'Western Africa'
  ECOWAS       -> is_ecowas

Why in code and not by the model: a name match is either right or wrong, and code is
never tired. The matches are handed to the model as NAME HINTS, so its SQL uses exact
codes and values. A capitalised place name that matches nothing gets a polite "I don't
recognise ..." with suggestions, without a model call.

Longer names are matched first, so "South Africa" is never read as "Africa" and
"Niger" is never found inside "Nigeria".
"""
import difflib
import re
import unicodedata
from dataclasses import dataclass, field

from emole.pipeline import catalog

# Other names people use -> ISO3. The country's own name in the data always works too.
COUNTRY_ALIASES = {
    "naija": "NGA", "ivory coast": "CIV", "cote d'ivoire": "CIV", "côte d'ivoire": "CIV",
    "usa": "USA", "u.s.": "USA", "u.s.a.": "USA", "us": "USA", "united states of america": "USA",
    "america": "USA", "the states": "USA",
    "uk": "GBR", "u.k.": "GBR", "britain": "GBR", "great britain": "GBR", "england": "GBR",
    "uae": "ARE", "emirates": "ARE",
    "drc": "COD", "dr congo": "COD", "dr. congo": "COD", "congo-kinshasa": "COD",
    "democratic republic of the congo": "COD",
    "congo-brazzaville": "COG", "republic of congo": "COG", "republic of the congo": "COG",
    "turkiye": "TUR", "türkiye": "TUR", "czech republic": "CZE", "swaziland": "SWZ",
    "burma": "MMR", "korea": "KOR", "republic of korea": "KOR", "dprk": "PRK",
    "russian federation": "RUS", "viet nam": "VNM", "lao pdr": "LAO", "cabo verde": "CPV",
    "the gambia": "GMB", "palestinian territories": "PSE", "state of palestine": "PSE",
    "holland": "NLD", "the netherlands": "NLD", "timor-leste": "TLS", "macau": "MAC",
    "federated states of micronesia": "FSM", "micronesia (country)": "FSM",
    "sao tome": "STP", "são tomé and príncipe": "STP", "persia": "IRN", "ksa": "SAU",
}

# Group names -> (column, value). value True = a bloc; a tuple = several values (IN).
GROUP_ALIASES = {
    "africa": ("continent", "Africa"), "asia": ("continent", "Asia"), "europe": ("continent", "Europe"),
    "oceania": ("continent", "Oceania"), "americas": ("continent", "Americas"),
    "the americas": ("continent", "Americas"),
    "west africa": ("subregion", "Western Africa"), "western africa": ("subregion", "Western Africa"),
    "east africa": ("subregion", "Eastern Africa"), "eastern africa": ("subregion", "Eastern Africa"),
    "north africa": ("subregion", "Northern Africa"), "northern africa": ("subregion", "Northern Africa"),
    "southern africa": ("subregion", "Southern Africa"),
    "central africa": ("subregion", "Middle Africa"), "middle africa": ("subregion", "Middle Africa"),
    "east asia": ("subregion", "Eastern Asia"), "eastern asia": ("subregion", "Eastern Asia"),
    "south asia": ("subregion", "Southern Asia"), "southern asia": ("subregion", "Southern Asia"),
    "southeast asia": ("subregion", "South-eastern Asia"),
    "south-east asia": ("subregion", "South-eastern Asia"),
    "south-eastern asia": ("subregion", "South-eastern Asia"),
    "central asia": ("subregion", "Central Asia"), "western asia": ("subregion", "Western Asia"),
    "eastern europe": ("subregion", "Eastern Europe"), "western europe": ("subregion", "Western Europe"),
    "northern europe": ("subregion", "Northern Europe"), "southern europe": ("subregion", "Southern Europe"),
    "caribbean": ("subregion", "Caribbean"), "the caribbean": ("subregion", "Caribbean"),
    "central america": ("subregion", "Central America"), "south america": ("subregion", "South America"),
    "north america": ("subregion", "Northern America"), "northern america": ("subregion", "Northern America"),
    "melanesia": ("subregion", "Melanesia"), "micronesia": ("subregion", "Micronesia"),
    "polynesia": ("subregion", "Polynesia"),
    "australia and new zealand": ("subregion", "Australia and New Zealand"),
    "sub-saharan africa": ("wb_region", "Sub-Saharan Africa"),
    "sub saharan africa": ("wb_region", "Sub-Saharan Africa"),
    "latin america": ("wb_region", "Latin America & Caribbean"),
    "latin america and the caribbean": ("wb_region", "Latin America & Caribbean"),
    "mena": ("wb_region", "Middle East, North Africa, Afghanistan & Pakistan"),
    "middle east and north africa": ("wb_region", "Middle East, North Africa, Afghanistan & Pakistan"),
    "east asia and pacific": ("wb_region", "East Asia & Pacific"),
    "east asia & pacific": ("wb_region", "East Asia & Pacific"),
    "europe and central asia": ("wb_region", "Europe & Central Asia"),
    "low income": ("income_group", "low"), "low-income": ("income_group", "low"),
    "lower middle income": ("income_group", "lower-middle"),
    "lower-middle income": ("income_group", "lower-middle"),
    "lower-middle-income": ("income_group", "lower-middle"),
    "upper middle income": ("income_group", "upper-middle"),
    "upper-middle income": ("income_group", "upper-middle"),
    "upper-middle-income": ("income_group", "upper-middle"),
    "middle income": ("income_group", ("lower-middle", "upper-middle")),
    "middle-income": ("income_group", ("lower-middle", "upper-middle")),
    "high income": ("income_group", "high"), "high-income": ("income_group", "high"),
    "rich countries": ("income_group", "high"),
    # adjectives: "African countries", "West African economies"
    "african": ("continent", "Africa"), "asian": ("continent", "Asia"), "european": ("continent", "Europe"),
    "west african": ("subregion", "Western Africa"), "east african": ("subregion", "Eastern Africa"),
    "north african": ("subregion", "Northern Africa"), "southern african": ("subregion", "Southern Africa"),
    "south american": ("subregion", "South America"), "central american": ("subregion", "Central America"),
    "caribbean countries": ("subregion", "Caribbean"),
    "latin american": ("wb_region", "Latin America & Caribbean"),
    "sub-saharan african": ("wb_region", "Sub-Saharan Africa"),
    "ecowas": ("is_ecowas", True), "african union": ("is_african_union", True),
    "european union": ("is_eu", True), "g20": ("is_g20", True), "g-20": ("is_g20", True),
    "middle east": ("is_middle_east", True), "middle eastern": ("is_middle_east", True),
}
# Short capital-letter names only count when written in capitals ("AU", "EU"),
# so the word "us" in "tell us" is never read as the United States.
CASE_SENSITIVE = {"AU": ("is_african_union", True), "EU": ("is_eu", True), "US": "USA",
                  "UK": "GBR", "UAE": "ARE", "DRC": "COD", "KSA": "SAU"}
WORLD = ("world", "global", "globally", "worldwide", "all countries", "every country",
         "the whole world")

# Capitalised words that are never place names (for the "I don't recognise" check).
NOT_PLACES = set("""
what which who whom whose when where why how is are was were do does did can could would should
will shall show give tell list compare rank find plot chart draw make please and or the a an in on of
for from to by with between versus vs than since during over under per about across among top bottom
highest lowest most least best worst latest current recent average total median share growth rate
gdp ppp co2 covid i me my we our you your emolé emole immy hi hello hey thanks thank okay ok yes no
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec q1 q2 q3 q4 un m49 ilo who imf icao itu oecd
world bank owid sql csv png english data movement output life energy internet electricity
inflation population unemployment renewables renewable airlines airline air
""".split())
# Phrases that contain a place word but are not places.
NOT_PLACE_PHRASES = ("world bank", "our world in data", "world development indicators")
PLACE_WORDS = re.compile(r"\b(in|for|of|from|between|and|vs|versus|than|like|across|to|about)\s*$", re.I)


def _norm(text: str) -> str:
    """Lowercase, straight quotes, no accents: 'Côte d’Ivoire' -> "cote d'ivoire"."""
    out = []
    for ch in text.replace("’", "'").replace("‘", "'").lower():   # one character in, one out,
        base = [c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c)]
        out.append(base[0] if base else ch)                   # so positions still line up
    return "".join(out)


@dataclass
class Place:
    kind: str            # 'country' | 'group' | 'world'
    said: str            # the words in the question
    iso3: str = ""       # countries
    name: str = ""       # countries: the data's own name; groups: a readable label
    column: str = ""     # groups: the grouping or bloc column
    value: object = None  # groups: the value(s); True for a bloc


@dataclass
class Resolution:
    places: list = field(default_factory=list)
    unknown: list = field(default_factory=list)     # [(words, [suggestions])]

    @property
    def countries(self):
        return [p for p in self.places if p.kind == "country"]

    @property
    def groups(self):
        return [p for p in self.places if p.kind == "group"]

    @property
    def world(self):
        return any(p.kind == "world" for p in self.places)


def _lexicon() -> dict:
    """normalised name -> ('country', iso3) or ('group', (col, value)) or ('world', None)."""
    facts = catalog.get_facts()
    lex = {}
    for iso3, name in facts["countries"].items():
        lex[_norm(name)] = ("country", iso3)
        if "(" in name:                                      # "Micronesia (country)" -> also without
            lex.setdefault(_norm(name.split("(")[0].strip()), ("country", iso3))
    for alias, iso3 in COUNTRY_ALIASES.items():
        if iso3 in facts["countries"]:
            lex.setdefault(_norm(alias), ("country", iso3))
    for alias, target in GROUP_ALIASES.items():
        lex[_norm(alias)] = ("group", target)                # groups win over a country alias
    for col, values in facts["groups"].items():              # every value as written in the data
        if col == "income_group":                            # 'high', 'low' are ordinary words
            continue
        for v in values:
            lex.setdefault(_norm(v), ("group", (col, v)))
    for w in WORLD:
        lex[w] = ("world", None)
    lex.pop("us", None)                                      # only "US" in capitals (CASE_SENSITIVE)
    return lex


def group_label(column: str, value) -> str:
    if value is True:
        return catalog.BLOC_COLUMNS.get(column, column)
    if isinstance(value, tuple):
        return " and ".join(f"{v} income" for v in value)
    return f"{value} income" if column == "income_group" else value


def resolve(question: str) -> Resolution:
    lex = _lexicon()
    facts = catalog.get_facts()
    text = _norm(question)
    taken = [False] * len(text)
    res = Resolution()
    for phrase in NOT_PLACE_PHRASES:                         # "World Bank" is not "the world"
        for m in re.finditer(re.escape(phrase), text):
            for i in range(m.start(), m.end()):
                taken[i] = True

    def add(kind, target, start, end, said):
        if any(taken[start:end]):
            return
        for i in range(start, end):
            taken[i] = True
        if kind == "country":
            res.places.append(Place("country", said, iso3=target, name=facts["countries"][target]))
        elif kind == "group":
            col, val = target
            res.places.append(Place("group", said, column=col, value=val, name=group_label(col, val)))
        else:
            res.places.append(Place("world", said, name="the world"))

    for key in sorted(lex, key=len, reverse=True):          # longest first
        for m in re.finditer(rf"(?<![\w-]){re.escape(key)}(?![\w-])", text):
            kind, target = lex[key]
            add(kind, target, m.start(), m.end(), question[m.start():m.end()])
    for word, target in CASE_SENSITIVE.items():
        for m in re.finditer(rf"\b{word}\b", question):
            if isinstance(target, tuple):
                add("group", target, m.start(), m.end(), word)
            elif target in facts["countries"]:
                add("country", target, m.start(), m.end(), word)
    # "Nigerian", "Kenyan", "Ghanaian", "Senegalese": a country's adjective means the country
    for m in re.finditer(r"\b[A-Z][a-z]{3,}\b", question):
        if any(taken[m.start():m.end()]):
            continue
        iso3 = _demonym(_norm(m.group(0)), lex)
        if iso3:
            add("country", iso3, m.start(), m.end(), m.group(0))
    # keep the order the places were written in
    res.places.sort(key=lambda p: text.find(_norm(p.said)))
    res.unknown = _unknown_names(question, taken, lex)
    return res


def _demonym(word: str, lex: dict):
    for suffix in ("s", "n", "i", "is", "an", "ans", "ese", "ish", "ian", "ians"):   # shortest first
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            stem = word[: -len(suffix)]
            for base in (stem, stem + "a", stem + "ia", stem + "o"):
                hit = lex.get(base)
                if hit and hit[0] == "country":
                    return hit[1]
    return None


def _unknown_names(question: str, taken: list, lex: dict) -> list:
    out = []
    names = sorted({k for k, (kind, _) in lex.items() if kind != "world"})
    # Hide every matched name, so "Compare Nigeria and Wakanda" leaves only "Wakanda".
    masked = "".join("|" if t else ch for ch, t in zip(question, taken, strict=False))
    for m in re.finditer(r"[A-Z][\w'’\-]*(?:\s+(?:and|of|the|de|du|da)?\s*[A-Z][\w'’\-]*)*", masked):
        words = [w for w in re.split(r"\s+", m.group(0)) if w]
        words = [re.sub(r"['’]s$", "", w) for w in words]
        if all(_norm(w) in NOT_PLACES for w in words):
            continue
        phrase = " ".join(w for w in words if _norm(w) not in NOT_PLACES).strip()
        if len(phrase) < 3 or not re.search(r"[A-Za-z]{3}", phrase):
            continue
        close = difflib.get_close_matches(_norm(phrase), names, n=3, cutoff=0.75)
        after_place_word = bool(PLACE_WORDS.search(question[:m.start()]))
        if close or after_place_word:
            out.append((phrase, [_pretty(c, lex) for c in close]))
    return out


def _pretty(key: str, lex: dict) -> str:
    kind, target = lex[key]
    if kind == "country":
        return catalog.get_facts()["countries"][target]
    return group_label(*target)


def hints_text(res: Resolution) -> str:
    """The NAME HINTS line given to the SQL model with the question."""
    parts = []
    for p in res.places:
        if p.kind == "country":
            parts.append(f"{p.said} -> country {p.name}, iso3 = '{p.iso3}'")
        elif p.kind == "world":
            parts.append(f"{p.said} -> all countries (no filter); the result is a total of "
                         "countries with data")
        elif p.value is True:
            parts.append(f"{p.said} -> {p.column} (true/false column): WHERE {p.column}")
        elif isinstance(p.value, tuple):
            vals = ", ".join(f"'{v}'" for v in p.value)
            parts.append(f"{p.said} -> {p.column} IN ({vals})")
        else:
            parts.append(f"{p.said} -> {p.column} = '{p.value}'")
    return "NAME HINTS: " + ("; ".join(parts) if parts else "none")


def unknown_reply(res: Resolution) -> str:
    words, suggestions = res.unknown[0]
    if suggestions:
        return (f"I don't recognise \"{words}\" as a country, region or bloc in my data. "
                f"Did you mean {_or_list(suggestions)}?")
    return (f"I don't recognise \"{words}\" as a country, region or bloc in my data. I cover "
            f"{len(catalog.get_facts()['countries'])} countries and territories, the continents, the UN "
            "subregions (such as Western Africa), the World Bank regions and income groups, ECOWAS, "
            "the African Union, the EU, the G20 and the Middle East.")


def _or_list(items: list) -> str:
    items = list(dict.fromkeys(items))
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " or " + items[-1]
