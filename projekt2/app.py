import io
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leistungen.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

st.set_page_config(page_title="Leistungsübersicht", layout="wide")


# ---------------------------------------------------------------------------
# Datenzugriff
# ---------------------------------------------------------------------------


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


@st.cache_data(show_spinner=False)
def load_class_overview():
    """Feingranulare Sicht: Fortschritt pro Klasse (statt nur pro Kategorie)."""
    query = text(
        """
        select
            c.name as category,
            cl.name as class,
            sc.student_id,
            sc.semester,
            sum(sc.points) as total_points,
            sum(sc.count) as total_count,
            cl.min_points as min_points_required,
            cl.min_count as min_count_required,
            (
                (cl.min_points is null or sum(sc.points) >= cl.min_points)
                and (cl.min_count is null or sum(sc.count) >= cl.min_count)
            ) as done,
            case
                when cl.min_points > 0 then
                    100.0 * cast(sum(sc.points) as real) / cl.min_points
                else null
            end as progress_pct
        from students_classes as sc
        join classes as cl on sc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        group by cl.id, sc.student_id
        order by
            c.id,
            cl.id,
            sc.student_id;
        """
    )
    return pd.read_sql(query, engine)


@st.cache_data(show_spinner=False)
def load_patient_cases():
    query = text(
        """
        select
            p.id as patient_id,
            p.name as patient,
            c.name as category,
            cl.name as class,
            pc.region,
            pc.min_points,
            pc.max_points
        from patient_cases as pc
        join patients as p on pc.patient_id = p.id
        join classes as cl on pc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        order by p.id, c.id, cl.id;
        """
    )
    return pd.read_sql(query, engine)


@st.cache_data(show_spinner=False)
def load_treatment_cases():
    query = text(
        """
        select
            tc.id as treatment_case_id,
            tc.student_id,
            c.name as category,
            cl.name as class,
            cc.name as case_category,
            p.name as patient,
            tc.semester,
            tc.difficulty,
            tc.expected_duration_min,
            tc.actual_duration_min,
            tc.setting,
            tc.treatment_date,
            tc.notes
        from treatment_cases as tc
        left join classes as cl on tc.class_id = cl.id
        left join categories as c on cl.category_id = c.id
        left join case_categories as cc on tc.case_category_id = cc.id
        left join patients as p on tc.patient_id = p.id
        order by tc.treatment_date, tc.id;
        """
    )
    return pd.read_sql(query, engine)


