# fashion_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os

# -------------------- Page Setup --------------------
st.set_page_config(page_title="Fashion Sales Performance Dashboard", layout="wide")
st.title("Fashion Sales Performance Dashboard")
st.markdown("This dashboard provides insights into fashion sales performance, including KPIs, top products, top cities, cancel/return orders, and distribution across platforms.")

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
    start_date, end_date = date_range[0], date_range[1]
else:
    start_date = date_range
    end_date = date_range

filtered_data = filtered_data[(filtered_data['Date'] >= pd.to_datetime(start_date)) & (filtered_data['Date'] <= pd.to_datetime(end_date))]
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

    # -------------------- Charts --------------------
    rev_platform = filtered_data.groupby("Platform")['Revenue'].sum().reset_index()
    fig_rev_platform = px.bar(rev_platform, x='Platform', y='Revenue', text='Revenue', title='Revenue by Platform')
    fig_rev_platform.update_traces(texttemplate='₹%{text:,.2f}', textposition='outside')
    fig_rev_platform.update_layout(bargap=0.4)  # narrower bars

    profit_platform = filtered_data.groupby("Platform")['Profit'].sum().reset_index()
    fig_profit_platform = px.bar(profit_platform, x='Platform', y='Profit', text='Profit', title='Profit by Platform', color_discrete_sequence=['#FFD580'])
    fig_profit_platform.update_traces(texttemplate='₹%{text:,.2f}', textposition='outside')
    fig_profit_platform.update_layout(bargap=0.4)  # narrower bars

    top_products = filtered_data.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(top_n).reset_index()
    fig_top_products = px.bar(top_products, x='Revenue', y='Product', orientation='h', title=f'Top {top_n} Products by Revenue', text='Revenue', color_discrete_sequence=['#FFFACD'])
    fig_top_products.update_traces(texttemplate='₹%{text:,.2f}', textposition='inside')

    top_cities = filtered_data.groupby('City')['Revenue'].sum().sort_values(ascending=False).head(top_n).reset_index()
    fig_top_cities = px.bar(top_cities, x='Revenue', y='City', orientation='h', title=f'Top {top_n} Cities by Revenue', text='Revenue', color_discrete_sequence=['#90EE90'])
    fig_top_cities.update_traces(texttemplate='₹%{text:,.2f}', textposition='inside')

    rev_trend = filtered_data.groupby('Date')['Revenue'].sum().reset_index()
    fig_rev_trend = px.line(rev_trend, x='Date', y='Revenue', title='Revenue Trend Over Time')
    fig_rev_trend.update_traces(mode='lines+markers', hovertemplate='Date: %{x}<br>Revenue: ₹%{y:,.2f}')

    bubble_data = filtered_data.groupby(['Platform', 'SKU']).agg({'Revenue':'sum', 'Quantity':'sum'}).reset_index()
    fig_bubble = px.scatter(bubble_data, x='Quantity', y='Revenue', size='Revenue', color='Platform', hover_name='SKU', title='Revenue vs Quantity by Platform', size_max=60)
    fig_bubble.update_traces(hovertemplate='SKU: %{hovertext}<br>Revenue: ₹%{y:,.2f}<br>Quantity: %{x}')

    # -------------------- Layout Charts --------------------
    col1, col2 = st.columns([0.9, 0.9])
    col1.plotly_chart(fig_rev_platform, use_container_width=True)
    col2.plotly_chart(fig_profit_platform, use_container_width=True)

    col3, col4 = st.columns([0.9, 0.9])
    col3.plotly_chart(fig_top_products, use_container_width=True)
    col4.plotly_chart(fig_top_cities, use_container_width=True)

    col5, col6 = st.columns([0.9, 0.9])
    col5.plotly_chart(fig_rev_trend, use_container_width=True)
    col6.plotly_chart(fig_bubble, use_container_width=True)

    # -------------------- Additional Visuals --------------------
    pie_qty = filtered_data.groupby('Platform')['Quantity'].sum().reset_index()
    fig_pie_qty = px.pie(pie_qty, names='Platform', values='Quantity', title='Quantity Share by Platform')
    fig_pie_qty.update_traces(textinfo='percent+label')

    state_gmv = filtered_data.groupby('State')['Revenue'].sum().reset_index().rename(columns={'Revenue': 'Total GMV'})
    state_gmv = state_gmv.sort_values(by='Total GMV', ascending=False).reset_index(drop=True)

    col7, col8 = st.columns([0.8, 1.2])
    col7.plotly_chart(fig_pie_qty, use_container_width=True)
    with col8:
        st.markdown("### State — Total GMV")
        st.table(state_gmv.head(top_n))

    # -------------------- Download Buttons (2x2) --------------------
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    # Prepare datasets
    excel_full = convert_df_to_excel(data)
    if 'Payment_Method' in filtered_data.columns:
        df_payment = filtered_data.groupby(['Customer_ID','Payment_Method']).sum(numeric_only=True).reset_index()
        excel_payment = convert_df_to_excel(df_payment)
    df_loyal = filtered_data.groupby('Customer_ID').agg({'Order_ID':'nunique','Revenue':'sum'}).reset_index()
    df_loyal = df_loyal[df_loyal['Order_ID']>1]
    excel_loyal = convert_df_to_excel(df_loyal)
    df_one_timer = filtered_data.groupby('Customer_ID').agg({'Order_ID':'nunique','Revenue':'sum'}).reset_index()
    df_one_timer = df_one_timer[df_one_timer['Order_ID']==1]
    excel_one_timer = convert_df_to_excel(df_one_timer)

    # Display buttons in 2 rows x 2 cols
    b1, b2 = st.columns(2)
    b1.download_button("Download Full Dataset", data=excel_full, file_name="full_dataset.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    b2.download_button("Download Payment Method per Customer", data=excel_payment, file_name="payment_method_customers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    b3, b4 = st.columns(2)
    b3.download_button("Download Loyal Customers", data=excel_loyal, file_name="loyal_customers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    b4.download_button("Download One-Timer Customers", data=excel_one_timer, file_name="one_timer_customers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
