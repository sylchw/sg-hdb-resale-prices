import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import altair as alt

from data_loader import load_resale_data
from visualizations import plot_price_over_time
from helpers import calculate_grants, calculate_affordability

#Session state details
# Initialize session state for affordability_input
if "affordability_input" not in st.session_state:
    st.session_state["affordability_input"] = None

if "loan_type_input" not in st.session_state:
    st.session_state["loan_type_input"] = "HDB Loan (2.6%)"  # Default to HDB Loan



# Set the title and favicon
st.set_page_config(
    page_title="Resale HDB Dashboard",
    page_icon="🏠",
    layout="wide"
)

# Title and Description
st.title("🏠 Resale HDB Dashboard")
st.write("""
This dashboard provides deeper insights into resale HDB prices in Singapore. 
You can filter by time, room type, remaining lease duration, HDB town, and storey range to better understand trends.

Data updated date: 18/1/2025

Resale transaction data used to power this dashboard is obtained from https://data.gov.sg/dataset/resale-flat-prices

Grant information is obtained from the HDB Website https://www.hdb.gov.sg/residential/buying-a-flat/understanding-your-eligibility-and-housing-loan-options/flat-and-grant-eligibility
""")

# Load the data
st.sidebar.header("Data Filters")
raw_data, median_price_per_month = load_resale_data()

# Sidebar Filters
from data_loader import setup_filters  # Modularized filters
filtered_data, filtered_median_price = setup_filters(st.sidebar, raw_data)

