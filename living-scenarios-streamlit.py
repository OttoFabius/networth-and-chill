import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

st.title("Rent vs Buy Net Wealth Comparison (NL)")

# Inputs
initial_cash = st.number_input("Initial cash available (EUR)", min_value=0.0, value=50000.0)
ownership_pct = st.slider("Home purchase fraction of €700k house (%)", 0, 100, 50)
home_value = ownership_pct/100 * 700_000
st.write(f"Effective home value: €{home_value:,.0f}")

monthly_rent = st.number_input("Monthly rent (EUR)", min_value=0.0, value=1100.0)

# Mortgage
mortgage_rate = st.number_input("Annual mortgage rate (%)", min_value=0.0, value=3.5) / 100
amort_years = 30

# Sunk costs & maintenance
mortgage_advisor = st.checkbox("Include mortgage advisor cost? (EUR)", value=True)
advisor_cost = st.number_input("Mortgage advisor cost (EUR)", min_value=0.0, value=2000.0) if mortgage_advisor else 0.0
sunk = 1500 + home_value*0.02 + advisor_cost

down_payment = max(0.0, initial_cash - sunk)
st.write(f"Calculated down payment: €{down_payment:,.0f}")

# Scenario definitions
st.sidebar.header("ROI & Appreciation scenarios")
scenarios = {
    "Pessimistic": {},
    "Expected": {},
    "Optimistic": {}
}
for name in scenarios:
    st.sidebar.subheader(name)
    if name != "Buying":
        scenarios[name]["roi"] = st.sidebar.number_input(f"Gross ROI {name} (%)", value={"Pessimistic":1, "Expected":7, "Optimistic":12}[name]) / 100
        scenarios[name]["tax"] = st.sidebar.number_input(f"Annual cap-gains tax {name} (%)", value={"Pessimistic":0.33, "Expected":2.2, "Optimistic":2.2}[name]) / 100
    scenarios[name]["app"] = st.sidebar.number_input(f"House appreciation {name} (%)", value={"Pessimistic":1, "Expected":3, "Optimistic":5}[name]) / 100

# Amortization helper
def mortgage_schedule(principal, annual_rate, total_months, months):
    r = annual_rate/12
    payment = r * principal / (1 - (1+r) ** (-total_months))
    balance = principal
    total_paid = 0.0
    total_interest = 0.0
    for m in range(1, months+1):
        interest = balance * r
        principal_paid = payment - interest
        balance -= principal_paid
        total_paid += payment
        total_interest += interest
    return total_paid, total_interest

# Checkbox to include tax benefits
include_tax_benefits = st.checkbox("Include tax benefits in buying scenario", value=False)

# Compute results
years = list(range(1,6))
records = []
expected_rent_5y = 0.0
expected_buy_5y = 0.0
for name, params in scenarios.items():
    for y in years:
        # Renting
        roi = params["roi"]
        tax = params["tax"]
        invest_after_tax = initial_cash * (1 + roi * (1-tax))**y
        total_rent = monthly_rent * 12 * y
        net_rent = invest_after_tax - total_rent

        # Buying
        maintenance = home_value * 0.01 * y
        total_months = amort_years * 12
        paid, interest = mortgage_schedule(home_value - down_payment, mortgage_rate, total_months, y*12)
        principal_paid = paid - interest
        tax_benefit = interest * 0.38 if include_tax_benefits else 0.0
        growth = home_value * ((1+params["app"])**y - 1)

        net_buy = growth + principal_paid + down_payment - sunk - maintenance - interest + tax_benefit

        if name == "Expected" and y == 5:
            expected_rent_5y = net_rent
            expected_buy_5y = net_buy

        records.append({"Year": y, "Scenario": name, "Type": f"{name} - Rent", "Net Wealth": net_rent})
        records.append({"Year": y, "Scenario": name, "Type": f"{name} - Buy",  "Net Wealth": net_buy})

# Show summary results for Expected scenario after 5 years
st.subheader("5-Year Net Wealth (Expected Scenario)")
st.write(f"**Renting:** €{expected_rent_5y:,.0f}")
st.write(f"**Buying:** €{expected_buy_5y:,.0f}")

df = pd.DataFrame(records)

chart = alt.Chart(df).mark_line(point=True).encode(
    x='Year:O', 
    y='Net Wealth:Q', 
    color=alt.Color('Type:N', title='Scenario - Strategy'),
    tooltip=['Year', 'Type', 'Net Wealth']
).properties(width=700, height=400)

st.altair_chart(chart)

if st.checkbox("Show data table"):
    st.dataframe(df)
