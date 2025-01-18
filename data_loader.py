import pandas as pd

def load_resale_data():
    """Load and preprocess resale flat price data."""
    # Load the combined dataset
    data = pd.read_csv('./data/combined_resale_data.csv', low_memory=False)
    
    # Ensure 'month' column is in datetime format
    data['month'] = pd.to_datetime(data['month'], errors='coerce')
    data['year'] = data['month'].dt.year
    
    # Calculate the remaining lease years
    current_year = pd.Timestamp.now().year
    data['remaining_lease'] = (data['lease_commence_date'] + 99) - current_year

    # Group by month to calculate the median resale price
    median_price_per_month = data.groupby(data['month'].dt.to_period('M')).agg(
        median_resale_price=('resale_price', 'median')
    ).reset_index()
    
    # Convert period back to timestamp for easier handling
    median_price_per_month['month'] = median_price_per_month['month'].dt.to_timestamp()

    # Calculate YoY growth (%)
    median_price_per_month['yoy_growth'] = median_price_per_month['median_resale_price'].pct_change(periods=12) * 100

    return data, median_price_per_month

