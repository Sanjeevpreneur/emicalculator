import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="EMI Calculator with Prepayment", page_icon="💰")
st.title("EMI Calculator with Part-Prepayment Feature")

def calculate_emi(principal, rate, tenure_months):
    monthly_rate = rate / 1200
    emi = (principal * monthly_rate * (1 + monthly_rate)**tenure_months) / \
          ((1 + monthly_rate)**tenure_months - 1)
    return emi

def generate_schedule(principal, rate, emi, tenure_months):
    schedule = []
    remaining_principal = principal
    total_interest = 0
    
    for month in range(1, tenure_months + 1):
        interest = remaining_principal * rate / 1200
        principal_component = emi - interest
        remaining_principal -= principal_component
        total_interest += interest
        
        schedule.append({
            "Month": month,
            "EMI": emi,
            "Principal": principal_component,
            "Interest": interest,
            "Remaining Principal": max(remaining_principal, 0)
        })
        
        if remaining_principal < 1:  # Loan fully paid
            break
            
    return pd.DataFrame(schedule), total_interest

with st.expander("Loan Details", expanded=True):
    col1, col2, col3 = st.columns(3)
    principal = col1.number_input("Loan Amount (₹)", min_value=1000, value=5000000, step=100000)
    interest_rate = col2.number_input("Annual Interest Rate (%)", min_value=0.1, value=8.5, step=0.1)
    tenure_years = col3.number_input("Loan Tenure (Years)", min_value=1, value=20, step=1)

tenure_months = tenure_years * 12
original_emi = calculate_emi(principal, interest_rate, tenure_months)
original_schedule, original_total_interest = generate_schedule(principal, interest_rate, original_emi, tenure_months)

with st.expander("Part-Prepayment Details"):
    prepayment_month = st.number_input("Prepayment Month", min_value=1, max_value=tenure_months, value=12)
    prepayment_amount = st.number_input("Prepayment Amount (₹)", min_value=1000, value=100000, step=1000)
    adjustment_type = st.radio("Adjustment Type", ["Reduce Tenure", "Reduce EMI"])

# Calculate prepayment impact
if prepayment_amount > 0:
    # Find remaining principal at prepayment month
    prepayment_remaining = original_schedule[original_schedule["Month"] == prepayment_month]["Remaining Principal"].values[0]
    
    if prepayment_amount > prepayment_remaining:
        st.error("Prepayment amount cannot exceed remaining principal!")
    else:
        new_principal = prepayment_remaining - prepayment_amount
        remaining_months = tenure_months - prepayment_month
        
        if adjustment_type == "Reduce Tenure":
            new_emi = original_emi
            new_tenure_months = math.ceil((math.log(new_emi/(new_emi - new_principal*interest_rate/1200)) /
                                         math.log(1 + interest_rate/1200)))
        else:
            new_emi = calculate_emi(new_principal, interest_rate, remaining_months)
            new_tenure_months = remaining_months
        
        new_schedule, new_total_interest = generate_schedule(new_principal, interest_rate, new_emi, new_tenure_months)
        interest_saved = original_total_interest - (original_schedule[:prepayment_month]["Interest"].sum() + new_total_interest)

        # Display results
        st.subheader("Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Original EMI", f"₹{original_emi:,.0f}")
        col2.metric("New EMI", f"₹{new_emi:,.0f}")
        col3.metric("Interest Saved", f"₹{interest_saved:,.0f}")

        col1, col2 = st.columns(2)
        col1.metric("Original Tenure", f"{tenure_years} years")
        col2.metric("New Tenure", f"{math.ceil(new_tenure_months/12)} years")

        # Visualization
        fig, ax = plt.subplots()
        ax.plot(original_schedule["Month"], original_schedule["Remaining Principal"], label="Original")
        ax.plot(new_schedule["Month"] + prepayment_month, new_schedule["Remaining Principal"], label="With Prepayment")
        ax.set_xlabel("Month")
        ax.set_ylabel("Remaining Principal (₹)")
        ax.set_title("Repayment Schedule Comparison")
        ax.legend()
        st.pyplot(fig)

        # Show schedule
        st.write("### Revised Payment Schedule")
        st.dataframe(new_schedule)
else:
    st.subheader("Original Repayment Plan")
    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly EMI", f"₹{original_emi:,.0f}")
    col2.metric("Total Interest", f"₹{original_total_interest:,.0f}")
    col3.metric("Total Payment", f"₹{principal + original_total_interest:,.0f}")

    fig, ax = plt.subplots()
    ax.plot(original_schedule["Month"], original_schedule["Remaining Principal"])
    ax.set_xlabel("Month")
    ax.set_ylabel("Remaining Principal (₹)")
    ax.set_title("Repayment Schedule")
    st.pyplot(fig)
