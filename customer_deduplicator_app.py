import streamlit as st
import pandas as pd
from datetime import date
import os

# Set up app title and description
st.title("Customer De-duplicator")
st.markdown("""
Upload today's customer list. The tool will store it by date and compare it with the previous day's list to find **new customers**.
""")

# Upload today's customer list
uploaded_file = st.file_uploader("Upload CSV with a 'customer' column", type=["csv"])

if uploaded_file:
    # Load today's customers
    today_df = pd.read_csv(uploaded_file)
    if 'customer' not in today_df.columns:
        st.error("The uploaded CSV must contain a 'customer' column.")
    else:
        today_customers = today_df['customer'].dropna().astype(str).unique()

        # Prepare file storage
        today = date.today().isoformat()
        os.makedirs("data", exist_ok=True)
        today_filename = f"data/{today}.csv"

        # Save today's customers
        pd.DataFrame(today_customers, columns=["customer"]).to_csv(today_filename, index=False)
        st.success(f"Saved today's list under {today_filename}")

        # Load all stored dates
        all_files = sorted([f for f in os.listdir("data") if f.endswith(".csv")])
        all_dates = [f.replace(".csv", "") for f in all_files]

        # Compare with the previous day's data if available
        if len(all_dates) > 1 and today in all_dates:
            today_index = all_dates.index(today)
            if today_index > 0:
                yesterday = all_dates[today_index - 1]
                prev_customers = pd.read_csv(f"data/{yesterday}.csv")['customer'].dropna().astype(str).unique()
                new_customers = list(set(today_customers) - set(prev_customers))

                st.subheader("New Customers Compared to Yesterday")
                st.write(new_customers)

                # Downloadable CSV
                st.download_button(
                    label="Download New Customers CSV",
                    data=pd.DataFrame(new_customers, columns=["customer"]).to_csv(index=False),
                    file_name="new_customers.csv",
                    mime="text/csv"
                )
            else:
                st.info("Today is the first entry. No comparison available.")
        else:
            st.info("No previous data to compare. Saved today's list.")
