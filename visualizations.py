import streamlit as st
import altair as alt
import pandas as pd

def plot_price_over_time(mean_price_per_month):
    """Plot mean resale prices over time with start-of-year prices."""
    
    # Highlight the mean price at the start of each year
    start_of_year_prices = (
        mean_price_per_month.groupby(mean_price_per_month["month"].dt.year)
        .first()
        .reset_index(names=["year"])  # Avoid conflict with "month"
    )
    start_of_year_prices["mean_resale_price"] = start_of_year_prices["mean_resale_price"].round()

    # Print start-of-year prices
    st.subheader("Start-of-Year Prices")
    st.table(start_of_year_prices[["year", "mean_resale_price"]])

    # Create the Altair chart
    line = alt.Chart(mean_price_per_month).mark_line(interpolate='monotone').encode(
        x=alt.X('month:T', title='Month'),
        y=alt.Y('mean_resale_price:Q', title='Mean Resale Price (S$)'),
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip('mean_resale_price:Q', title='Price (S$)', format=',.0f')
        ]
    )
    
    points = alt.Chart(mean_price_per_month).mark_circle(size=60).encode(
        x='month:T',
        y='mean_resale_price:Q',
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip('mean_resale_price:Q', title='Price (S$)', format=',.0f')
        ]
    )

    # Combine line and points for better interactivity
    chart = (line + points).properties(
        title="Mean Resale Prices Over Time",
        width='container',
        height=400
    ).interactive()

    # Display the chart
    st.altair_chart(chart, use_container_width=True)
