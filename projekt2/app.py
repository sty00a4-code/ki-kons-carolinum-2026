import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leistungen.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

st.set_page_config(page_title="Leistungsübersicht", layout="wide")


@st.cache_data(show_spinner=False)
def load_category_overview():
    query = text(
        """
        select
            c.name as category,
            sc.student_id,
            sum(sc.points) as total_points,
            c.min_points as min,
            (sum(sc.points) >= c.min_points) as done,
            case
                when c.min_points > 0 then
                    100.0 * cast(sum(sc.points) as real) / c.min_points
                else null
            end as progress_pct
        from students_classes as sc
        join classes as cl on sc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        group by c.id, sc.student_id
        order by
            c.id,
            sc.student_id,
            c.name;
        """
    )
    return pd.read_sql(query, engine)


@st.cache_data(show_spinner=False)
def load_category_totals():
    query = text(
        """
        select
            sc.student_id,
            sc.semester,
            c.name as category,
            sum(sc.points) as total_points
        from students_classes as sc
        join classes as cl on sc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        group by sc.student_id, sc.semester, c.id
        order by
            sc.student_id,
            sc.semester,
            c.name;
        """
    )
    return pd.read_sql(query, engine)


def load_category_done():
    overview = load_category_overview()
    mask = overview["done"].fillna(False).astype(bool)
    return overview.loc[mask].copy()


def load_category_not_done():
    overview = load_category_overview()
    mask = overview["done"].fillna(False).astype(bool)
    return overview.loc[~mask].copy()


def render_heatmap(df: pd.DataFrame):
    heatmap_df = df.pivot_table(
        index="semester",
        columns="category",
        values="total_points",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    if heatmap_df.empty:
        st.info("Keine Daten für die Heatmap vorhanden.")
        return

    heatmap_long = (
        heatmap_df.reset_index()
        .melt(id_vars="semester", var_name="category", value_name="points")
        .assign(semester=lambda x: x["semester"].astype(str))
    )

    chart = (
        alt.Chart(heatmap_long)
        .mark_rect()
        .encode(
            x=alt.X("category:N", title="Kategorie"),
            y=alt.Y("semester:O", title="Semester"),
            color=alt.Color(
                "points:Q",
                scale=alt.Scale(scheme="reds"),
                title="Punkte",
            ),
            tooltip=[
                alt.Tooltip("category:N", title="Kategorie"),
                alt.Tooltip("semester:O", title="Semester"),
                alt.Tooltip("points:Q", title="Punkte"),
            ],
        )
        .properties(width=700, height=300)
    )

    st.altair_chart(chart, width="stretch")


def main():
    overview = load_category_overview()
    totals = load_category_totals()

    if overview.empty:
        st.warning("Keine Daten gefunden. Bitte prüfe die Datenbankdatei.")
        st.stop()

    st.title("Leistungsübersicht")
    st.caption("Interaktive Darstellung der Leistungsdaten aus der SQLite-Datenbank.")

    students = sorted(overview["student_id"].astype(int).unique())
    categories = sorted(overview["category"].unique())

    with st.sidebar:
        st.header("Filter")
        selected_student = st.selectbox("Student", ["Alle", *students], index=0)
        selected_category = st.selectbox("Kategorie", ["Alle", *categories], index=0)

    filtered_overview = overview.copy()

    if selected_student != "Alle":
        filtered_overview = filtered_overview[
            filtered_overview["student_id"] == selected_student
        ]

    if selected_category != "Alle":
        filtered_overview = filtered_overview[
            filtered_overview["category"] == selected_category
        ]

    filtered_totals = totals.copy()

    if selected_student != "Alle":
        filtered_totals = filtered_totals[
            filtered_totals["student_id"] == selected_student
        ]

    if selected_category != "Alle":
        filtered_totals = filtered_totals[
            filtered_totals["category"] == selected_category
        ]

    done_mask = filtered_overview["done"].fillna(False).astype(bool)
    done = filtered_overview.loc[done_mask].copy()
    not_done = filtered_overview.loc[~done_mask].copy()

    display_df = filtered_overview.copy()

    if selected_student != "Alle":
        display_df = display_df.drop(columns=["student_id"])

    if selected_category != "Alle":
        display_df = display_df.drop(columns=["category"])

    rename_map = {
        "total_points": "Punkte",
        "min": "Mindestpunktzahl",
        "done": "Erfüllt",
        "progress_pct": "Fortschritt (%)",
    }
    if selected_student == "Alle":
        rename_map["student_id"] = "Student"
    if selected_category == "Alle":
        rename_map["category"] = "Kategorie"

    display_df = display_df.rename(columns=rename_map)
    display_df["Fortschritt (%)"] = display_df["Fortschritt (%)"].round(1)
    display_df["Erfüllt"] = (
        display_df["Erfüllt"]
        .fillna(False)
        .astype(bool)
        .map({True: "Ja", False: "Nein"})
    )

    done_count = int(filtered_overview["done"].fillna(False).astype(bool).sum())
    open_count = int(len(filtered_overview) - done_count)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Studenten", filtered_overview["student_id"].nunique())
    col2.metric("Kategorien", filtered_overview["category"].nunique())
    col3.metric("Erfüllt", done_count)
    col4.metric("Offen", open_count)

    tab1, tab2, tab3, tab4 = st.tabs(["Übersicht", "Erfüllt", "Offen", "Entwicklung"])

    with tab1:
        st.subheader("Kategorie-Übersicht")
        st.dataframe(display_df, width="stretch", hide_index=True)

    with tab2:
        st.subheader("Erfüllte Kategorien")
        if done.empty:
            st.info("Keine erfüllten Kategorien vorhanden.")
        else:
            st.dataframe(done, width="stretch", hide_index=True)

    with tab3:
        st.subheader("Nicht erfüllte Kategorien")
        if not_done.empty:
            st.info("Keine offenen Kategorien vorhanden.")
        else:
            st.dataframe(not_done, width="stretch", hide_index=True)

    with tab4:
        st.subheader("Punkte pro Student und Semester")

        chart_df = filtered_totals.copy()

        if not chart_df.empty:
            pivot_bar = chart_df.pivot_table(
                index=["student_id", "semester"],
                columns="category",
                values="total_points",
                aggfunc="sum",
                fill_value=0,
            ).sort_index()
            pivot_bar.index = [f"S{sid} · {sem}" for sid, sem in pivot_bar.index]
            st.bar_chart(pivot_bar)

            st.subheader("Entwicklung über die Semester")
            if selected_student != "Alle":
                student_progress = chart_df.copy()
                progress_pivot = student_progress.pivot_table(
                    index="semester",
                    columns="category",
                    values="total_points",
                    aggfunc="sum",
                    fill_value=0,
                ).sort_index()
                st.line_chart(progress_pivot)

            st.subheader("Heatmap")
            render_heatmap(chart_df)


if __name__ == "__main__":
    main()
