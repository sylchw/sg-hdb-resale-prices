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
You can filter by time, room type, HDB town, storey range, and remaining lease duration to better understand trends.
""")

# Load the data
st.sidebar.header("Data Filters")
raw_data, mean_price_per_month = load_resale_data()

# Sidebar Filters
max_year = int(raw_data["year"].max())
min_year = max_year - 5  # Default range to the most recent 5 years

years = st.sidebar.slider(
    "Select Year Range:",
    int(raw_data["year"].min()),
    int(raw_data["year"].max()),
    (min_year, max_year)
)

towns = st.sidebar.multiselect(
    "Select HDB Towns:",
    options=raw_data["town"].unique(),
    default=raw_data["town"].unique()
)

flat_types = st.sidebar.multiselect(
    "Select Flat Types:",
    options=raw_data["flat_type"].unique(),
    default=raw_data["flat_type"].unique()
)

storey_ranges = st.sidebar.multiselect(
    "Select Storey Range:",
    options=raw_data["storey_range"].unique(),
    default=raw_data["storey_range"].unique()
)

remaining_lease = st.sidebar.slider(
    "Select Remaining Lease (Years):",
    int(raw_data["remaining_lease"].min()),
    int(raw_data["remaining_lease"].max()),
    (int(raw_data["remaining_lease"].min()), int(raw_data["remaining_lease"].max()))
)

# Filter the raw data
filtered_data = raw_data[
    (raw_data["year"] >= years[0]) &
    (raw_data["year"] <= years[1]) &
    (raw_data["town"].isin(towns)) &
    (raw_data["flat_type"].isin(flat_types)) &
    (raw_data["storey_range"].isin(storey_ranges)) &
    (raw_data["remaining_lease"] >= remaining_lease[0]) &
    (raw_data["remaining_lease"] <= remaining_lease[1])
]

# Apply the same filters to calculate mean resale prices for the filtered data
filtered_mean_price = (
    filtered_data.groupby(filtered_data["month"].dt.to_period("M"))
    .agg(mean_resale_price=("resale_price", "mean"))
    .reset_index()
)

# Convert period back to timestamp for plotting
filtered_mean_price["month"] = filtered_mean_price["month"].dt.to_timestamp()

# Plot Price Trends
st.header("Mean Resale Prices Over Time")
plot_price_over_time(filtered_mean_price)

# Show Filtered Data
st.header("Filtered Data")
st.dataframe(filtered_data, use_container_width=True)
