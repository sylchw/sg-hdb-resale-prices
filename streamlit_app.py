import streamlit as st
from data_loader import load_resale_data
from visualizations import plot_price_over_time

# Set the title and favicon
st.set_page_config(
    page_title="Resale HDB Dashboard",
    page_icon="🏠",
)

# Title and Description
st.title("🏠 Resale HDB Dashboard")
st.write("""
This dashboard provides insights into resale HDB prices in Singapore. 
You can filter by time, room type, remaining lease duration, HDB town, and storey range to better understand trends.
""")

# Load the data
st.sidebar.header("Data Filters")
raw_data, median_price_per_month = load_resale_data()

# Sidebar Filters in Order of Importance
# 1. Year Range
max_year = int(raw_data["year"].max())
min_year = int(raw_data["year"].min())
years = st.sidebar.slider(
    "Select Year Range:",
    min_year,
    max_year,
    (max_year - 5, max_year)  # Default to last 5 years
)

# 2. Flat Type
flat_types = st.sidebar.multiselect(
    "Select Flat Types:",
    options=raw_data["flat_type"].unique(),
    default=raw_data["flat_type"].unique()
)

# 3. Remaining Lease
remaining_lease = st.sidebar.slider(
    "Select Remaining Lease (Years):",
    int(raw_data["remaining_lease"].min()),
    int(raw_data["remaining_lease"].max()),
    (int(raw_data["remaining_lease"].min()), int(raw_data["remaining_lease"].max()))
)

# 4. Towns
towns = st.sidebar.multiselect(
    "Select HDB Towns:",
    options=raw_data["town"].unique(),
    default=raw_data["town"].unique()
)

# 5. Storey Range
storey_ranges = st.sidebar.multiselect(
    "Select Storey Range:",
    options=raw_data["storey_range"].unique(),
    default=raw_data["storey_range"].unique()
)

# Filter the raw data
filtered_data = raw_data[
    (raw_data["year"] >= years[0]) &
    (raw_data["year"] <= years[1]) &
    (raw_data["flat_type"].isin(flat_types)) &
    (raw_data["remaining_lease"] >= remaining_lease[0]) &
    (raw_data["remaining_lease"] <= remaining_lease[1]) &
    (raw_data["town"].isin(towns)) &
    (raw_data["storey_range"].isin(storey_ranges))
]

# Apply the same filters to calculate the median resale prices for the filtered data
filtered_median_price = (
    filtered_data.groupby(filtered_data["month"].dt.to_period("M"))
    .agg(median_resale_price=("resale_price", "median"))
    .reset_index()
)

# Convert period back to timestamp for plotting
filtered_median_price["month"] = filtered_median_price["month"].dt.to_timestamp()

# Plot Median Price Trends
st.header("Median Resale Prices Over Time")
plot_price_over_time(filtered_median_price)

# Show Filtered Data
st.header("Filtered Data")
st.dataframe(filtered_data, use_container_width=True)