try:
    # Display Median Price Trends
    st.header("Median Resale Prices Over Time")
    plot_price_over_time(filtered_median_price)

    # Affordability Calculator
    st.header("Affordability Calculator")
    affordability_input = calculate_grants(st)

    if affordability_input:
        total_income = affordability_input["annual_income"] + affordability_input["spouse_income"]

        loan_type_input = affordability_input["loan_type_input"]
        loan_interest_rate = affordability_input["loan_interest_rate"]
        if total_income > 168000:
            st.warning("HDB Loan is not available for combined annual income above SGD 168,000.")
            loan_type_input = "Bank Loan"

        # Update affordability input with the selected interest rate
        affordability_input.update({
            "loan_interest_rate": loan_interest_rate,
            "loan_tenure": affordability_input.get("loan_tenure", 25)  # Default tenure if not provided
        })

        # Calculate affordability
        affordability_result = calculate_affordability(
            is_couple=affordability_input["is_couple"],
            citizen_status=affordability_input["citizen_status"],
            annual_income=affordability_input["annual_income"],
            spouse_income=affordability_input["spouse_income"],
            cpf_oa=affordability_input["cpf_oa"],
            spouse_cpf_oa=affordability_input["spouse_cpf_oa"],
            personal_cash=affordability_input["personal_cash"],
            spouse_cash=affordability_input["spouse_cash"],
            proximity_option=affordability_input["proximity_option"],
            loan_tenure=affordability_input["loan_tenure"],
            flat_size=affordability_input["flat_size"],
            loan_interest_rate=affordability_input["loan_interest_rate"],
            loan_type_input=loan_type_input.split(' ')[0]
        )


        # Display Results
        st.subheader("Affordability Results")
        # Create a DataFrame from the results
        results_df = pd.DataFrame(list(affordability_result.items()), columns=["Component", "Amount"])

        # Define a function to apply bold styling to the "Total Affordability" row
        def highlight_total(row):
            return ["font-weight: bold" if row.Component == "Total Affordability" else "" for _ in row]

        # Apply the styling
        styled_df = results_df.style.apply(highlight_total, axis=1)

        # Display the styled DataFrame using st.table
        st.table(styled_df)

        # Generate Affordability Plot
        st.subheader("Affordability Plot")
        income_range = np.arange(20000, 180001, 5000)  # From 20,000 to 180,000 in steps of 5,000
        affordability_values = []

        for income in income_range:
            updated_input = affordability_input.copy()
            updated_input["annual_income"] = income
            updated_input["spouse_income"] = affordability_input["spouse_income"]  # Keep spouse income constant

            # Calculate HDB Loan Affordability
            updated_input["loan_type_input"] = "HDB"
            updated_input["loan_interest_rate"] = 0.026  # Fixed HDB interest rate
            try:
                hdb_result = calculate_affordability(**updated_input)
                hdb_affordability = {
                    "Income": income,
                    "Affordability": float(hdb_result["Total Affordability"].replace("SGD ", "").replace(",", "")),
                    "Grants": float(hdb_result["Total Grants Available"].replace("SGD ", "").replace(",", "")),
                    "Loan Available": float(hdb_result["Maximum Loan Eligibility"].replace("SGD ", "").replace(",", "")),
                    "Monthly Repayment": float(hdb_result["Monthly Repayment"].replace("SGD ", "").replace(",", "")),
                    "Loan Type": "HDB Loan",
                }
                affordability_values.append(hdb_affordability)
            except ValueError:
                pass  # Skip HDB calculations for incomes above the threshold

            # Calculate Bank Loan Affordability
            updated_input["loan_type_input"] = "Bank"
            updated_input["loan_interest_rate"] = 0.03  # Example Bank interest rate
            bank_result = calculate_affordability(**updated_input)
            bank_affordability = {
                "Income": income,
                "Affordability": float(bank_result["Total Affordability"].replace("SGD ", "").replace(",", "")),
                "Grants": float(bank_result["Total Grants Available"].replace("SGD ", "").replace(",", "")),
                "Loan Available": float(bank_result["Maximum Loan Eligibility"].replace("SGD ", "").replace(",", "")),
                "Monthly Repayment": float(bank_result["Monthly Repayment"].replace("SGD ", "").replace(",", "")),
                "Loan Type": "Bank Loan",
            }
            affordability_values.append(bank_affordability)

        # Convert to DataFrame for Altair
        affordability_df = pd.DataFrame(affordability_values)

        # Create Altair chart
        line = alt.Chart(affordability_df).mark_line().encode(
            x=alt.X('Income:Q', title='Annual Income (SGD)'),
            y=alt.Y('Affordability:Q', title='Total Affordability (SGD)'),
            color=alt.Color('Loan Type:N', scale=alt.Scale(domain=["HDB Loan", "Bank Loan"], range=["red", "blue"])),
            tooltip=[
                alt.Tooltip('Income:Q', title='Annual Income (SGD)', format=',.0f'),
                alt.Tooltip('Affordability:Q', title='Affordability (SGD)', format=',.0f'),
                alt.Tooltip('Grants:Q', title='Grants Available (SGD)', format=',.0f'),
                alt.Tooltip('Loan Available:Q', title='Loan Available (SGD)', format=',.0f'),
                alt.Tooltip('Monthly Repayment:Q', title='Monthly Repayment (SGD)', format=',.0f'),
                alt.Tooltip('Loan Type:N', title='Loan Type')
            ]
        )

        points = alt.Chart(affordability_df).mark_circle(size=60).encode(
            x=alt.X('Income:Q', title='Annual Income (SGD)'),
            y=alt.Y('Affordability:Q', title='Total Affordability (SGD)'),
            color=alt.Color('Loan Type:N', scale=alt.Scale(domain=["HDB Loan", "Bank Loan"], range=["red", "blue"])),
            tooltip=[
                alt.Tooltip('Income:Q', title='Annual Income (SGD)', format=',.0f'),
                alt.Tooltip('Affordability:Q', title='Affordability (SGD)', format=',.0f'),
                alt.Tooltip('Grants:Q', title='Grants Available (SGD)', format=',.0f'),
                alt.Tooltip('Loan Available:Q', title='Loan Available (SGD)', format=',.0f'),
                alt.Tooltip('Monthly Repayment:Q', title='Monthly Repayment (SGD)', format=',.0f'),
                alt.Tooltip('Loan Type:N', title='Loan Type')
            ]
        )

        # Combine line and points
        chart = (line + points).properties(
            title="Affordability vs Income for HDB and Bank Loans",
            width='container',
            height=400
        ).interactive()

        # Display the chart
        st.altair_chart(chart, use_container_width=True)


        # Best possible house in each town within the last 3 months
        st.subheader("Best Possible House You Can Buy in Each Town (Last 3 Months)")

        if affordability_result:
            # Extract total affordability
            total_affordability = float(affordability_result["Total Affordability"].replace("SGD ", "").replace(",", ""))

            # Calculate the date threshold (3 months before the current date)
            current_date = datetime.now()
            date_threshold = current_date - timedelta(days=90)

            # Filter houses within affordability range and sale date within the last 3 months
            filtered_data["month"] = pd.to_datetime(filtered_data["month"])  # Ensure 'month' is datetime
            affordable_houses = filtered_data[
                (filtered_data["resale_price"] <= total_affordability) &
                (filtered_data["month"] >= date_threshold)
            ].copy()

            # Sort by town, date, and resale price
            affordable_houses = affordable_houses.sort_values(by=["town", "month", "resale_price"], ascending=[True, False, False])

            # Select the most expensive affordable house in each town
            best_houses = affordable_houses.groupby("town").first().reset_index()

            # Select relevant columns to display
            columns_to_display = ["town", "month", "block", "street_name", "flat_type", "storey_range", "floor_area_sqm", "resale_price", "remaining_lease"]
            best_houses_display = best_houses[columns_to_display]

            # Expand the DataFrame display
            st.dataframe(best_houses_display, use_container_width=True)
        else:
            st.warning("Please calculate affordability to see the best houses you can buy in each town (last 3 months).")

        # Minimum required income for each town based on filtered data
        st.subheader("Minimum Combined Annual Income Required for Each Town (Last 3 Months), based on your filters")

        if affordability_input and not filtered_data.empty:
            try:
                # Extract relevant inputs for affordability calculation
                loan_type_input = affordability_input["loan_type_input"].split(' ')[0]
                loan_tenure = affordability_input["loan_tenure"]
                loan_interest_rate = affordability_input["loan_interest_rate"]

                # Calculate the date threshold (3 months before the current date)
                current_date = datetime.now()
                date_threshold = current_date - timedelta(days=90)

                # Filter houses within the last 3 months
                filtered_data["month"] = pd.to_datetime(filtered_data["month"])  # Ensure 'month' is datetime
                recent_houses = filtered_data[filtered_data["month"] >= date_threshold].copy()

                # Get the minimum resale price per town
                recent_houses = recent_houses.sort_values(by=["town", "resale_price"])
                grouped = recent_houses.groupby("town", as_index=False).first()

                # Initialize a list to store results
                required_income_data = []

                # Iterate over towns and calculate required income
                for _, row in grouped.iterrows():
                    town = row["town"]
                    min_price = row["resale_price"]

                    # Iteratively find the minimum income that satisfies the affordability condition
                    required_income = 0
                    step = 500  # Increment step for income in SGD
                    max_iterations = 5000  # Safeguard against infinite loops
                    iteration_count = 0
                    found = False

                    while iteration_count < max_iterations:
                        iteration_count += 1
                        try:
                            affordability_result = calculate_affordability(
                                is_couple=affordability_input["is_couple"],
                                citizen_status=affordability_input["citizen_status"],
                                annual_income=required_income,
                                spouse_income=0,  # Assuming single-income affordability
                                cpf_oa=0,
                                spouse_cpf_oa=0,
                                personal_cash=0,
                                spouse_cash=0,
                                proximity_option=affordability_input["proximity_option"],
                                loan_tenure=loan_tenure,
                                flat_size="",
                                loan_interest_rate=loan_interest_rate,
                                loan_type_input=loan_type_input
                            )
                        except ValueError:
                            # Handle HDB loan restriction or other calculation errors
                            required_income_data.append({
                                "Town": town,
                                "Month": row["month"].strftime("%Y-%m"),
                                "Block": row["block"],
                                "Street Name": row["street_name"],
                                "Flat Type": row["flat_type"],
                                "Storey Range": row["storey_range"],
                                "Resale Price (SGD)": min_price,
                                "Remaining Lease": row["remaining_lease"],
                                "Required Annual Income (SGD)": "HDB Loan Restricted"
                            })
                            found = True
                            break

                        # Check if the total affordability meets the minimum price
                        total_affordability = float(affordability_result["Total Affordability"].replace("SGD ", "").replace(",", ""))
                        if total_affordability >= min_price:
                            found = True
                            break

                        required_income += step

                    if found and required_income != 0:
                        required_income_data.append({
                            "Town": town,
                            "Month": row["month"].strftime("%Y-%m"),
                            "Block": row["block"],
                            "Street Name": row["street_name"],
                            "Flat Type": row["flat_type"],
                            "Storey Range": row["storey_range"],
                            "Resale Price (SGD)": min_price,
                            "Remaining Lease": row["remaining_lease"],
                            "Required Annual Income (SGD)": required_income
                        })
                    elif not found:
                        required_income_data.append({
                            "Town": town,
                            "Month": row["month"].strftime("%Y-%m"),
                            "Block": row["block"],
                            "Street Name": row["street_name"],
                            "Flat Type": row["flat_type"],
                            "Storey Range": row["storey_range"],
                            "Resale Price (SGD)": min_price,
                            "Remaining Lease": row["remaining_lease"],
                            "Required Annual Income (SGD)": "No House Available"
                        })

                # Convert results to DataFrame and display
                required_income_df = pd.DataFrame(required_income_data)
                st.dataframe(required_income_df, use_container_width=True)

            except Exception as e:
                st.warning(f"An error occurred while calculating minimum income: {e}")
        else:
            st.warning("Please calculate affordability and ensure filters are applied to see the required combined annual income for each town.")

    else:
        st.warning("Please fill in the required inputs to calculate affordability.")

    # Display Filtered Data
    st.header("Filtered Data")
    st.dataframe(filtered_data, use_container_width=True)
except Exception as e:
    st.warning(e)
    st.warning(f"An error occurred while applying filters. Please ensure that all filters are set before continuing.")


