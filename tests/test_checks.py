"""Code checks on the model's SQL, and the instant fixes."""
from emole.pipeline import checks, names


def test_plain_average_across_countries_is_fixed(engine_db):
    sql = ("SELECT 'Western Africa' AS group_name, year, AVG(internet_users_pct) AS internet_users_pct "
           "FROM country_year WHERE subregion = 'Western Africa' AND year = 2023 GROUP BY year")
    assert "pop_avg(internet_users_pct)" in checks.group_maths_problem(sql)
    fixed, made = checks.apply_instant_fixes("internet use in West Africa in 2023", sql)
    assert made == ["group maths"] and "pop_avg(internet_users_pct)" in fixed
    assert "SUM(population)" in checks.fix_group_maths(sql.replace("AVG(internet_users_pct)",
                                                                   "AVG(population)"))


def test_each_rule_gets_its_own_function(engine_db):
    sql = ("SELECT year, SUM(internet_users_pct) AS a, AVG(gdp_growth_pct) AS b, SUM(air_passengers) AS c "
           "FROM country_year WHERE is_ecowas GROUP BY year")
    fixed = checks.fix_group_maths(sql)
    assert "pop_avg(internet_users_pct)" in fixed and "gdp_avg(gdp_growth_pct)" in fixed
    assert "SUM(air_passengers)" in fixed and checks.group_maths_problem(fixed) is None


def test_one_country_over_years_may_average(engine_db):
    sql = "SELECT country, AVG(internet_users_pct) AS v FROM country_year WHERE iso3 = 'NGA' GROUP BY country"
    assert checks.group_maths_problem(sql) is None


def test_per_person_is_fixed_for_one_country_and_for_a_group(engine_db):
    q = "air passengers per person in Nigeria in 2023"
    one = "SELECT country, year, air_passengers FROM country_year WHERE iso3 = 'NGA' AND year = 2023"
    assert checks.per_person_problem(q, one)
    assert "air_passengers / population AS air_passengers_per_person" in checks.fix_per_person(q, one)
    group = ("SELECT 'ECOWAS' AS group_name, year, SUM(air_passengers) AS air_passengers FROM country_year "
             "WHERE is_ecowas AND year = 2022 GROUP BY year")
    assert "pop_avg(air_passengers / population) AS air_passengers_per_person" in \
        checks.fix_per_person("air passengers per person in ECOWAS", group)


def test_latest_year_uses_the_broad_year_for_rankings(engine_db):
    # fixtures: air_passengers latest 2023 but broad-coverage 2022
    q = "Which countries carried the most air passengers?"
    sql = ("SELECT country, year, air_passengers FROM country_year WHERE year = 2023 "
           "AND air_passengers IS NOT NULL ORDER BY air_passengers DESC LIMIT 10")
    assert "year = 2022" in checks.latest_year_problem(q, sql)
    assert "year = 2022" in checks.fix_latest_year(q, sql)
    assert checks.latest_year_problem(q + " in 2023", sql) is None      # a year was asked for


def test_names_must_appear(engine_db):
    q = "internet use in Ghana and ECOWAS"
    res = names.resolve(q)
    assert checks.names_problem(res, "SELECT * FROM country_year WHERE iso3 = 'NGA'")
    assert checks.names_problem(res, "SELECT * FROM country_year WHERE iso3 = 'GHA' OR is_ecowas") is None


def test_rankings_rank_countries(engine_db):
    sql = "SELECT continent, SUM(population) FROM country_year GROUP BY continent"
    assert checks.ranking_problem("Which countries have the most people?", sql)
    assert checks.ranking_problem("Which continent has the most people?", sql) is None
