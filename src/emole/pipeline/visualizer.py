"""visualizer.py: decide text or chart, and draw the chart.

Emolé's data is yearly, so the only time axis is the year (the earlier build's month,
quarter and week logic was removed, not kept: it can never apply here).

  several countries (or groups) over time   -> a line chart, one line each
  one country, several measures over time   -> one small chart per measure, each with
                                               its own unit (the units differ, so they
                                               cannot share one axis)
  a ranking or a comparison in one year     -> a bar chart
  "as a bar / line / pie chart"             -> followed when the data suits it; a note
                                               explains when it does not

Every axis carries its unit ("Internet users (% of population)"), labels use short
numbers (950, 54.3k, 1.2M), and the full table is always in the CSV download.
"""
import math
import re
from datetime import datetime
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")                       # draw to files, no screen needed
import matplotlib.pyplot as plt  # noqa: E402
import plotly.express as px  # noqa: E402

from emole import config  # noqa: E402
from emole.pipeline import catalog  # noqa: E402
from emole.pipeline.columns import COLUMNS  # noqa: E402

CHART_WORDS = ("chart", "plot", "graph", "visuali", "diagram")
TREND_WORDS = ("trend", "over time", "since", "from 19", "from 20", "between", "each year", "by year",
               "history", "compare", "comparison", "across", "rank", "top ", "highest", "lowest")
COLORWAY = ["#1F5C45", "#C9962B", "#6E9C7F", "#3E7CB1", "#B5543C", "#8E6CBF", "#2E8B8B", "#7F8C8D",
            "#A3B86C", "#D9822B"]
MAX_BARS = 25
MAX_LABELLED = 18
MAX_PIE_SLICES = 12
SERIES_COLUMNS = ("country", "group_name")

_TYPE_WORDS = [("pie", re.compile(r"\b(pie|donut|doughnut)\b", re.I)),
               ("bar", re.compile(r"\b(bar|bars|column chart|histogram)\b", re.I)),
               ("line", re.compile(r"\b(line|lines|trend ?line)\b", re.I))]
