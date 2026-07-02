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
            sc.semester,
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

    st.altair_chart(chart, use_container_width=True)


def filter_dataframe(
    df: pd.DataFrame,
    selected_student: str = "Alle",
    selected_category: str = "Alle",
    selected_semester: str = "Alle",
) -> pd.DataFrame:
    filtered_df = df.copy()

    if selected_student != "Alle":
        filtered_df = filtered_df[filtered_df["student_id"] == selected_student]

    if selected_category != "Alle":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    if selected_semester != "Alle":
        filtered_df = filtered_df[filtered_df["semester"] == selected_semester]

    return filtered_df


def prepare_display_dataframe(
    df: pd.DataFrame,
    selected_student: str = "Alle",
    selected_category: str = "Alle",
    selected_semester: str = "Alle",
) -> pd.DataFrame:
    display_df = df.copy()

    for column_name, selected_value in {
        "student_id": selected_student,
        "category": selected_category,
        "semester": selected_semester,
    }.items():
        if selected_value != "Alle" and column_name in display_df.columns:
            display_df = display_df.drop(columns=[column_name])

    rename_map = {
        "total_points": "Punkte",
        "min": "Mindestpunktzahl",
        "done": "Erfüllt",
        "progress_pct": "Fortschritt (%)",
    }
    column_labels = {
        "student_id": "Student" if selected_student == "Alle" else None,
        "category": "Kategorie" if selected_category == "Alle" else None,
        "semester": "Semester" if selected_semester == "Alle" else None,
    }
    rename_map.update(
        {
            column: label
            for column, label in column_labels.items()
            if label is not None and column in display_df.columns
        }
    )

    display_df = display_df.rename(columns=rename_map)
    display_df["Fortschritt (%)"] = display_df["Fortschritt (%)"].round(1)
    display_df["Erfüllt"] = (
        display_df["Erfüllt"]
        .fillna(False)
        .astype(bool)
        .map({True: "Ja", False: "Nein"})
    )
    return display_df


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
    semesters = sorted(overview["semester"].unique())

    with st.sidebar:
        st.header("Filter")
        selected_student = st.selectbox("Student", ["Alle", *students], index=0)
        selected_category = st.selectbox("Kategorie", ["Alle", *categories], index=0)
        selected_semester = st.selectbox("Semester", ["Alle", *semesters], index=0)

    filtered_overview = filter_dataframe(
        overview,
        selected_student=selected_student,
        selected_category=selected_category,
        selected_semester=selected_semester,
    )
    filtered_totals = filter_dataframe(
        totals,
        selected_student=selected_student,
        selected_category=selected_category,
        selected_semester=selected_semester,
    )

    done_mask = filtered_overview["done"].fillna(False).astype(bool)
    done = filtered_overview.loc[done_mask].copy()
    not_done = filtered_overview.loc[~done_mask].copy()

    display_df = prepare_display_dataframe(
        filtered_overview,
        selected_student=selected_student,
        selected_category=selected_category,
        selected_semester=selected_semester,
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
        st.dataframe(display_df, hide_index=True, use_container_width=True)

    with tab2:
        st.subheader("Erfüllte Kategorien")
        if done.empty:
            st.info("Keine erfüllten Kategorien vorhanden.")
        else:
            st.dataframe(done, hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("Nicht erfüllte Kategorien")
        if not_done.empty:
            st.info("Keine offenen Kategorien vorhanden.")
        else:
            st.dataframe(not_done, hide_index=True, use_container_width=True)

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

            if selected_student != "Alle":
                st.subheader("Entwicklung über die Semester")
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
