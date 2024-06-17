import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key="sk-proj-oKiDwOZxcqoulcwiGQEcT3BlbkFJ0R6dA0U2RhkC2R1POgIb",
)

# Function to call OpenAI API
def call_openai_api(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Or another model like gpt-4
        messages=[
            {"role": "system", "content": "You are a helpful mortgage calculator and home expense assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

def loan_amortization(principal, annual_interest_rate, years, pmi_rate, purchase_price):
    # Calculate the monthly interest rate
    monthly_interest_rate = annual_interest_rate / 12 / 100
    # Total number of payments
    number_of_payments = years * 12
    # PMI threshold
    pmi_threshold = 0.8 * purchase_price
    
    # Calculate the monthly payment using the formula for annuity
    monthly_payment = (principal * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -number_of_payments)
    
    # Initialize the schedule list
    schedule = []
    
    # Initialize the remaining balance
    remaining_balance = principal
    
    for month in range(1, number_of_payments + 1):
        # Calculate the interest for the current month
        interest_payment = remaining_balance * monthly_interest_rate
        # Calculate the principal for the current month
        principal_payment = monthly_payment - interest_payment
        # Deduct the principal payment from the remaining balance
        remaining_balance -= principal_payment
        
        # Calculate PMI if applicable
        pmi_payment = 0
        if remaining_balance > pmi_threshold:
            pmi_payment = (pmi_rate / 12 / 100) * principal
        
        # Append the details for the current month to the schedule
        schedule.append({
            'Month': month,
            'Payment': round(monthly_payment + pmi_payment, 2),
            'Principal Paid': round(principal_payment, 2),
            'Interest Paid': round(interest_payment, 2),
            'PMI Paid': round(pmi_payment, 2),
            'Remaining Balance': round(remaining_balance, 2)
        })
    
    return round(monthly_payment, 2), schedule

def aggregate_amortization(schedule, aggregation_period):
    # Convert the aggregation period from years to months
    period = aggregation_period * 12
    
    # Initialize list to hold aggregated results for each period
    aggregated_results = []
    
    for year in range(1, len(schedule) // period + 1):
        # Initialize aggregates for the current period
        total_payment = 0
        total_principal = 0
        total_interest = 0
        total_pmi = 0
        remaining_balance = 0
        
        # Calculate start and end index for the current period
        start_idx = (year - 1) * period
        end_idx = min(year * period, len(schedule))
        
        for i in range(start_idx, end_idx):
            total_payment += schedule[i]['Payment']
            total_principal += schedule[i]['Principal Paid']
            total_interest += schedule[i]['Interest Paid']
            total_pmi += schedule[i]['PMI Paid']
            remaining_balance = schedule[i]['Remaining Balance']
        
        # Store the results for the current period
        aggregated_results.append({
            'Period (Years)': year * aggregation_period,
            'Total Payment': round(total_payment, 2),
            'Total Principal': round(total_principal, 2),
            'Total Interest': round(total_interest, 2),
            'Total PMI': round(total_pmi, 2),
            'Remaining Balance': round(remaining_balance, 2)
        })
    
    return aggregated_results

def plot_amortization_chart(amortization_df, show_pmi):
    plt.figure(figsize=(10, 6))
    plt.plot(amortization_df['Month'], amortization_df['Interest Paid'], label='Interest Paid')
    plt.plot(amortization_df['Month'], amortization_df['Principal Paid'], label='Principal Paid')
    if show_pmi:
        plt.plot(amortization_df['Month'], amortization_df['PMI Paid'], label='PMI Paid')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.title('Amortization Chart')
    plt.legend()
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

def main():
    st.title("Mortgage and Home Expense Calculator")

    # Mortgage Details
    st.header("Mortgage Details")
    purchase_price = st.number_input("Purchase Price ($)", value=350000, min_value=0)
    down_payment_type = st.selectbox("Down Payment Type", ["Amount", "Percentage"])
    
    if down_payment_type == "Amount":
        down_payment = st.number_input("Down Payment Amount ($)", value=50000, min_value=0)
        down_payment_percentage = round((down_payment / purchase_price) * 100, 2)
        st.text_input("Down payment %", value=down_payment_percentage, disabled=True)
    else:
        down_payment_percentage = st.number_input("Down Payment Percentage (%)", value=20.0, min_value=0.0, format="%.2f")
        down_payment = purchase_price * (down_payment_percentage / 100)
        st.text_input("Down payment Amount ($)", value=down_payment, disabled=True)
    
    # Calculate principal amount (loan amount)
    principal = purchase_price - down_payment
    
    st.text_input("Principal Amount ($)", value=principal, disabled=True)
    initial_interest_rate = st.number_input("Initial Interest Rate (%)", value=3.5, min_value=0.0, format="%.2f")
    if down_payment_percentage < 20:
        pmi_rate = st.number_input("PMI Rate (%)", value=0.5, min_value=0.0, format="%.2f")
    else:
        pmi_rate = 0
    loan_term_options = {
        "30 Year Fixed": 30,
        "15 Year Fixed": 15
    }
    loan_term = st.selectbox("Loan Term", list(loan_term_options.keys()))
    years_fixed = loan_term_options[loan_term]
    total_years = 30 if "ARM" in loan_term else years_fixed  # Assume 30 years for ARM loans

    if "ARM" in loan_term:
        subsequent_interest_rate = st.number_input("Subsequent Interest Rate (%)", value=initial_interest_rate + 2.0, min_value=0.0, format="%.2f")
    else:
        subsequent_interest_rate = initial_interest_rate  # No change for fixed loans

        # Home Expenses
    st.header("Home Expenses")
    property_tax = st.number_input("Property Tax ($/month)", value=200, min_value=0)
    home_insurance = st.number_input("Home Insurance ($/month)", value=100, min_value=0)
    hoa_fees = st.number_input("HOA Fees ($/month)", value=50, min_value=0)

    # Calculate amortization schedule
    monthly_payment, amortization_schedule = loan_amortization(principal, initial_interest_rate, total_years, pmi_rate, purchase_price)
    total_monthly_payment = monthly_payment + property_tax + home_insurance + hoa_fees

    # ChatGPT Integration
    # st.header("Any questions?")
    # user_question = st.text_input("Enter your question about mortgage or home expenses:")
    # if st.button("Ask") and user_question:
    #     response = call_openai_api(user_question)
    #     st.write(f"**ChatGPT Response:** {response}")

    # Display Results
    st.subheader("Monthly Payment Breakdown")
    st.write(f"**Initial Monthly Mortgage Payment:** ${monthly_payment:,.2f}")
    st.write(f"**Property Tax:** ${property_tax:,.2f}")
    st.write(f"**Home Insurance:** ${home_insurance:,.2f}")
    st.write(f"**HOA Fees:** ${hoa_fees:,.2f}")
    st.write(f"**Total Monthly Payment:** ${total_monthly_payment:,.2f}")

    breakdown, amortization = st.tabs(["Mortgage Payment Breakdown", "Amortization Schedule"])


    with breakdown:
        aggregation_period = st.selectbox(
        "Payment breakdown (Years)",
        (1, 5, 10))

        st.header(f'Payment info every {aggregation_period} year(s)')
        aggregated_amortization = aggregate_amortization(amortization_schedule, aggregation_period)
        df_aggregated = pd.DataFrame(aggregated_amortization)
        if down_payment_percentage >= 20:
            df_aggregated = df_aggregated.drop(columns=['Total PMI'])
        st.dataframe(df_aggregated)

    with amortization:
        st.header("Amortization Schedule")
        df_amortization = pd.DataFrame(amortization_schedule)
        if down_payment_percentage >= 20:
            df_amortization = df_amortization.drop(columns=['PMI Paid'])
        st.dataframe(df_amortization)

        # Plot amortization chart
        st.header("Amortization Chart")
        plot_amortization_chart(df_amortization, down_payment_percentage < 20)

if __name__ == "__main__":
    main()
