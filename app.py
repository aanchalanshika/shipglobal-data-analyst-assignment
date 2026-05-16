from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)


DATA_FILE = Path(__file__).with_name("Coffee Shop Sales.xlsx")

MONTH_ORDER = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

COLUMN_ALIASES = {
    "transaction_id": ["transaction_id", "order_id", "id", "sale_id"],
    "transaction_date": ["transaction_date", "date", "transactiondate"],
    "transaction_time": ["transaction_time", "time", "transactiontime"],
    "store_location": ["store_location", "store", "location", "branch"],
    "product_category": ["product_category", "category"],
    "product_type": ["product_type", "product", "item", "product_name"],
    "transaction_qty": ["transaction_qty", "quantity", "qty", "units_sold"],
    "unit_price": ["unit_price", "price", "unitprice", "sales_price"],
}


def normalize_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def find_column(columns: pd.Index, aliases: list[str]) -> str | None:
    normalized = {normalize_name(column): column for column in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


@st.cache_data(show_spinner=False)
def load_raw_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_excel(path)


def clean_sales_data(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], dict[str, int]]:
    df = raw_df.copy()
    df.columns = [normalize_name(column) for column in df.columns]

    resolved_columns: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        found = find_column(df.columns, aliases)
        if found is not None:
            resolved_columns[target] = found

    required = ["transaction_date", "transaction_time", "store_location", "product_category", "product_type", "transaction_qty", "unit_price"]
    missing = [column for column in required if column not in resolved_columns]
    if missing:
        raise ValueError(
            "The workbook is missing required columns: " + ", ".join(missing)
        )

    rename_map = {resolved_columns[key]: key for key in resolved_columns}
    df = df.rename(columns=rename_map)

    before_rows = len(df)
    before_duplicates = int(df.duplicated().sum())

    df = df.drop_duplicates().copy()

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["transaction_time"] = pd.to_datetime(df["transaction_time"].astype(str), errors="coerce")
    df["transaction_qty"] = pd.to_numeric(df["transaction_qty"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    df = df.dropna(subset=["transaction_date", "transaction_time", "transaction_qty", "unit_price"]).copy()
    df = df[(df["transaction_qty"] > 0) & (df["unit_price"] > 0)].copy()

    df["revenue"] = df["transaction_qty"] * df["unit_price"]
    df["day_name"] = df["transaction_date"].dt.day_name()
    df["month_name"] = df["transaction_date"].dt.month_name()
    df["year"] = df["transaction_date"].dt.year
    df["hour"] = df["transaction_time"].dt.hour
    df["week_type"] = np.where(df["day_name"].isin(["Saturday", "Sunday"]), "Weekend", "Weekday")

    revenue_q1 = df["revenue"].quantile(0.25)
    revenue_q3 = df["revenue"].quantile(0.75)
    revenue_iqr = revenue_q3 - revenue_q1
    lower_limit = revenue_q1 - (1.5 * revenue_iqr)
    upper_limit = revenue_q3 + (1.5 * revenue_iqr)
    df = df[df["revenue"].between(lower_limit, upper_limit)].copy()

    if "transaction_id" not in df.columns:
        df["transaction_id"] = np.arange(1, len(df) + 1)

    if resolved_columns.get("transaction_id") and resolved_columns["transaction_id"] in raw_df.columns:
        df["transaction_id"] = pd.to_numeric(df["transaction_id"], errors="ignore")

    metrics = {
        "rows_before": before_rows,
        "rows_after": len(df),
        "duplicates_removed": before_duplicates,
        "null_rows_removed": int(before_rows - len(raw_df.dropna())),
    }
    return df, resolved_columns, metrics


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


st.markdown(
    """
    <style>
    :root{
        --accent-1: #0ea5a4;
        --bg-1: #0f172a;
        --panel: #0b1220;
        --muted: #94a3b8;
        --card: #0b1220;
    }
    .block-container{padding-top:1.5rem;padding-bottom:2rem;font-family:Segoe UI, Roboto, Arial, sans-serif}
    .hero{padding:1.25rem 1.5rem;border-radius:1rem;background:linear-gradient(90deg,var(--panel),#1f2a44);color:#fff;margin-bottom:1rem}
    .hero h1{margin:0;font-size:2.2rem}
    .hero p{margin:0.35rem 0 0 0;opacity:0.9;color:var(--muted)}
    .kpi-grid{display:flex;gap:12px;flex-wrap:wrap}
    .kpi-card{flex:1;min-width:160px;background:linear-gradient(180deg,#0b1220 0%, #111827 100%);padding:14px;border-radius:12px;border:1px solid rgba(255,255,255,0.03);box-shadow:0 6px 18px rgba(2,6,23,0.6)}
    .kpi-title{color:#94a3b8;font-size:13px}
    .kpi-value{color:#fff;font-size:20px;font-weight:700;margin-top:6px}
    .kpi-sub{color:var(--accent-1);font-weight:600;margin-top:6px}
    .sidebar-box{padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,0.03);background:linear-gradient(180deg,#071029,#071426)}
    .chart-caption{color:var(--muted);font-size:12px;margin-bottom:6px}
    @media (max-width:720px){.kpi-grid{flex-direction:column}}
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="hero">
        <h1>Sales Analytics Dashboard</h1>
        <p>Data cleaning, KPI reporting, trend analysis, and final recommendations in Streamlit.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.spinner("Loading and cleaning sales data..."):
    try:
        raw_df = load_raw_data(DATA_FILE)
        df, resolved_columns, cleaning_metrics = clean_sales_data(raw_df)
    except Exception as exc:
        st.error(f"Unable to load the workbook: {exc}")
        st.stop()


st.sidebar.header("Dashboard Filters")
st.sidebar.caption("Use the controls below to focus the analysis.")

store_options = sorted(df["store_location"].dropna().astype(str).unique().tolist())
category_options = sorted(df["product_category"].dropna().astype(str).unique().tolist())
product_options = sorted(df["product_type"].dropna().astype(str).unique().tolist())

# visually group filters
st.sidebar.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
st.sidebar.markdown("**Date range**")

min_date = df["transaction_date"].min().date()
max_date = df["transaction_date"].max().date()

date_range = st.sidebar.date_input(
    "Transaction date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

store_filter = st.sidebar.multiselect("Store location", store_options, default=store_options)
category_filter = st.sidebar.multiselect("Product category", category_options, default=category_options)
product_filter = st.sidebar.multiselect("Product type", product_options, default=product_options)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered_df = df[
    df["store_location"].isin(store_filter)
    & df["product_category"].isin(category_filter)
    & df["product_type"].isin(product_filter)
    & df["transaction_date"].dt.date.between(start_date, end_date)
].copy()

if filtered_df.empty:
    st.warning("No records match the current filters. Expand the date range or relax the sidebar filters.")
    st.stop()


st.subheader("Data Quality Summary")
quality_col1, quality_col2, quality_col3, quality_col4 = st.columns(4)
quality_col1.metric("Rows loaded", f"{cleaning_metrics['rows_before']:,}")
quality_col2.metric("Rows after cleaning", f"{cleaning_metrics['rows_after']:,}")
quality_col3.metric("Duplicates removed", f"{cleaning_metrics['duplicates_removed']:,}")
quality_col4.metric("Filtered rows", f"{len(filtered_df):,}")

with st.expander("Show resolved column mapping and cleaned preview", expanded=False):
    st.write(resolved_columns)
    st.dataframe(df.head(10), use_container_width=True)


st.subheader("KPI Reporting")
total_revenue = float(filtered_df["revenue"].sum())
total_orders = int(filtered_df["transaction_id"].nunique())
total_quantity = float(filtered_df["transaction_qty"].sum())
average_order_value = total_revenue / total_orders if total_orders else 0.0
average_unit_price = float(filtered_df["unit_price"].mean()) if not filtered_df.empty else 0.0

def _render_kpis(kpis: list[tuple[str, str, str]]):
    html = '<div class="kpi-grid">'
    for title, value, sub in kpis:
        html += f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div>"
        if sub:
            html += f"<div class='kpi-sub'>{sub}</div>"
        html += "</div>"
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

_render_kpis([
    ("Total Revenue", format_currency(total_revenue), "Overall sales"),
    ("Total Orders", f"{total_orders:,}", "Unique transactions"),
    ("Quantity Sold", f"{total_quantity:,.0f}", "Units sold"),
    ("Avg Order Value", format_currency(average_order_value), "Revenue/order"),
    ("Avg Unit Price", format_currency(average_unit_price), "Per unit"),
])


st.divider()
st.subheader("Trend Analysis")

trend_col1, trend_col2 = st.columns(2)

daily_sales = filtered_df.groupby("transaction_date", as_index=False)["revenue"].sum().sort_values("transaction_date")
monthly_sales = filtered_df.groupby("month_name", as_index=False)["revenue"].sum()
monthly_sales["month_name"] = pd.Categorical(monthly_sales["month_name"], categories=MONTH_ORDER, ordered=True)
monthly_sales = monthly_sales.sort_values("month_name")

with trend_col1:
    st.caption("Daily revenue trend")
    fig_daily = px.line(daily_sales, x="transaction_date", y="revenue", markers=True)
    fig_daily.update_layout(margin=dict(l=0, r=0, t=20, b=0), yaxis_title="Revenue")
    st.plotly_chart(fig_daily, use_container_width=True)

with trend_col2:
    st.caption("Monthly revenue trend")
    fig_monthly = px.bar(monthly_sales, x="month_name", y="revenue", color="revenue")
    fig_monthly.update_layout(margin=dict(l=0, r=0, t=20, b=0), xaxis_title="Month", yaxis_title="Revenue")
    st.plotly_chart(fig_monthly, use_container_width=True)


analysis_col1, analysis_col2 = st.columns(2)

with analysis_col1:
    st.caption("Revenue by product category")
    category_sales = filtered_df.groupby("product_category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    fig_category = px.bar(category_sales, x="product_category", y="revenue", color="product_category")
    fig_category.update_layout(margin=dict(l=0, r=0, t=20, b=0), showlegend=False, xaxis_title="Category", yaxis_title="Revenue")
    st.plotly_chart(fig_category, use_container_width=True)

with analysis_col2:
    st.caption("Revenue by store location")
    store_sales = filtered_df.groupby("store_location", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    fig_store = px.pie(store_sales, names="store_location", values="revenue", hole=0.45)
    fig_store.update_layout(margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_store, use_container_width=True)


analysis_col3, analysis_col4 = st.columns(2)

with analysis_col3:
    st.caption("Top 10 products by revenue")
    top_products = filtered_df.groupby("product_type", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False).head(10)
    fig_top_products = px.bar(top_products, x="revenue", y="product_type", orientation="h", color="revenue")
    fig_top_products.update_layout(margin=dict(l=0, r=0, t=20, b=0), yaxis_title="Product", xaxis_title="Revenue")
    st.plotly_chart(fig_top_products, use_container_width=True)

with analysis_col4:
    st.caption("Weekend versus weekday")
    week_sales = filtered_df.groupby("week_type", as_index=False)["revenue"].sum().sort_values("week_type")
    fig_week = px.bar(week_sales, x="week_type", y="revenue", color="week_type")
    fig_week.update_layout(margin=dict(l=0, r=0, t=20, b=0), showlegend=False, xaxis_title="Day type", yaxis_title="Revenue")
    st.plotly_chart(fig_week, use_container_width=True)


st.subheader("Operational Analysis")
operational_col1, operational_col2 = st.columns(2)

hourly_sales = filtered_df.groupby("hour", as_index=False)["revenue"].sum().sort_values("hour")
heatmap_data = filtered_df.pivot_table(values="revenue", index="day_name", columns="hour", aggfunc="sum", fill_value=0)
heatmap_data = heatmap_data.reindex(DAY_ORDER)

with operational_col1:
    st.caption("Sales by hour")
    fig_hourly = px.area(hourly_sales, x="hour", y="revenue")
    fig_hourly.update_layout(margin=dict(l=0, r=0, t=20, b=0), xaxis_title="Hour", yaxis_title="Revenue")
    st.plotly_chart(fig_hourly, use_container_width=True)

with operational_col2:
    st.caption("Sales heatmap")
    fig_heatmap = px.imshow(heatmap_data, aspect="auto", color_continuous_scale="Blues", text_auto=True)
    fig_heatmap.update_layout(margin=dict(l=0, r=0, t=20, b=0), xaxis_title="Hour", yaxis_title="Day")
    st.plotly_chart(fig_heatmap, use_container_width=True)


st.subheader("Insights and Recommendations")

best_category = category_sales.iloc[0]["product_category"] if not category_sales.empty else "N/A"
best_store = store_sales.iloc[0]["store_location"] if not store_sales.empty else "N/A"
best_hour = int(hourly_sales.iloc[hourly_sales["revenue"].idxmax()]["hour"]) if not hourly_sales.empty else None
weekend_revenue = float(week_sales.loc[week_sales["week_type"] == "Weekend", "revenue"].sum()) if not week_sales.empty else 0.0
weekday_revenue = float(week_sales.loc[week_sales["week_type"] == "Weekday", "revenue"].sum()) if not week_sales.empty else 0.0

insight_lines = [
    f"Top category: {best_category}",
    f"Best-performing store: {best_store}",
    f"Peak sales hour: {best_hour}:00" if best_hour is not None else "Peak sales hour: not available",
    f"Weekend revenue is {'higher' if weekend_revenue > weekday_revenue else 'lower or equal'} than weekday revenue.",
]

recommendations = [
    "Keep more inventory for the top category and top products.",
    "Schedule more staff during the peak sales hour.",
    "Use targeted offers for weaker categories and slower stores.",
    "Plan weekend campaigns if weekend revenue is already outperforming weekdays.",
    "Track the dashboard weekly to monitor shifts in demand.",
]

insight_left, insight_right = st.columns(2)
with insight_left:
    st.markdown("**Key findings**")
    for line in insight_lines:
        st.write(f"- {line}")

with insight_right:
    st.markdown("**Final recommendation**")
    for recommendation in recommendations:
        st.write(f"- {recommendation}")


st.subheader("Cleaned Data")
st.dataframe(filtered_df, use_container_width=True, height=350)

csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download cleaned CSV",
    data=csv,
    file_name="cleaned_sales_data.csv",
    mime="text/csv",
)


st.divider()
st.markdown("Sales Analytics Dashboard built with Streamlit, Pandas, NumPy, and Plotly.")