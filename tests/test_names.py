"""Place names are matched in code, before any model call."""
from emole.pipeline import names


def places(q):
    return [(p.kind, p.iso3 or p.column, p.value) for p in names.resolve(q).places]


def test_nicknames_and_regions(engine_db):
    got = places("How is Naija doing compared with West Africa and ECOWAS?")
    assert got == [("country", "NGA", None), ("group", "subregion", "Western Africa"),
                   ("group", "is_ecowas", True)]


def test_middle_east_and_world(engine_db):
    assert places("CO2 in the Middle East") == [("group", "is_middle_east", True)]
    assert places("What is the world population?") == [("world", "", None)]
    assert places("Which World Bank region is biggest?") == []        # "World Bank" is not the world


def test_longest_name_wins_and_case_rules(engine_db):
    assert places("Kosovo and Southern Europe") == [("country", "XKX", None),
                                                    ("group", "subregion", "Southern Europe")]
    assert places("Tell us about Ghana") == [("country", "GHA", None)]   # "us" is not the USA


def test_adjectives_mean_places(engine_db):
    assert places("Which African countries grew fastest?") == [("group", "continent", "Africa")]
    assert places("Ghanaian internet use") == [("country", "GHA", None)]
    lex = {"niger": ("country", "NER"), "nigeria": ("country", "NGA")}
    assert names._demonym("nigerian", lex) == "NGA"                    # not Niger


def test_unknown_name_gets_suggestions(engine_db):
    res = names.resolve("What was GDP growth in Nigerai in 2020?")
    assert res.unknown and "Nigeria" in res.unknown[0][1]
    assert "Did you mean Nigeria" in names.unknown_reply(res)
    res = names.resolve("Compare Ghana and Wakanda")
    assert [p.iso3 for p in res.countries] == ["GHA"] and res.unknown[0][0] == "Wakanda"


def test_question_words_are_not_places(engine_db):
    assert names.resolve("Which countries have the highest GDP per person?").unknown == []
    assert names.resolve("Show Emolé the latest inflation").unknown == []


def test_hints_text(engine_db):
    text = names.hints_text(names.resolve("Naija and ECOWAS"))
    assert "iso3 = 'NGA'" in text and "WHERE is_ecowas" in text
