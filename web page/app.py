import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Function to load extended sample data
def load_sample_data():
    # Sample dim_date DataFrame with a range of dates
    dim_date = pd.DataFrame({
        'DateID': range(1, 31),
        'Date': pd.date_range(start='2024-01-01', periods=30, freq='D')
    })

    # Sample dim_hotels DataFrame with multiple hotels and categories
    dim_hotels = pd.DataFrame({
        'HotelID': range(1, 6),
        'HotelName': ['Hotel A', 'Hotel B', 'Hotel C', 'Hotel D', 'Hotel E'],
        'HotelCategory': ['Luxury', 'Economy', 'Business', 'Luxury', 'Economy']
    })

    # Sample fact_booking DataFrame with multiple bookings for each date and hotel
    fact_booking = pd.DataFrame({
        'BookingID': range(1, 101),
        'HotelID': np.random.choice(dim_hotels['HotelID'], 100),
        'DateID': np.random.choice(dim_date['DateID'], 100),
        'Revenue': np.random.uniform(100, 500, 100),  # Random revenue between 100 and 500
        'Occupancy': np.random.uniform(50, 100, 100)  # Random occupancy percentage
    })

    # Sample fact_aggregated_booking DataFrame with daily totals per booking
    fact_aggregated_booking = pd.DataFrame({
        'BookingID': fact_booking['BookingID'],
        'TotalBookings': np.random.randint(1, 5, 100)  # Random number of bookings between 1 and 5
    })

    return dim_date, dim_hotels, fact_booking, fact_aggregated_booking

# Load the sample data
dim_date, dim_hotels, fact_booking, fact_aggregated_booking = load_sample_data()

# Merge datasets based on keys
merged_data = fact_booking.merge(dim_hotels, on='HotelID', how='left')\
    .merge(dim_date, on='DateID', how='left')\
    .merge(fact_aggregated_booking, on='BookingID', how='left')

# Dashboard Layout
st.title("Revenue Insights in Hospitality Domain")
st.markdown("### A visually interactive dashboard for hotel bookings, offering insights into key metrics and trends.")

# Sidebar for Filters
st.sidebar.header("Filters")
selected_hotel = st.sidebar.selectbox("Select Hotel", dim_hotels['HotelName'].unique())

# Convert Timestamp to datetime.date for slider compatibility
min_date = dim_date['Date'].min().date()
max_date = dim_date['Date'].max().date()

# Date range slider with datetime.date values
selected_date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

# Filter data based on selections
filtered_data = merged_data[ 
    (merged_data['HotelName'] == selected_hotel) & 
    (pd.to_datetime(merged_data['Date']).dt.date >= selected_date_range[0]) & 
    (pd.to_datetime(merged_data['Date']).dt.date <= selected_date_range[1])
]

# KPIs Section
st.subheader("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered_data['Revenue'].sum():,.2f}", delta=f"${filtered_data['Revenue'].sum() - 10000:,.2f}")
col2.metric("Total Bookings", filtered_data['BookingID'].nunique(), delta=10)
col3.metric("Avg Revenue per Booking", f"${filtered_data['Revenue'].mean():,.2f}")
col4.metric("Occupancy Rate", f"{filtered_data['Occupancy'].mean():.2f}%")

# Revenue by Hotel Category Pie Chart (update with combined revenue across all hotels)
st.subheader("Revenue by Hotel Category")
category_revenue_data = merged_data.groupby('HotelCategory')['Revenue'].sum().reset_index()

category_order = ['Luxury', 'Business', 'Economy']
category_revenue_data['HotelCategory'] = pd.Categorical(category_revenue_data['HotelCategory'], categories=category_order, ordered=True)
category_revenue_data = category_revenue_data.sort_values('HotelCategory')

# Create the pie chart for revenue by category (combined across all hotels)
fig_pie = px.pie(category_revenue_data, values='Revenue', names='HotelCategory', title='Revenue by Hotel Category (Combined)', color='HotelCategory')
fig_pie.update_traces(textinfo='percent+label', pull=[0.1, 0.1, 0.1])  # Make it visually appealing
st.plotly_chart(fig_pie, use_container_width=True)

# Line Chart for Booking Trends by Date with Interactive Click-to-Filter
st.subheader("Booking Trends Over Time")

# Group by date and calculate the total revenue and booking count per day
booking_trends_data = filtered_data.groupby('Date').agg(
    TotalRevenue=('Revenue', 'sum'),
    TotalBookings=('BookingID', 'count')
).reset_index()

# Ensure that all dates within the selected range are included in the data
date_range = pd.date_range(start=selected_date_range[0], end=selected_date_range[1])
booking_trends_data_full = pd.DataFrame({'Date': date_range})

# Merge back with the aggregated data to ensure all dates are included
booking_trends_data_full = booking_trends_data_full.merge(
    booking_trends_data,
    on='Date', how='left'
)

# Fill NaN values with zeros for missing dates (days without bookings)
booking_trends_data_full['TotalRevenue'] = booking_trends_data_full['TotalRevenue'].fillna(0)
booking_trends_data_full['TotalBookings'] = booking_trends_data_full['TotalBookings'].fillna(0)

# Create a figure with two line traces: Total Revenue and Total Bookings
fig_trend = go.Figure()

fig_trend.add_trace(go.Scatter(x=booking_trends_data_full['Date'], y=booking_trends_data_full['TotalRevenue'], mode='lines+markers', name='Revenue', line=dict(color='green', width=3)))
fig_trend.add_trace(go.Scatter(x=booking_trends_data_full['Date'], y=booking_trends_data_full['TotalBookings'], mode='lines+markers', name='Bookings', line=dict(color='blue', width=3)))

# Enhance chart styling
fig_trend.update_layout(
    title="Booking Trends Over Time",
    xaxis_title="Date",
    yaxis_title="Total Revenue / Total Bookings",
    legend_title="Metrics",
    template="plotly_dark",  # Use dark theme for contrast
    hovermode="x unified",  # Unified hover for both lines
    plot_bgcolor="#1e1e1e",  # Dark background
    paper_bgcolor="#111111",  # Dark paper background
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    font=dict(family="Arial, sans-serif", size=12, color="white")  # Stylish font
)

# Add grid lines and make the lines smoother and more defined
fig_trend.update_traces(marker=dict(size=8, line=dict(width=2, color='white')))

st.plotly_chart(fig_trend, use_container_width=True)

# Display Filtered Data Table
st.subheader("Filtered Data")
st.dataframe(filtered_data.style.set_properties(**{'background-color': '#1e1e1e', 'color': 'white'}))  # Stylish table
