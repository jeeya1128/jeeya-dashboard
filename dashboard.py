import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page Config
st.set_page_config(page_title="Centralized Dashboard", layout="wide")

# -----------------------------
# Load Dataset
df = pd.read_excel("fashion_dataset.xlsx")

# -----------------------------
# Title
st.markdown("<h1 style='text-align:center;'>Centralized Dashboard</h1>", unsafe_allow_html=True)

# -----------------------------
# Platform Selector (Top)
platform_options = ["Amazon", "Flipkart", "Shopify"]
selected_platform_top = st.radio("Select Platform (Top)", options=platform_options + ["All"], horizontal=True)
# Sidebar platform selector
selected_platform_sidebar = st.sidebar.selectbox("Select Platform (Sidebar)", options=["All"] + platform_options)

# Determine final platform filter (if sidebar is used, it overrides top)
if selected_platform_sidebar == "All":
    platform_filter = platform_options
else:
    platform_filter = [selected_platform_sidebar]

# -----------------------------
# Sidebar Filters
st.sidebar.header("Other Filters")

def multiselect_with_all(label, options):
    options_with_all = ["All"] + list(options)
    selected = st.sidebar.multiselect(label, options_with_all, default=["All"])
    if "All" in selected or not selected:
        return list(options)
    else:
        return selected

# Date range at top
date_range = st.sidebar.date_input("Select Date Range", [df["Date"].min(), df["Date"].max()])

# Other filters
selected_state = multiselect_with_all("State", df["State"].unique())
selected_city = multiselect_with_all("City", df["City"].unique())
selected_product = multiselect_with_all("Product", df["Product"].unique())

# -----------------------------
# Filter Data
filtered_df = df[
    (df["Date"] >= pd.to_datetime(date_range[0])) &
    (df["Date"] <= pd.to_datetime(date_range[1])) &
    (df["Platform"].isin(platform_filter)) &
    (df["State"].isin(selected_state)) &
    (df["City"].isin(selected_city)) &
    (df["Product"].isin(selected_product))
]

# -----------------------------
# KPI Calculations
total_gmv = filtered_df["Revenue"].sum()
aov = filtered_df["Revenue"].sum() / max(len(filtered_df),1)
profit = filtered_df["Profit"].sum()
return_cancel_count = filtered_df[filtered_df["Delivery_Status"].isin(["Returned","Cancelled"])].shape[0]
quantity_sold = filtered_df["Quantity"].sum()
unique_products = filtered_df["Product"].nunique()

# -----------------------------
# KPI Cards
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("GMV", f"₹{total_gmv:,.0f}")
kpi2.metric("AOV", f"₹{aov:,.0f}")
kpi3.metric("Profit", f"₹{profit:,.0f}")

kpi4, kpi5, kpi6 = st.columns(3)
kpi4.metric("Return/Cancel Orders", return_cancel_count)
kpi5.metric("Quantity Sold", quantity_sold)
kpi6.metric("Unique Products", unique_products)

# -----------------------------
# Charts Layout

# Row 1: Revenue vs Profit + Top Products
colA, colB = st.columns(2)

with colA:
    rev_profit_df = filtered_df.groupby("Product")[["Revenue","Profit"]].sum().reset_index()
    fig1 = px.bar(rev_profit_df, x="Product", y=["Revenue","Profit"], barmode="group", title="Revenue vs Profit")
    st.plotly_chart(fig1, use_container_width=True)

with colB:
    top_products_df = filtered_df.groupby("Product")["Revenue"].sum().nlargest(5).reset_index()
    fig2 = px.bar(top_products_df, x="Product", y="Revenue", title="Top 5 Products by Revenue",
                  color_discrete_sequence=["lightyellow"])
    st.plotly_chart(fig2, use_container_width=True)

# Row 2: Top 5 Cities by Revenue
top_cities_df = filtered_df.groupby("City")["Revenue"].sum().nlargest(5).reset_index()
fig3 = px.bar(top_cities_df, x="City", y="Revenue", title="Top 5 Cities by Revenue",
              color_discrete_sequence=["lightgreen"])
st.plotly_chart(fig3, use_container_width=True)

# Row 3: Grouped Bar Chart (Revenue & Quantity by Platform)
platform_summary = filtered_df.groupby("Platform")[["Revenue","Quantity"]].sum().reset_index()
fig4 = px.bar(platform_summary, x="Platform", y=["Revenue","Quantity"], barmode="group",
              title="Revenue and Quantity by Platform")
st.plotly_chart(fig4, use_container_width=True)

# Row 4: Revenue Trend Over Time
revenue_trend_df = filtered_df.groupby("Date")["Revenue"].sum().reset_index()
fig5 = px.line(revenue_trend_df, x="Date", y="Revenue", title="Revenue Trend Over Time")
st.plotly_chart(fig5, use_container_width=True)

# Row 5: Product Contribution Pie
fig6 = px.pie(filtered_df, names="Product", values="Revenue", title="Revenue Contribution by Product")
st.plotly_chart(fig6, use_container_width=True)
