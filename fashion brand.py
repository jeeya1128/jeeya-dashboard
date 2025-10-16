# fashion_brand.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os

# -------------------- Page Setup --------------------
st.set_page_config(page_title="Centralized Analytical dashboard for a fashion brand", layout="wide")
st.title("Centralized Analytical dashboard for a fashion brand")

# -------------------- Dataset Path --------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_dir, "fashion_dataset.xlsx")

# -------------------- Load Dataset --------------------
@st.cache_data
def load_data(file):
    if not os.path.exists(file):
        st.error(f"Dataset not found at {file}. Please check the file path.")
        return pd.DataFrame()
    df = pd.read_excel(file)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    return df

data = load_data(data_file)

# -------------------- Sidebar Filters --------------------
st.sidebar.markdown("### Filters")
min_date = data['Date'].min() if not data.empty else pd.Timestamp.today()
max_date = data['Date'].max() if not data.empty else pd.Timestamp.today()

date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

platforms = ["All"] + sorted(data['Platform'].unique().tolist()) if not data.empty else ["All"]
selected_platform = st.sidebar.multiselect("Platform", platforms, default="All")

states = ["All"] + sorted(data['State'].unique().tolist()) if not data.empty else ["All"]
selected_state = st.sidebar.multiselect("State", states, default="All")

cities = ["All"] + sorted(data['City'].unique().tolist()) if not data.empty else ["All"]
selected_city = st.sidebar.multiselect("City", cities, default="All")

products = ["All"] + sorted(data['Product'].unique().tolist()) if not data.empty else ["All"]
selected_product = st.sidebar.multiselect("Product", products, default="All")

top_n = st.sidebar.slider("Top N for Products & Cities", min_value=1, max_value=20, value=5, step=1)

# -------------------- Filter Data --------------------
filtered_data = data.copy()
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

filtered_data = filtered_data[(filtered_data['Date'] >= pd.to_datetime(start_date)) & 
                              (filtered_data['Date'] <= pd.to_datetime(end_date))]

if "All" not in selected_platform:
    filtered_data = filtered_data[filtered_data['Platform'].isin(selected_platform)]
if "All" not in selected_state:
    filtered_data = filtered_data[filtered_data['State'].isin(selected_state)]
if "All" not in selected_city:
    filtered_data = filtered_data[filtered_data['City'].isin(selected_city)]
if "All" not in selected_product:
    filtered_data = filtered_data[filtered_data['Product'].isin(selected_product)]

# -------------------- Empty Data Check --------------------
if filtered_data.empty:
    st.warning("No data available for the selected filters.")
