import streamlit as st

st.title("Matrix Coding Agent — Smoke Test")

opening_cash = 1000
receipts = 300
payroll = 120
vendors = 140

ending_cash = opening_cash + receipts - payroll - vendors

st.write(f"Ending Cash: {ending_cash}")