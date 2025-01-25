import pandas as pd
import numpy_financial as npf
from data_loader import load_ehg_data

def calculate_grants(st):
    """Handles user input and calculates grant amounts."""
    with st.form("affordability_form"):
        st.subheader("Enter Your Details")
        is_couple = st.radio("Are you applying as a couple or single?", ["Couple", "Single"])
        citizen_status = st.radio(
            "Couple Composition:",
            ["2 Singapore Citizens (SC)", "1 SC and 1 Singapore Permanent Resident (SPR)", "SC and Non-Resident Spouse"]
        )
        annual_income = st.number_input("Your Annual Income (SGD):", min_value=0, value=60000)
        spouse_income = st.number_input("Spouse's Annual Income (SGD):", min_value=0) if is_couple == "Couple" else 0
        cpf_oa = st.number_input("Your CPF OA Balance (SGD):", min_value=0)
        spouse_cpf_oa = st.number_input("Spouse's CPF OA Balance (SGD):", min_value=0) if is_couple == "Couple" else 0
        personal_cash = st.number_input("Your Personal Cash Savings (SGD):", min_value=0)
        spouse_cash = st.number_input("Spouse's Cash Savings (SGD):", min_value=0) if is_couple == "Couple" else 0
        monthly_debt = st.number_input("Total of your other MONTHLY debt obligations, e.g. Car, Education, Personal Loan, etc:", min_value=0)
        spouse_monthly_debt = st.number_input("Total of your spouse's other MONTHLY debt obligations, e.g. Car, Education, Personal Loan, etc:", min_value=0) \
            if is_couple == "Couple" else 0
        proximity_option = st.radio(
            "Proximity to Parents/Children:",
            ["Not Applicable", "Live with", "Live near (within 4km)"]
        )
        loan_tenure = st.slider("Loan Tenure (Years):", min_value=5, max_value=30, value=25)
        flat_size = st.radio("Flat Size:", ["2 to 4-room", "5-room or larger"])

        loan_type_input = st.radio(
            "Choose your loan type:",
            options=["HDB Loan (2.6%)", "Bank Loan"],
            index=0
        )

        # Default loan interest rate for HDB Loan
        loan_interest_rate = 0.026

        # If Bank Loan is selected, prompt for customizable interest rate
        if loan_type_input == "Bank Loan":
            bank_loan_interest = st.number_input(
                "Enter your Bank Loan Interest Rate (%):",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.1,
                format="%.2f"
            )
            loan_interest_rate = bank_loan_interest / 100  # Convert percentage to decimal

        submitted = st.form_submit_button("Calculate Affordability")

    if submitted:
        return {
            "is_couple": is_couple,
            "citizen_status": citizen_status,
            "annual_income": annual_income,
            "spouse_income": spouse_income,
            "cpf_oa": cpf_oa,
            "spouse_cpf_oa": spouse_cpf_oa,
            "personal_cash": personal_cash,
            "spouse_cash": spouse_cash,
            "proximity_option": proximity_option,
            "loan_tenure": loan_tenure,
            "flat_size": flat_size,
            "loan_type_input": loan_type_input,
            "loan_interest_rate": loan_interest_rate,
            "monthly_debt": monthly_debt,
            "spouse_monthly_debt": spouse_monthly_debt
        }
    return None

