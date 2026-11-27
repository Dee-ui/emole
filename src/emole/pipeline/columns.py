"""columns.py: what Emolé knows about each of her 17 columns, in words.

The database's column_meta table holds the facts that come from the data (unit, group
rule, years, source). This file holds the WORDS around each column, which the data
cannot give us:

  label      a short name for charts and notes ("air passengers")
  words      phrases people use for it, so a question can be matched to a column
             without a model call (used by the year guard and the checks)
  sentence   the fixed sentence for a quick one-number answer (no model call)
  decimals   how many decimals to show

A test checks that every column in sources.yaml has an entry here and every entry has
a column, so the two lists can never drift apart.
"""
COLUMNS = {
    # --- M: Movement -------------------------------------------------------------
    "air_passengers": {
        "label": "air passengers",
        "words": ("air passenger", "passengers", "people flew", "flyers", "air travel"),
        "sentence": "Airlines registered in {place} carried {value} passengers in {year}.",
        "decimals": 0,
    },
    "air_departures": {
        "label": "airline departures",
        "words": ("departures", "take-offs", "takeoffs", "flights"),
        "sentence": "Airlines registered in {place} made {value} departures in {year}.",
        "decimals": 0,
    },
    "air_freight_mtkm": {
        "label": "air freight",
        "words": ("freight", "air cargo", "cargo", "tonne-km", "ton-km"),
        "sentence": "Airlines registered in {place} flew {value} million tonne-km of freight in {year}.",
        "decimals": 2,
    },
    "internet_users_pct": {
        "label": "internet users",
        "words": ("internet", "online", "web users"),
        "sentence": "{value}% of people in {place} used the internet in {year}.",
        "decimals": 1,
    },
    "mobile_subs_per_100": {
        "label": "mobile subscriptions",
        "words": ("mobile", "cell phone", "cellphone", "phone subscriptions", "sim"),
        "sentence": "{place} had {value} mobile subscriptions per 100 people in {year}.",
        "decimals": 1,
    },
    # --- O: Output ---------------------------------------------------------------
    "gdp_per_capita_ppp": {
        "label": "GDP per person",
        "words": ("gdp per person", "gdp per capita", "income per person", "gdp per head",
                  "per capita income", "living standards"),
        "sentence": ("{place}'s GDP per person was {value} international dollars "
                     "(PPP, 2021 prices) in {year}."),
        "decimals": 0,
    },
    "gdp_growth_pct": {
        "label": "GDP growth",
        "words": ("gdp growth", "economic growth", "growth rate", "economy grew", "economy grow",
                  "recession"),
        "sentence": "{place}'s GDP growth was {value}% in {year}.",
        "decimals": 1,
    },
    "inflation_cpi_pct": {
        "label": "inflation",
        "words": ("inflation", "consumer prices", "cost of living", "price rise"),
        "sentence": "Consumer price inflation in {place} was {value}% in {year}.",
        "decimals": 1,
    },
    "unemployment_pct": {
        "label": "unemployment",
        "words": ("unemployment", "jobless", "out of work"),
        "sentence": "Unemployment in {place} was {value}% of the labour force in {year}.",
        "decimals": 1,
    },
    # --- L: Life -----------------------------------------------------------------
    "life_expectancy_years": {
        "label": "life expectancy",
        "words": ("life expectancy", "lifespan", "how long people live"),
        "sentence": "Life expectancy at birth in {place} was {value} years in {year}.",
        "decimals": 1,
    },
    "under5_deaths_per_1000": {
        "label": "under-five deaths",
        "words": ("under-5", "under 5", "under-five", "under five", "child mortality",
                  "child deaths", "infant"),
        "sentence": ("Under-five mortality in {place} was {value} deaths per 1,000 live births "
                     "in {year}."),
        "decimals": 1,
    },
    "health_spend_per_capita_ppp": {
        "label": "health spending per person",
        "words": ("health spending", "health spend", "healthcare spending", "health expenditure",
                  "spend on health"),
        "sentence": ("Health spending in {place} was {value} international dollars per person "
                     "in {year}."),
        "decimals": 0,
    },
    "population": {
        "label": "population",
        "words": ("population", "how many people", "people live", "inhabitants"),
        "sentence": "{place} had a population of {value} in {year}.",
        "decimals": 0,
    },
    "urban_pop_pct": {
        "label": "urban population",
        "words": ("urban", "cities", "city dwellers", "urbanisation", "urbanization"),
        "sentence": "{value}% of people in {place} lived in urban areas in {year}.",
        "decimals": 1,
    },
    # --- E: Energy ---------------------------------------------------------------
    "electricity_access_pct": {
        "label": "electricity access",
        "words": ("electricity access", "access to electricity", "electrification", "electricity",
                  "power access"),
        "sentence": "{value}% of people in {place} had access to electricity in {year}.",
        "decimals": 1,
    },
    "renewables_share_elec_pct": {
        "label": "renewable electricity",
        "words": ("renewable", "renewables", "clean power", "solar", "wind", "hydro"),
        "sentence": "Renewables made up {value}% of {place}'s electricity generation in {year}.",
        "decimals": 1,
    },
    "co2_per_capita_t": {
        "label": "CO2 per person",
        "words": ("co2", "carbon", "emissions", "greenhouse"),
        "sentence": "{place}'s CO2 emissions were {value} tonnes per person in {year}.",
        "decimals": 2,
    },
}

# Columns that are totals: dividing them by population gives a per-person figure.
TOTALS = ("air_passengers", "air_departures", "air_freight_mtkm", "population")
AVIATION = ("air_passengers", "air_departures", "air_freight_mtkm")


def columns_in(text: str) -> list:
    """The columns a question seems to be about, in the order of COLUMNS.
    'electricity' alone means access; 'renewable electricity' means renewables."""
    t = " " + text.lower().replace("’", "'") + " "
    found = [c for c, info in COLUMNS.items() if any(w in t for w in info["words"])]
    if "renewables_share_elec_pct" in found and "electricity_access_pct" in found \
            and not any(w in t for w in ("access", "electrification")):
        found.remove("electricity_access_pct")
    if "gdp_growth_pct" in found and "gdp_per_capita_ppp" in found \
            and not any(w in t for w in ("per person", "per capita", "per head", "income per")):
        found.remove("gdp_per_capita_ppp")
    if "air_passengers" in found and "air_departures" in found and "passenger" in t \
            and "departure" not in t:
        found.remove("air_departures")
    return found
