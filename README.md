# Fashion Sales Performance Dashboard

Interactive Streamlit dashboard for analyzing fashion sales data, KPIs, top products, top cities, and customer behavior.

---

## Overview

This dashboard provides insights into fashion sales performance, including:

- Key KPIs: GMV, AOV, Profit, Quantity Sold, Unique Customers, Cancel/Return Orders  
- Top Products & Top Cities by Revenue  
- Revenue trend over time  
- Revenue vs Quantity by platform  
- Quantity distribution by platform (pie chart)  
- State-wise Total GMV  
- Download options for datasets: full dataset, payment method per customer, loyal customers, one-time customers  

---

## Features

- Fully interactive Streamlit dashboard  
- Filters for date, platform, state, city, and product  
- Top N selection for products and cities  
- Slim and clean bar charts for better visualization  
- Multiple download options for filtered datasets  
- KPIs and charts aligned for clear visual hierarchy  

---

## Installation / Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-folder>

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate the virtual environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run fashion_dashboard.py