_UNITS = [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "k"), (1, "")]


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------
def short_number(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    value = float(value)
    if value == 0:
        return "0"
    size, suffix = next(((s, x) for s, x in _UNITS if abs(value) >= s), (1, ""))
    scaled = value / size
    if suffix == "" and value.is_integer():
        return f"{int(value):,}"
    if suffix == "" and abs(value) < 1:
        return f"{value:.3g}"
    text = f"{scaled:,.{config.LABEL_DECIMALS}f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text + suffix


def measure_title(col) -> str:
    """'internet_users_pct' -> 'Internet users (% of population)'."""
    c = str(col)
    base = c[:-11] if c.endswith("_per_person") else c
    facts = catalog.get_facts()["columns"]
    name = COLUMNS.get(base, {}).get("label", base.replace("_", " "))
    if c.endswith("_per_person"):
        unit = facts[base]["unit"] + " per person" if base in facts else "per person"
    else:
        unit = facts[base]["unit"] if base in facts else ""
    title = name[0].upper() + name[1:]
    return f"{title} ({unit})" if unit else title


def requested_type(question: str):
    for kind, rx in _TYPE_WORDS:
        if rx.search(question):
            return kind
    return None


def chart_title(question: str) -> str:
    t = question.strip().rstrip("?.!")
    t = re.sub(r"^(please\s+)?(can|could|would) you\s+(please\s+)?", "", t, flags=re.I)
    t = re.sub(r"^(show|plot|draw|make|give|chart|display)( me)?\s+((a|an|the)\s+)?", "", t, flags=re.I)
    t = re.sub(r"\s+(as|in|into)\s+(a|an)\s+(\w+\s+)?(chart|graph|plot)$", "", t, flags=re.I)
    t = t or question.strip()
    t = t[0].upper() + t[1:]
    return t if len(t) <= 80 else t[:77].rsplit(" ", 1)[0] + "..."


# ---------------------------------------------------------------------------
# what is in the result?
# ---------------------------------------------------------------------------
def _measures(df) -> list:
    return [c for c in df.select_dtypes(include="number").columns
            if c != "year" and not str(c).endswith("_year") and c not in SERIES_COLUMNS]


def _series_col(df):
    for c in SERIES_COLUMNS:
        if c in df.columns and df[c].nunique() > 1:
            return c
    return None


def _label_col(df):
    for c in SERIES_COLUMNS:
        if c in df.columns:
            return c
    return None


def is_chartable(df) -> bool:
    return df is not None and len(df) >= 2 and bool(_measures(df))


def decide_output(question: str, df) -> str:
    if not is_chartable(df):
        return "text"
    q = question.lower()
    if requested_type(question) or any(w in q for w in CHART_WORDS):
        return "chart"
    years = df["year"].nunique() if "year" in df.columns else 0
    if years >= 3:
        return "chart"
    if any(w in q for w in TREND_WORDS) and len(df) >= 3:
        return "chart"
    return "text"


def choose_chart(df, question: str = "") -> dict:
    wanted = requested_type(question)
    measures = _measures(df)
    series = _series_col(df)
    over_time = "year" in df.columns and df["year"].nunique() > 1
    spec = {"note": "", "series": series, "measures": measures[:1], "facets": False}
    if over_time:
        spec.update(kind="line", x="year")
        if len(measures) > 1 and not series:
            spec.update(measures=measures, facets=True)          # one panel per measure
        elif len(measures) > 1:
            spec["note"] = (f" The chart shows {measure_title(measures[0]).lower()}; the other "
                            "measures are in the CSV download.")
        if wanted == "bar":
            spec["kind"] = "bar"
        elif wanted == "pie":
            spec["note"] += " A pie chart cannot show change over time, so this is a line chart."
    else:
        spec.update(kind="bar", x=_label_col(df) or df.columns[0])
        if spec["series"] == spec["x"]:               # one bar per country: no legend needed
            spec["series"] = None
        if len(measures) > 1:
            spec["note"] = (f" The chart shows {measure_title(measures[0]).lower()}; the other "
                            "measures are in the CSV download.")
        if wanted == "line":
            spec["note"] += (" A line chart suits values in time order; these are separate countries, "
                             "so they are bars.")
        elif wanted == "pie":
            vals = df[measures[0]].dropna()
            if len(df) > MAX_PIE_SLICES:
                spec["note"] += (f" A pie chart is hard to read with more than {MAX_PIE_SLICES} slices, "
                                 "so these are bars.")
            elif (vals < 0).any():
                spec["note"] += " A pie chart cannot show negative values, so these are bars."
            else:
                spec["kind"] = "pie"
    return spec


def _prepare(df, spec) -> pd.DataFrame:
    data = df.copy()
    if spec["x"] == "year":
        data = data.sort_values([c for c in (spec["series"], "year") if c])
        data["year"] = data["year"].astype(int).astype(str)          # category axis: 2019, 2020 ...
    elif spec["kind"] == "bar":
        data = data.head(MAX_BARS)
    return data.reset_index(drop=True)


def _labels(series: pd.Series, sparse: bool) -> list:
    labs = [short_number(v) for v in series]
    if not sparse or len(series) <= MAX_LABELLED:
        return labs
    s = series.reset_index(drop=True).dropna()
    keep = {s.idxmax(), s.idxmin(), s.index[-1]} if len(s) else set()
    return [lab if i in keep else "" for i, lab in enumerate(labs)]


# ---------------------------------------------------------------------------
# the interactive chart (Plotly, for the website) and the picture (PNG)
# ---------------------------------------------------------------------------
def build_figure(question: str, df):
    spec = choose_chart(df, question)
    data = _prepare(df, spec)
    title = chart_title(question)
    x, series = spec["x"], spec["series"]
    if spec["facets"]:
        long = data.melt(id_vars=[c for c in data.columns if c not in spec["measures"]],
                         value_vars=spec["measures"], var_name="measure", value_name="value")
        long["measure"] = long["measure"].map(measure_title)
        long["_label"] = _labels(long["value"], sparse=False)
        fig = px.line(long, x="year", y="value", facet_row="measure", markers=True, text="_label",
                      title=title, color_discrete_sequence=COLORWAY,
                      height=260 * len(spec["measures"]) + 80)
        fig.update_yaxes(matches=None, title_text="")
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_traces(textposition="top center")
    else:
        y = spec["measures"][0]
        data["_label"] = _labels(data[y], sparse=x == "year")
        labels = {x: "Year" if x == "year" else x.replace("_", " ").capitalize(), y: measure_title(y)}
        if spec["kind"] == "pie":
            fig = px.pie(data, names=x, values=y, title=title, color_discrete_sequence=COLORWAY)
        elif spec["kind"] == "line":
            fig = px.line(data, x=x, y=y, color=series, markers=True, text="_label", title=title,
                          labels=labels, color_discrete_sequence=COLORWAY)
            fig.update_traces(textposition="top center")
        else:
            fig = px.bar(data, x=x, y=y, color=series, barmode="group", text="_label", title=title,
                         labels=labels, color_discrete_sequence=COLORWAY)
            fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(font=dict(family="Segoe UI, Arial, sans-serif", size=13, color="#1B2A22"),
                      paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", margin=dict(l=60, r=30, t=60, b=60),
                      legend=dict(orientation="h", y=-0.2))
    if spec["kind"] != "pie":
        fig.update_xaxes(type="category", showgrid=False)
        fig.update_yaxes(gridcolor="#E4EDE7", tickformat="~s")
    return fig, spec, data


def _save_png(question: str, data: pd.DataFrame, spec: dict, path: Path) -> None:
    measures = spec["measures"] if spec["facets"] else spec["measures"][:1]
    fig, axes = plt.subplots(len(measures), 1, figsize=(10, 3.2 * len(measures) + 1.5), squeeze=False)
    for ax, y in zip(axes[:, 0], measures, strict=True):
        if spec["kind"] == "pie":
            ax.pie(data[y], labels=data[spec["x"]].astype(str), colors=COLORWAY[: len(data)],
                   autopct="%1.0f%%", startangle=90)
            continue
        groups = data.groupby(spec["series"]) if spec["series"] else [(None, data)]
        for i, (name, part) in enumerate(groups):
            colour = COLORWAY[i % len(COLORWAY)]
            labels = _labels(part[y], sparse=True)
            if spec["kind"] == "line":
                ax.plot(part[spec["x"]], part[y], marker="o", color=colour, label=name)
                for xv, yv, lab in zip(part[spec["x"]], part[y], labels, strict=True):
                    if lab:
                        ax.annotate(lab, (xv, yv), textcoords="offset points", xytext=(0, 7),
                                    ha="center", fontsize=8)
            else:
                bars = ax.bar(part[spec["x"]].astype(str), part[y], color=colour, label=name)
                ax.bar_label(bars, labels=labels, padding=2, fontsize=8)
        ax.set_ylabel(measure_title(y), fontsize=9)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: short_number(v)))
        ax.grid(axis="y", color="#E4EDE7")
        ax.set_axisbelow(True)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        if spec["series"]:
            ax.legend(fontsize=8)
    axes[0, 0].set_title(chart_title(question))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def build_chart(question: str, df, save_files: bool = True, out_dir=None) -> dict:
    """{'kind', 'x', 'measures', 'series', 'points', 'note', 'figure' (Plotly JSON)} and,
    when save_files is True, 'png' and 'html' file paths."""
    fig, spec, data = build_figure(question, df)
    result = {"kind": spec["kind"], "x": spec["x"], "measures": [str(m) for m in spec["measures"]],
              "series": spec["series"], "points": len(data), "note": spec["note"],
              "figure": fig.to_json()}
    if save_files:
        out_dir = Path(out_dir or config.CHART_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        fig.write_html(str(base.with_suffix(".html")), include_plotlyjs=True)
        _save_png(question, data, spec, base.with_suffix(".png"))
        result.update(html=str(base.with_suffix(".html")), png=str(base.with_suffix(".png")))
    return result
