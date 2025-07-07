import streamlit as st
import pandas as pd
import os
from datetime import date

# ---------- Config ----------
MASTER_FILE = "master_file_A.xlsx"

# ---------- Inputs ----------
st.title("Lead Nurturing Session Tool")

session_type = st.radio("Is this your first session?", ["Yes", "No"])
nurturing_file = st.file_uploader("Upload Nurturing List (CSV or Excel)", type=["csv", "xlsx"])
priority_file = st.file_uploader("Upload Priority Table (CSV or Excel)", type=["csv", "xlsx"])
template_repository = st.text_area("Enter Template Repository (one template per line)")

if nurturing_file and priority_file and template_repository:
    # Load input files
    def load_file(f):
        if f.name.endswith("csv"):
            return pd.read_csv(f)
        else:
            return pd.read_excel(f)

    leads_df = load_file(nurturing_file)
    priority_df = load_file(priority_file)
    templates = [t.strip() for t in template_repository.splitlines() if t.strip()]

    # Merge leads with priority
    leads_df = leads_df.merge(priority_df, on="Phone Number", how="left")
    leads_df["Priority"] = leads_df["Priority"].fillna(999)  # Default low priority if not found
    leads_df = leads_df.sort_values("Priority")

    # If not first session, load master and filter leads already sent 3+ times
    if session_type == "No" and os.path.exists(MASTER_FILE):
        master_df = pd.read_excel(MASTER_FILE)
        leads_df = leads_df[~leads_df["Phone Number"].isin(master_df[master_df["Count"] >= 3]["Phone Number"])]
    else:
        master_df = pd.DataFrame()

    # Show filtered leads
    st.subheader("Filtered Leads")
    leads_df = leads_df.drop_duplicates("Phone Number")
    leads_df["Date"] = date.today()
    leads_df["Sent"] = False
    leads_df["Template"] = ""

    edited_df = st.data_editor(
        leads_df[["Date", "Phone Number", "Priority", "Sent", "Template"]],
        num_rows="dynamic",
        column_config={"Template": st.column_config.SelectboxColumn("Template", options=templates)},
        use_container_width=True,
        key="editor1"
    )

    if st.button("Submit"):
        # Filter sent entries
        sent_df = edited_df[edited_df["Sent"] == True].copy()

        # Update master
        for _, row in sent_df.iterrows():
            phone = row["Phone Number"]
            template = row["Template"]
            send_date = row["Date"]

            if phone in master_df["Phone Number"].values:
                idx = master_df[master_df["Phone Number"] == phone].index[0]
                master_df.at[idx, "Count"] += 1
                c = master_df.at[idx, "Count"]
                master_df.at[idx, f"Date of template {c}"] = send_date
                master_df.at[idx, f"Template {c}"] = template
            else:
                new_entry = {
                    "Phone Number": phone,
                    "Status": "Sent",
                    "Count": 1,
                    "Date of template 1": send_date,
                    "Template 1": template,
                }
                master_df = pd.concat([master_df, pd.DataFrame([new_entry])], ignore_index=True)

        # Save master file
        master_df.to_excel(MASTER_FILE, index=False)
        st.success("Session data submitted and master file updated.")
        st.download_button(
            "Download Master File",
            data=master_df.to_excel(index=False, engine='openpyxl'),
            file_name="master_file_A.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