else:
    # -------------------- KPIs --------------------
    total_revenue = filtered_data['Revenue'].sum()
    total_orders = filtered_data['Order_ID'].nunique()
    aov = total_revenue / total_orders if total_orders else 0
    total_profit = filtered_data['Profit'].sum()
    total_quantity = filtered_data['Quantity'].sum()
    unique_customers = filtered_data['Customer_ID'].nunique()
    cancel_return_orders = filtered_data['Delivery_Status'].isin(['Cancelled', 'Returned']).sum() if 'Delivery_Status' in filtered_data.columns else 0

    # KPIs Row 1
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("GMV", f"₹{total_revenue:,.2f}")
    kpi2.metric("AOV", f"₹{aov:,.2f}")
    kpi3.metric("Profit", f"₹{total_profit:,.2f}")

    # KPIs Row 2
    kpi4, kpi5, kpi6 = st.columns(3)
    kpi4.metric("Quantity Sold", int(total_quantity))
    kpi5.metric("Unique Customers", int(unique_customers))
    kpi6.metric("Cancel/Return Orders", int(cancel_return_orders))

    st.markdown("### 🔹 Key Business Highlights")
    st.markdown("""
    These KPIs summarize the overall business performance:
    - GMV → Total revenue earned from all sales.
    - AOV → Average amount spent per order.
    - Profit → Total profit earned after costs.
    - Quantity Sold →Total number of items sold.
    - Unique Customers → Number of distinct customers in the data.
    - Cancel/Return Orders → Number of orders that were cancelled or returned..
    """)

    # -------------------- Charts --------------------
    # Revenue & Profit by Platform
    col1, col2 = st.columns(2)

    with col1:
        rev_platform = filtered_data.groupby("Platform")['Revenue'].sum().reset_index()
        fig_rev_platform = px.bar(rev_platform, x='Platform', y='Revenue', text='Revenue', title='Revenue by Platform')
        fig_rev_platform.update_traces(texttemplate='₹%{text:,.2f}', textposition='outside')
        fig_rev_platform.update_layout(bargap=0.4)
        st.plotly_chart(fig_rev_platform, use_container_width=True)
        st.markdown("Revenue by Platform represents the total revenue contributed by each platform, highlighting where most sales are coming from.")

    with col2:
        profit_platform = filtered_data.groupby("Platform")['Profit'].sum().reset_index()
        fig_profit_platform = px.bar(profit_platform, x='Platform', y='Profit', text='Profit', title='Profit by Platform', color_discrete_sequence=['#FFD580'])
        fig_profit_platform.update_traces(texttemplate='₹%{text:,.2f}', textposition='outside')
        fig_profit_platform.update_layout(bargap=0.4)
        st.plotly_chart(fig_profit_platform, use_container_width=True)
        st.markdown("Profit by Platform shows which platforms are the most profitable, helping focus on high-margin channels.")

    # Top Products & Cities (Horizontal & side by side)
    col3, col4 = st.columns(2)

    top_products = filtered_data.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(top_n).reset_index()
    top_cities = filtered_data.groupby('City')['Revenue'].sum().sort_values(ascending=False).head(top_n).reset_index()

    with col3:
        fig_top_products = px.bar(top_products, x='Revenue', y='Product', orientation='h',
                                  title=f'Top {top_n} Products by Revenue', text='Revenue', color_discrete_sequence=['#FFFACD'])
        fig_top_products.update_traces(texttemplate='₹%{text:,.2f}', textposition='inside')
        st.plotly_chart(fig_top_products, use_container_width=True)
        st.markdown("This horizontal bar chart highlights the top products generating the most revenue.")

    with col4:
        fig_top_cities = px.bar(top_cities, x='Revenue', y='City', orientation='h',
                                title=f'Top {top_n} Cities by Revenue', text='Revenue', color_discrete_sequence=['#90EE90'])
        fig_top_cities.update_traces(texttemplate='₹%{text:,.2f}', textposition='inside')
        st.plotly_chart(fig_top_cities, use_container_width=True)
        st.markdown("This horizontal bar chart highlights the cities generating the most revenue.")

    # Revenue Trend Over Time
    rev_trend = filtered_data.groupby('Date')['Revenue'].sum().reset_index()
    fig_rev_trend = px.line(rev_trend, x='Date', y='Revenue', title='Revenue Trend Over Time')
    fig_rev_trend.update_traces(mode='lines+markers', hovertemplate='Date: %{x}<br>Revenue: ₹%{y:,.2f}')
    st.plotly_chart(fig_rev_trend, use_container_width=True)
    st.markdown("Revenue Trend Over Time shows how revenue grows or drops each day.")

    # Revenue vs Quantity by Platform (Bubble Chart)
    bubble_data = filtered_data.groupby(['Platform', 'SKU']).agg({'Revenue':'sum', 'Quantity':'sum'}).reset_index()
    fig_bubble = px.scatter(bubble_data, x='Quantity', y='Revenue', size='Revenue', color='Platform',
                            hover_name='SKU', title='Revenue vs Quantity by Platform', size_max=60)
    fig_bubble.update_traces(hovertemplate='SKU: %{hovertext}<br>Revenue: ₹%{y:,.2f}<br>Quantity: %{x}')
    st.plotly_chart(fig_bubble, use_container_width=True)
    st.markdown("This bubble chart compares revenue and quantity sold for each product on each platform, highlighting high-volume and high-value items.")

    # Quantity Share by Platform (Pie Chart)
    pie_qty = filtered_data.groupby('Platform')['Quantity'].sum().reset_index()
    fig_pie_qty = px.pie(pie_qty, names='Platform', values='Quantity', title='Quantity Share by Platform')
    fig_pie_qty.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_pie_qty, use_container_width=True)
    st.markdown("Pie chart showing how total quantity sold is distributed across different platforms, revealing the largest contributors to sales volume.")

    # State — Total GMV (Table)
    state_gmv = filtered_data.groupby('State')['Revenue'].sum().reset_index().rename(columns={'Revenue': 'Total GMV'})
    state_gmv = state_gmv.sort_values(by='Total GMV', ascending=False).reset_index(drop=True)
    st.table(state_gmv.head(top_n))
    st.markdown("Table displaying total revenue generated from each state, helping identify top-performing regions.")

    # -------------------- Download Buttons --------------------
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    # Most Profitable Products
    df_profitable = filtered_data.groupby(['Order_ID', 'Product']).agg({'Profit':'sum', 'Revenue':'sum'}).reset_index()
    excel_profitable = convert_df_to_excel(df_profitable)

    # Payment Method per Customer (with Product Name)
    if 'Payment_Method' in filtered_data.columns:
        df_payment = filtered_data.groupby(['Customer_ID', 'Product', 'Payment_Method']).sum(numeric_only=True).reset_index()
        excel_payment = convert_df_to_excel(df_payment)

    # Highest Revenue Customers
    df_highest_rev = filtered_data.groupby(['Customer_ID', 'Product']).agg({'Profit':'sum', 'Revenue':'sum'}).reset_index()
    excel_highest_rev = convert_df_to_excel(df_highest_rev)

    # One-Time Customers
    df_one_timer = filtered_data.groupby(['Customer_ID', 'Customer_Name', 'City']).agg({'Profit':'sum', 'Quantity':'sum', 'Order_ID':'nunique'}).reset_index()
    df_one_timer = df_one_timer[df_one_timer['Order_ID'] == 1]
    excel_one_timer = convert_df_to_excel(df_one_timer)

    st.markdown("### 📁 Download Reports")
    b1, b2 = st.columns(2)
    b1.download_button("Download Most Profitable Products", data=excel_profitable,
                       file_name="most_profitable_products.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    b2.download_button("Download Payment Method per Customer", data=excel_payment,
                       file_name="payment_method_customers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    b3, b4 = st.columns(2)
    b3.download_button("Download Highest Revenue Customers", data=excel_highest_rev,
                       file_name="highest_revenue_customers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    b4.download_button("Download One-Time Customers", data=excel_one_timer,
                       file_name="one_time_customers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
