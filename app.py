# streamlit_fashion_dashboard_final_fixed.py

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# -------------------- Page Setup --------------------
st.set_page_config(page_title="Centralized Dashboard", layout="wide")
st.title("Centralized Dashboard")
st.markdown("Analyze fashion sales performance across platforms, products, and cities.")

# -------------------- Load Dataset --------------------
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df['Date'] = pd.to_datetime(df['Date'])
    # Ensure numeric columns
    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    return df

data = load_data("fashion_dataset.xlsx")

# -------------------- Sidebar Filters --------------------
st.sidebar.markdown("### Filters")

# Date range
min_date = data['Date'].min()
max_date = data['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# Platform filter
platforms = ["All"] + sorted(data['Platform'].unique().tolist())
selected_platform = st.sidebar.multiselect("Platform", platforms, default="All")

# State filter
states = ["All"] + sorted(data['State'].unique().tolist())
selected_state = st.sidebar.multiselect("State", states, default="All")

# City filter
cities = ["All"] + sorted(data['City'].unique().tolist())
selected_city = st.sidebar.multiselect("City", cities, default="All")

# Product filter
products = ["All"] + sorted(data['Product'].unique().tolist())
selected_product = st.sidebar.multiselect("Product", products, default="All")

# -------------------- Filter Data --------------------
filtered_data = data.copy()

filtered_data = filtered_data[(filtered_data['Date'] >= pd.to_datetime(date_range[0])) &
                              (filtered_data['Date'] <= pd.to_datetime(date_range[1]))]

if "All" not in selected_platform:
    filtered_data = filtered_data[filtered_data['Platform'].isin(selected_platform)]

if "All" not in selected_state:
    filtered_data = filtered_data[filtered_data['State'].isin(selected_state)]

if "All" not in selected_city:
    filtered_data = filtered_data[filtered_data['City'].isin(selected_city)]

if "All" not in selected_product:
    filtered_data = filtered_data[filtered_data['Product'].isin(selected_product)]

# -------------------- Check for empty data --------------------
if filtered_data.empty:
    st.warning("No data available for the selected filters.")
else:

    # -------------------- KPIs --------------------
    total_revenue = filtered_data['Revenue'].sum()
    total_orders = filtered_data['Order_ID'].nunique()
    aov = total_revenue / total_orders if total_orders else 0
    total_profit = filtered_data['Profit'].sum()
    
    # Fixed Return/Cancel Orders KPI
    return_cancel_orders = filtered_data[
        filtered_data['Delivery_Status'].isin(['Return', 'Cancel'])
    ]['Order_ID'].nunique()  # counts unique orders only
    
    total_quantity = filtered_data['Quantity'].sum()
    unique_customers = filtered_data['Customer_ID'].nunique()

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi4, kpi5, kpi6 = st.columns(3)

    kpi1.metric("GMV", f"${total_revenue:,.2f}")
    kpi2.metric("AOV", f"${aov:,.2f}")
    kpi3.metric("Profit", f"${total_profit:,.2f}")
    #kpi4.metric("Return/Cancel Orders", return_cancel_orders)
    kpi4.metric("Quantity Sold", total_quantity)
    kpi5.metric("Unique Customers", unique_customers)

    # -------------------- Charts --------------------
    # Revenue by Platform
    rev_platform = filtered_data.groupby("Platform")['Revenue'].sum().reset_index()
    fig_rev_platform = px.bar(rev_platform, x='Platform', y='Revenue', text='Revenue', title='Revenue by Platform')
    fig_rev_platform.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
    fig_rev_platform.update_layout(showlegend=False)

    # Profit by Platform
    profit_platform = filtered_data.groupby("Platform")['Profit'].sum().reset_index()
    fig_profit_platform = px.bar(profit_platform, x='Platform', y='Profit', text='Profit', title='Profit by Platform')
    fig_profit_platform.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
    fig_profit_platform.update_layout(showlegend=False)

    # Top 5 Products by Revenue (light yellow)
    top_products = filtered_data.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(5).reset_index()
    fig_top_products = px.bar(top_products, x='Revenue', y='Product', orientation='h',
                              title='Top 5 Products by Revenue', text='Revenue',
                              color_discrete_sequence=['#FFFACD'])
    fig_top_products.update_traces(texttemplate='$%{text:,.2f}', textposition='inside')

    # Top 5 Cities by Revenue (light green)
    top_cities = filtered_data.groupby('City')['Revenue'].sum().sort_values(ascending=False).head(5).reset_index()
    fig_top_cities = px.bar(top_cities, x='Revenue', y='City', orientation='h',
                            title='Top 5 Cities by Revenue', text='Revenue',
                            color_discrete_sequence=['#90EE90'])
    fig_top_cities.update_traces(texttemplate='$%{text:,.2f}', textposition='inside')

    # Revenue Trend Over Time
    rev_trend = filtered_data.groupby('Date')['Revenue'].sum().reset_index()
    fig_rev_trend = px.line(rev_trend, x='Date', y='Revenue', title='Revenue Trend Over Time')
    fig_rev_trend.update_traces(mode='lines+markers')

    # Revenue vs Quantity Bubble Chart
    bubble_data = filtered_data.groupby(['Platform', 'SKU']).agg({'Revenue':'sum', 'Quantity':'sum'}).reset_index()
    fig_bubble = px.scatter(bubble_data, x='Quantity', y='Revenue', size='Revenue', color='Platform',
                            hover_name='SKU', title='Revenue vs Quantity by Platform', size_max=60)

    # -------------------- Layout: 3 rows x 2 columns --------------------
    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_rev_platform, use_container_width=True)
    col2.plotly_chart(fig_profit_platform, use_container_width=True)

    col3, col4 = st.columns(2)
    col3.plotly_chart(fig_top_products, use_container_width=True)
    col4.plotly_chart(fig_top_cities, use_container_width=True)

    col5, col6 = st.columns(2)
    col5.plotly_chart(fig_rev_trend, use_container_width=True)
    col6.plotly_chart(fig_bubble, use_container_width=True)

    # -------------------- Filtered Data Table --------------------
    st.markdown("### Filtered Data Preview")
    st.dataframe(filtered_data.head(30))

    # -------------------- Download Button --------------------
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = convert_df_to_excel(filtered_data)

    st.download_button(
        label="Download Filtered Data",
        data=excel_data,
        file_name="filtered_fashion_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