def calculate_affordability(
    is_couple,
    citizen_status,
    annual_income,
    spouse_income,
    cpf_oa,
    spouse_cpf_oa,
    personal_cash,
    spouse_cash,
    proximity_option,
    loan_tenure,
    flat_size,
    loan_interest_rate,
    loan_type_input,
    monthly_debt,
    spouse_monthly_debt
):
    """
    Calculate affordability based on user inputs.
    Args:
        is_couple: Whether the buyer is a couple or single.
        citizen_status: The citizenship status of the buyer(s).
        annual_income: The buyer's annual income.
        spouse_income: The spouse's annual income (if applicable).
        cpf_oa: CPF Ordinary Account savings of the buyer.
        spouse_cpf_oa: CPF Ordinary Account savings of the spouse.
        personal_cash: Personal cash savings of the buyer.
        spouse_cash: Personal cash savings of the spouse (if applicable).
        proximity_option: Whether the buyer is living with/near family.
        loan_tenure: Loan tenure in years.
        flat_size: The size of the flat being purchased.
        loan_interest_rate: Selected loan interest rate (HDB Loan or Bank Loan).
        loan_type_input: The type of loan selected by the user ("HDB" or "Bank").
        monthly_debt: Other monthly debt obligations of the buyer.
        spouse_monthly_debt: Other monthly debt obligations of the spouse.
    Returns:
        A dictionary with calculated affordability components.
    """
    LOAN_THRESHOLD = 168000  # Income threshold for HDB loan eligibility

    # Total household income and monthly income
    total_income = annual_income + (spouse_income if is_couple == "Couple" else 0)
    monthly_income = total_income / 12

    # Total CPF savings and personal cash
    total_cpf = cpf_oa + (spouse_cpf_oa if is_couple == "Couple" else 0)
    total_cash = personal_cash + (spouse_cash if is_couple == "Couple" else 0)

    # Load EHG data based on couple/single status
    ehg_file = "data/ehg_couples_families.csv" if is_couple == "Couple" else "data/ehg_singles.csv"
    ehg_data = load_ehg_data(ehg_file, is_couple=(is_couple == "Couple"))

    # Calculate EHG amount based on income range
    applicable_row = ehg_data[
        (ehg_data["min_income"] <= monthly_income) & (monthly_income <= ehg_data["max_income"])
    ]
    ehg_amount = applicable_row["EHG Amount (SGD)"].iloc[0] if not applicable_row.empty else 0

    # Determine Family Grant or Singles Grant
    family_grant = 0
    if is_couple == "Couple":
        if monthly_income > 14000:
            family_grant = 0  # Exceeds income ceiling
        else:
            if citizen_status in ["2 Singapore Citizens (SC)", "1 SC and 1 Singapore Permanent Resident (SPR)"]:
                family_grant = 80000 if flat_size == "2 to 4-room" else 50000
                if citizen_status == "1 SC and 1 Singapore Permanent Resident (SPR)":
                    family_grant -= 10000
            elif citizen_status == "SC and Non-Resident Spouse":
                family_grant = 40000 if flat_size == "2 to 4-room" else 25000
    else:
        if monthly_income > 7000:
            family_grant = 0  # Exceeds income ceiling for singles
        else:
            family_grant = 40000 if flat_size == "2 to 4-room" else 25000

    # Proximity Housing Grant (PHG)
    phg = 0
    if proximity_option == "Live with":
        phg = 30000 if citizen_status in ["2 Singapore Citizens (SC)", "1 SC and 1 Singapore Permanent Resident (SPR)"] else 15000
    elif proximity_option == "Live near (within 4km)":
        phg = 20000 if citizen_status in ["2 Singapore Citizens (SC)", "1 SC and 1 Singapore Permanent Resident (SPR)"] else 10000

    # Total debt obligations
    total_monthly_debt = monthly_debt + (spouse_monthly_debt if is_couple == "Couple" else 0)

    # # Calculate the remaining TDSR allowance
    # tdsr_cap = monthly_income * 0.55
    # remaining_tdsr_allowance = max(tdsr_cap - total_monthly_debt, 0)

    # import streamlit as st
    # st.write(loan_type_input, monthly_income)

    # Determine loan type and calculate maximum loan eligibility based on user input
    if loan_type_input == "HDB":
        if total_income > LOAN_THRESHOLD:
            raise ValueError("HDB loans are not allowed for income above SGD 168,000.")
        max_loan = calculate_hdb_loan(monthly_income, total_monthly_debt, loan_tenure, 0.026)  # Fixed HDB rate
    elif loan_type_input == "Bank":
        max_loan = calculate_bank_loan(monthly_income, total_monthly_debt, loan_tenure, loan_interest_rate)
    else:
        raise ValueError("Invalid loan type. Please select either 'HDB' or 'Bank'.")

    # Apply 30% gross income cap for loan eligibility
    repayment_cap = monthly_income * 0.30
    max_loan = min(max_loan, calculate_loan_from_repayment(repayment_cap, loan_tenure, loan_interest_rate))

    # Calculate monthly repayment based on loan type
    monthly_repayment = calculate_monthly_repayment(max_loan, loan_tenure, loan_interest_rate)

    # Total affordability calculation
    total_grants = ehg_amount + family_grant + phg
    total_affordability = max_loan + total_cpf + total_cash + total_grants

    return {
        "Enhanced CPF Housing Grant (EHG)": f"SGD {ehg_amount:,.0f}",
        "Family Grant (or Singles Grant)": f"SGD {family_grant:,.0f}",
        "Proximity Housing Grant (PHG)": f"SGD {phg:,.0f}",
        "Total Grants Available": f"SGD {total_grants:,.0f}",
        "Maximum Loan Eligibility": f"SGD {max_loan:,.0f}",
        "Total Personal and Spouse Savings": f"SGD {total_cash:,.0f}",
        "Loan Interest Rate": f"{loan_interest_rate * 100:.2f}%",
        "Loan Type": loan_type_input,
        "Monthly Repayment": f"SGD {monthly_repayment:,.0f}",
        "Total Affordability": f"SGD {total_affordability:,.0f}"
    }