@st.cache_data(show_spinner=False)
def load_osce_results():
    query = text(
        """
        select
            r.student_id,
            e.name as exam,
            e.semester,
            e.exam_date,
            st.name as station,
            comp.name as competency,
            r.points_achieved,
            st.max_points,
            case when r.passed = 1 then 'Bestanden' else 'Nicht bestanden' end as status
        from student_osce_results as r
        join osce_stations as st on r.station_id = st.id
        join osce_exams as e on st.exam_id = e.id
        left join competencies as comp on st.competency_id = comp.id
        order by e.exam_date, r.student_id;
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


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Filter, Darstellung, Export
# ---------------------------------------------------------------------------


def filter_dataframe(
    df: pd.DataFrame,
    selected_student: str = "Alle",
    selected_category: str = "Alle",
    selected_semester: str = "Alle",
) -> pd.DataFrame:
    filtered_df = df.copy()

    if selected_student != "Alle" and "student_id" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["student_id"] == selected_student]

    if selected_category != "Alle" and "category" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    if selected_semester != "Alle" and "semester" in filtered_df.columns:
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
    if "Fortschritt (%)" in display_df.columns:
        display_df["Fortschritt (%)"] = display_df["Fortschritt (%)"].round(1)
    if "Erfüllt" in display_df.columns:
        display_df["Erfüllt"] = (
            display_df["Erfüllt"]
            .fillna(False)
            .astype(bool)
            .map({True: "Ja", False: "Nein"})
        )
    return display_df


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Export")
    return buffer.getvalue()


def render_export_buttons(df: pd.DataFrame, key_prefix: str, filename_base: str):
    """Zeigt CSV- und Excel-Download-Buttons für einen gefilterten DataFrame."""
    if df.empty:
        return
    col1, col2 = st.columns(2)
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    col1.download_button(
        "⬇️ Als CSV exportieren",
        data=csv_bytes,
        file_name=f"{filename_base}.csv",
        mime="text/csv",
        key=f"{key_prefix}_csv",
    )
    col2.download_button(
        "⬇️ Als Excel exportieren",
        data=to_excel_bytes(df),
        file_name=f"{filename_base}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key_prefix}_xlsx",
    )


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


def render_progress_by_category_chart(df: pd.DataFrame):
    """Balkendiagramm: durchschnittlicher Fortschritt (%) je Kategorie."""
    if df.empty:
        st.info("Keine Daten vorhanden.")
        return

    progress_df = (
        df.groupby("category", as_index=False)["progress_pct"]
        .mean()
        .sort_values("progress_pct", ascending=False)
    )
    progress_df["progress_pct"] = progress_df["progress_pct"].clip(upper=150)

    chart = (
        alt.Chart(progress_df)
        .mark_bar()
        .encode(
            x=alt.X("progress_pct:Q", title="Ø Fortschritt (%)"),
            y=alt.Y("category:N", title="Kategorie", sort="-x"),
            color=alt.Color(
                "progress_pct:Q",
                scale=alt.Scale(scheme="redyellowgreen", domain=[0, 100]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("category:N", title="Kategorie"),
                alt.Tooltip("progress_pct:Q", title="Ø Fortschritt (%)", format=".1f"),
            ],
        )
        .properties(width=700, height=300)
    )
    rule = (
        alt.Chart(pd.DataFrame({"x": [100]}))
        .mark_rule(color="black", strokeDash=[4, 4])
        .encode(x="x:Q")
    )

    st.altair_chart(chart + rule, use_container_width=True)


# ---------------------------------------------------------------------------
# Hauptseite
# ---------------------------------------------------------------------------


def main():
    overview = load_category_overview()
    totals = load_category_totals()
    class_overview = load_class_overview()
    patient_cases = load_patient_cases()
    treatment_cases = load_treatment_cases()
    osce_results = load_osce_results()

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
    filtered_class_overview = filter_dataframe(
        class_overview,
        selected_student=selected_student,
        selected_category=selected_category,
        selected_semester=selected_semester,
    )
    filtered_treatment_cases = filter_dataframe(
        treatment_cases,
        selected_student=selected_student,
        selected_category=selected_category,
        selected_semester=selected_semester,
    )
    # patient_cases hat keinen Studenten-/Semesterbezug im Schema, daher nur
    # die Kategorie-Filterung anwenden.
    filtered_patient_cases = filter_dataframe(
        patient_cases, selected_category=selected_category
    )
    filtered_osce_results = filter_dataframe(
        osce_results,
        selected_student=selected_student,
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
    class_display_df = prepare_display_dataframe(
        filtered_class_overview,
        selected_student=selected_student,
        selected_category=selected_category,
        selected_semester=selected_semester,
    )

    done_count = int(filtered_overview["done"].fillna(False).astype(bool).sum())
    open_count = int(len(filtered_overview) - done_count)
    avg_progress = filtered_overview["progress_pct"].mean()
    class_done_count = int(
        filtered_class_overview["done"].fillna(False).astype(bool).sum()
    )
    class_open_count = int(len(filtered_class_overview) - class_done_count)

    # ---------------------------- KPIs ----------------------------
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Studenten", filtered_overview["student_id"].nunique())
    col2.metric("Kategorien", filtered_overview["category"].nunique())
    col3.metric("Kategorien erfüllt", done_count)
    col4.metric("Kategorien offen", open_count)
    col5.metric(
        "Ø Fortschritt",
        f"{avg_progress:.1f} %" if pd.notna(avg_progress) else "–",
    )
    col6.metric(
        "Klassen erfüllt",
        f"{class_done_count} / {class_done_count + class_open_count}",
    )

    tab_labels = [
        "Übersicht",
        "Klassen",
        "Erfüllt",
        "Offen",
        "Entwicklung",
        "Patientenfälle",
        "Behandlungsfälle",
        "OSCE",
    ]
    (
        tab1,
        tab_classes,
        tab2,
        tab3,
        tab4,
        tab_patients,
        tab_treatments,
        tab_osce,
    ) = st.tabs(tab_labels)

    with tab1:
        st.subheader("Kategorie-Übersicht")
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        render_export_buttons(display_df, "overview", "kategorie_uebersicht")

        st.subheader("Ø Fortschritt je Kategorie")
        render_progress_by_category_chart(filtered_overview)

    with tab_classes:
        st.subheader("Fortschritt je Klasse")
        st.caption(
            "Feingranulare Ansicht unterhalb der Kategorien – berücksichtigt "
            "sowohl die Mindestpunktzahl als auch die Mindestanzahl je Klasse."
        )
        st.dataframe(class_display_df, hide_index=True, use_container_width=True)
        render_export_buttons(class_display_df, "classes", "klassen_uebersicht")

    with tab2:
        st.subheader("Erfüllte Kategorien")
        if done.empty:
            st.info("Keine erfüllten Kategorien vorhanden.")
        else:
            st.dataframe(done, hide_index=True, use_container_width=True)
            render_export_buttons(done, "done", "erfuellte_kategorien")

    with tab3:
        st.subheader("Nicht erfüllte Kategorien")
        if not_done.empty:
            st.info("Keine offenen Kategorien vorhanden.")
        else:
            st.dataframe(not_done, hide_index=True, use_container_width=True)
            render_export_buttons(not_done, "not_done", "offene_kategorien")

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
        else:
            st.info("Keine Daten für die Entwicklungsansicht vorhanden.")

    with tab_patients:
        st.subheader("Patientenfälle")
        st.caption(
            "Geplante Leistungen je Patient (unabhängig vom Studenten-Filter, "
            "da patient_cases keinen direkten Studentenbezug im Schema hat)."
        )
        if filtered_patient_cases.empty:
            st.info("Keine Patientenfälle vorhanden.")
        else:
            patient_names = sorted(filtered_patient_cases["patient"].unique())
            selected_patient = st.selectbox("Patient", ["Alle", *patient_names])
            pc_display = filtered_patient_cases
            if selected_patient != "Alle":
                pc_display = pc_display[pc_display["patient"] == selected_patient]

            pc_display = pc_display.rename(
                columns={
                    "patient": "Patient",
                    "category": "Kategorie",
                    "class": "Klasse",
                    "region": "Region/Zahn",
                    "min_points": "Min. Punkte",
                    "max_points": "Max. Punkte",
                }
            ).drop(columns=["patient_id"])
            st.dataframe(pc_display, hide_index=True, use_container_width=True)
            render_export_buttons(pc_display, "patient_cases", "patientenfaelle")

            summary = (
                filtered_patient_cases.groupby("patient", as_index=False)
                .agg(
                    Leistungen=("class", "count"),
                    Punkte_min=("min_points", "sum"),
                    Punkte_max=("max_points", "sum"),
                )
                .rename(columns={"patient": "Patient"})
            )
            st.subheader("Leistungen je Patient")
            st.dataframe(summary, hide_index=True, use_container_width=True)

    with tab_treatments:
        st.subheader("Behandlungsfälle")
        if filtered_treatment_cases.empty:
            st.info(
                "Noch keine Behandlungsfälle in der Datenbank erfasst "
                "(Tabelle treatment_cases ist leer)."
            )
        else:
            st.dataframe(
                filtered_treatment_cases, hide_index=True, use_container_width=True
            )
            render_export_buttons(
                filtered_treatment_cases, "treatment_cases", "behandlungsfaelle"
            )

    with tab_osce:
        st.subheader("OSCE-Ergebnisse")
        if filtered_osce_results.empty:
            st.info(
                "Noch keine OSCE-Ergebnisse in der Datenbank erfasst "
                "(Tabelle student_osce_results ist leer)."
            )
        else:
            st.dataframe(
                filtered_osce_results, hide_index=True, use_container_width=True
            )
            render_export_buttons(filtered_osce_results, "osce", "osce_ergebnisse")


if __name__ == "__main__":
    main()
