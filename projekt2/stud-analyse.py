import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///leistungen.db")


def load_category_totals(engine):
    """Load total points per student / semester / category."""
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
        order by sc.student_id, sc.semester, c.name
        """
    )
    return pd.read_sql(query, engine)


def plot_category_totals(df):
    """Plot total points per student/semester by category."""
    if df.empty:
        print("No data available to plot category totals.")
        return

    pivot = df.pivot_table(
        index=["student_id", "semester"],
        columns="category",
        values="total_points",
        fill_value=0,
    )
    pivot.index = [f"S{sid} · {sem}" for sid, sem in pivot.index]

    ax = pivot.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 7),
        colormap="tab20",
    )
    ax.set_title("Total Points per Student and Semester by Category")
    ax.set_ylabel("Points")
    ax.set_xlabel("Student · Semester")
    ax.legend(title="Category", bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


def plot_category_heatmap(df):
    """Show category totals aggregated by semester."""
    if df.empty:
        print("No data available to plot category heatmap.")
        return

    pivot = df.pivot_table(
        index="semester",
        columns="category",
        values="total_points",
        aggfunc="sum",
        fill_value=0,
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(pivot, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Total Points by Semester and Category")
    fig.colorbar(im, ax=ax, label="Points")
    plt.tight_layout()
    plt.show()


def plot_top_categories(df, top_n=10):
    """Plot the top categories by total points across all students."""
    if df.empty:
        print("No data available to plot top categories.")
        return

    totals = (
        df.groupby("category")
        .total_points.sum()
        .sort_values(ascending=False)
        .head(top_n)
    )
    ax = totals.plot(kind="barh", figsize=(10, 6), color="#5A9")
    ax.invert_yaxis()
    ax.set_title(f"Top {top_n} Categories by Total Points")
    ax.set_xlabel("Points")
    plt.tight_layout()
    plt.show()


def plot_student_progress(df, student_id):
    """Plot category progress across semesters for one student."""
    if df.empty:
        print("No data available to plot student progress.")
        return

    student = df[df.student_id == student_id]
    if student.empty:
        print(f"No data found for student {student_id}.")
        return

    pivot = student.pivot_table(
        index="semester",
        columns="category",
        values="total_points",
        fill_value=0,
    ).sort_index()

    ax = pivot.plot(kind="line", marker="o", figsize=(10, 5))
    ax.set_title(f"Category Points Across Semesters for Student {student_id}")
    ax.set_ylabel("Points")
    ax.set_xlabel("Semester")
    ax.legend(title="Category", bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    df = load_category_totals(engine)
    print("Loaded category totals:")
    print(df.head(20).to_string(index=False))

    plot_category_totals(df)
    plot_category_heatmap(df)
    plot_top_categories(df, top_n=8)

    # Choose a student to inspect. Replace 1 with any existing student ID.
    plot_student_progress(df, student_id=2)