def calculate_hdb_loan(monthly_income, total_monthly_debt, loan_tenure_years, interest_rate):
    """
    Calculate the maximum HDB loan amount based on MSR (30% of gross monthly income).
    """
    # HDB's Mortgage Servicing Ratio (MSR) is 30% of gross monthly income
    msr_limit = 0.30 * monthly_income

    # Check TDSR
    remaining_debt_limit = max(0, 0.55 * monthly_income - total_monthly_debt)
    msr_limit = min(remaining_debt_limit, msr_limit)

    # Monthly interest rate
    monthly_interest_rate = interest_rate / 12

    # Number of monthly payments
    num_payments = loan_tenure_years * 12

    # Calculate maximum loan amount based on MSR
    if monthly_interest_rate > 0:
        max_loan = (msr_limit * (1 - (1 + monthly_interest_rate) ** -num_payments)) / monthly_interest_rate
    else:
        max_loan = msr_limit * num_payments

    return max_loan

def calculate_bank_loan(monthly_income, total_monthly_debt, loan_tenure_years, interest_rate):
    """
    Calculate the maximum bank loan amount based on TDSR (55% of gross monthly income).
    """
    # HDB's Mortgage Servicing Ratio (MSR) is 30% of gross monthly income
    msr_limit = 0.30 * monthly_income

    # Check TDSR
    remaining_debt_limit = max(0, 0.55 * monthly_income - total_monthly_debt)
    msr_limit = min(remaining_debt_limit, msr_limit)

    # Monthly interest rate
    monthly_interest_rate = interest_rate / 12

    # Number of monthly payments
    num_payments = loan_tenure_years * 12

    # Calculate maximum loan amount based on TDSR
    if monthly_interest_rate > 0:
        max_loan = (msr_limit * (1 - (1 + monthly_interest_rate) ** -num_payments)) / monthly_interest_rate
    else:
        max_loan = msr_limit * num_payments

    return max_loan

def calculate_loan_from_repayment(repayment_cap, loan_tenure, interest_rate):
    """
    Calculate the maximum loan amount based on a repayment cap.
    """
    monthly_interest_rate = interest_rate / 12
    num_payments = loan_tenure * 12

    if monthly_interest_rate > 0:
        max_loan = (repayment_cap * (1 - (1 + monthly_interest_rate) ** -num_payments)) / monthly_interest_rate
    else:
        max_loan = repayment_cap * num_payments

    return max_loan

def calculate_monthly_repayment(loan_amount, loan_tenure, interest_rate):
    """
    Calculate monthly repayment for the loan.
    """
    monthly_interest_rate = interest_rate / 12
    num_payments = loan_tenure * 12
    if monthly_interest_rate > 0:
        monthly_repayment = loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** num_payments / \
                            ((1 + monthly_interest_rate) ** num_payments - 1)
    else:
        monthly_repayment = loan_amount / num_payments
    return monthly_repayment
