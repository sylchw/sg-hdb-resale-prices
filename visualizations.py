import streamlit as st
import altair as alt
import pandas as pd

def plot_price_over_time(median_price_per_month):
    """Plot median resale prices and YoY growth over time."""

    # Ensure 'month' is a datetime object
    median_price_per_month['month'] = pd.to_datetime(median_price_per_month['month'])

    # Calculate YoY Growth
    median_price_per_month['yoy_growth'] = median_price_per_month.apply(
        lambda row: (
            (row['median_resale_price'] - median_price_per_month[
                (median_price_per_month['month'] == row['month'] - pd.DateOffset(years=1))
            ]['median_resale_price'].iloc[0]) /
            median_price_per_month[
                (median_price_per_month['month'] == row['month'] - pd.DateOffset(years=1))
            ]['median_resale_price'].iloc[0]
        ) * 100 if row['month'] - pd.DateOffset(years=1) in median_price_per_month['month'].values else None,
        axis=1
    )

    # Filter out rows where YoY growth is NaN
    median_price_per_month = median_price_per_month.dropna(subset=['yoy_growth'])

    # Calculate yearly median prices for the table
    start_of_year_prices = (
        median_price_per_month.groupby(median_price_per_month["month"].dt.year)
        .first()
        .reset_index(names=["year"])
    )
    start_of_year_prices["median_resale_price"] = start_of_year_prices["median_resale_price"].astype(int)

    # Display the yearly median price table
    st.subheader("Start-of-Year Prices (Median)")
    st.table(start_of_year_prices[["year", "median_resale_price"]])

    # Base chart for shared X-axis
    base = alt.Chart(median_price_per_month).encode(
        x=alt.X('month:T', title='Month')
    )

    # Line chart for Median Resale Prices
    price_line = base.mark_line(interpolate='monotone', color='steelblue').encode(
        y=alt.Y('median_resale_price:Q', title='Median Resale Price (S$)', axis=alt.Axis(titleColor='steelblue')),
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip('median_resale_price:Q', title='Price (S$)', format=',.0f')
        ]
    )

    # Circle markers for Median Resale Prices (No additional axis)
    price_points = base.mark_circle(size=60, color='steelblue').encode(
        y=alt.Y('median_resale_price:Q', axis=None),  # Suppress axis for points
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip('median_resale_price:Q', title='Price (S$)', format=',.0f')
        ]
    )

    # Line chart for YoY Growth
    yoy_line = base.mark_line(interpolate='monotone', color='orange').encode(
        y=alt.Y('yoy_growth:Q', title='YoY Growth (%)', axis=alt.Axis(titleColor='orange')),
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip('yoy_growth:Q', title='YoY Growth (%)', format='.2f')
        ]
    )

    # Circle markers for YoY Growth (No additional axis)
    yoy_points = base.mark_circle(size=60, color='orange').encode(
        y=alt.Y('yoy_growth:Q', axis=None),  # Suppress axis for points
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip('yoy_growth:Q', title='YoY Growth (%)', format='.2f')
        ]
    )

    # Horizontal line at YoY Growth = 0% tied to the secondary Y-axis
    zero_growth_line = alt.Chart(median_price_per_month).mark_rule(
        color='gray', strokeDash=[4, 4], size=2
    ).encode(
        y=alt.Y('yoy_growth:Q', title=None)  # Explicitly tie to the secondary axis
    ).transform_filter(
        alt.datum.yoy_growth == 0  # Ensure line is drawn correctly
    )

    # Combine all layers and resolve dual Y-axes
    chart = alt.layer(
        price_line,
        price_points,
        yoy_line,
        yoy_points,
        zero_growth_line  # Add the horizontal line
    ).resolve_scale(
        y='independent'  # Enable dual Y-axes with independent scales
    ).properties(
        title="Median Resale Prices and YoY Growth Over Time",
        width='container',
        height=400
    ).interactive()

    # Display the chart
    st.altair_chart(chart, use_container_width=True)
