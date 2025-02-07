import pandas as pd
import os

def create_resale_data():
    # Define the folder where the CSV files are stored
    data_folder = "./data/govsgdata"

    # List all CSV files in the data folder
    csv_files = [
        os.path.join(data_folder, file)
        for file in os.listdir(data_folder)
        if file.endswith(".csv")
    ]

    # Initialize an empty list to store DataFrames
    data_frames = []

    # Read and preprocess each file
    for file in csv_files:
        # Load CSV file into a DataFrame
        df = pd.read_csv(file)
        
        # Ensure consistent column naming and data types across files
        # Rename columns if necessary to ensure consistency
        df.columns = df.columns.str.lower().str.replace(" ", "_")  # Standardize column names
        
        # Append the DataFrame to the list
        data_frames.append(df)

    # Concatenate all DataFrames into a single DataFrame
    combined_data = pd.concat(data_frames, ignore_index=True)

    # Save the combined DataFrame to a single CSV file
    output_file = "./data/combined_resale_data.csv"
    combined_data.to_csv(output_file, index=False)

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


def load_ehg_data(filepath, is_couple=True):
    """
    Load and preprocess EHG data for couples or singles.
    Args:
        filepath: Path to the EHG CSV file.
        is_couple: Boolean indicating if the data is for couples (True) or singles (False).
    Returns:
        Processed DataFrame with 'min_income', 'max_income', and 'EHG Amount (SGD)' columns.
    """
    ehg_data = pd.read_csv(filepath)

    # Choose the correct column based on couple or single
    income_column = "Average Monthly Household Income" if is_couple else "Half of Average Monthly Household Income"

    # Parse income ranges into min and max income
    def parse_income_bracket(bracket):
        if isinstance(bracket, str):
            if "Not more than" in bracket:
                return 0, int(bracket.replace("Not more than $", "").replace(",", ""))
            elif "to" in bracket:
                parts = bracket.replace("$", "").replace(",", "").split(" to ")
                return int(parts[0]), int(parts[1])
            elif "More than" in bracket:
                return int(bracket.replace("More than $", "").replace(",", "")), float("inf")
        raise ValueError(f"Unexpected format in income bracket: {bracket}")

    # Apply parsing
    ehg_data[["min_income", "max_income"]] = ehg_data[income_column].apply(parse_income_bracket).apply(pd.Series)

    return ehg_data


def setup_filters(sidebar, raw_data):
    """
    Set up the sidebar filters and return filtered data and filtered median prices.
    Args:
        sidebar: Streamlit sidebar object for filter controls.
        raw_data: Original raw data to apply filters on.
    Returns:
        filtered_data: DataFrame after applying filters.
        filtered_median_price: DataFrame of median resale prices per month.
    """
    # 1. Year Range
    max_year = int(raw_data["year"].max())
    min_year = int(raw_data["year"].min())
    years = sidebar.slider(
        "Select Year Range:",
        min_year,
        max_year,
        (max_year - 5, max_year)  # Default to last 5 years
    )

    # 2. Flat Type
    flat_types = sidebar.multiselect(
        "Select Flat Types:",
        options=raw_data["flat_type"].unique(),
        default=raw_data["flat_type"].unique()
    )

    # 3. Remaining Lease
    remaining_lease = sidebar.slider(
        "Select Remaining Lease (Years):",
        int(raw_data["remaining_lease"].min()),
        int(raw_data["remaining_lease"].max()),
        (int(raw_data["remaining_lease"].min()), int(raw_data["remaining_lease"].max()))
    )

    # 4. Towns
    towns = sidebar.multiselect(
        "Select HDB Towns:",
        options=raw_data["town"].unique(),
        default=raw_data["town"].unique()
    )

    # 5. Storey Range
    storey_ranges = sidebar.multiselect(
        "Select Storey Range:",
        options=raw_data["storey_range"].unique(),
        default=raw_data["storey_range"].unique()
    )

    # Apply filters to the raw data
    filtered_data = raw_data[
        (raw_data["year"] >= years[0]) &
        (raw_data["year"] <= years[1]) &
        (raw_data["flat_type"].isin(flat_types)) &
        (raw_data["remaining_lease"] >= remaining_lease[0]) &
        (raw_data["remaining_lease"] <= remaining_lease[1]) &
        (raw_data["town"].isin(towns)) &
        (raw_data["storey_range"].isin(storey_ranges))
    ]

    # Compute median resale prices over time for the filtered data
    filtered_median_price = (
        filtered_data.groupby(filtered_data["month"].dt.to_period("M"))
        .agg(median_resale_price=("resale_price", "median"))
        .reset_index()
    )
    # Convert the period back to a timestamp for plotting
    filtered_median_price["month"] = filtered_median_price["month"].dt.to_timestamp()

    return filtered_data, filtered_median_price
