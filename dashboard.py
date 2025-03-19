import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Airport Complaint Dashboard", layout="wide")

st.title("✈️ Airport Complaint Logging System")

# ------------------ Upload Audio Section ------------------

st.header("🎙️ Upload New Complaint (Audio)")

audio_file = st.file_uploader("Upload Audio File (wav/mp3)", type=["wav", "mp3"])

if audio_file is not None:
    with st.spinner("Processing Audio..."):
        files = {"file": (audio_file.name, audio_file, "audio/wav")}
        try:
            # ✅ FIXED URL here:
            response = requests.post("http://127.0.0.1:5000/upload", files=files)
            response.raise_for_status()
            result = response.json()

            st.success("✅ Complaint uploaded and processed successfully!")

            st.subheader("📝 Transcribed Complaint")
            st.info(result.get("transcription", "No transcription available."))

            st.subheader("📋 Extracted Complaint Details")
            st.json(result.get("data"))

        except Exception as e:
            st.error(f"❌ Error connecting to backend: {e}")
            if hasattr(response, 'text'):
                st.error(f"Response content: {response.text}")

# ------------------ Complaints Dashboard Section ------------------

st.header("📊 Complaints Dashboard")

# Filters
with st.sidebar:
    st.header("🔍 Filter Complaints")
    urgency_options = st.multiselect("Urgency", ["low", "medium", "high"])
    location = st.text_input("Location (optional)")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)

# Prepare GET params
params = {}
if urgency_options:
    params["urgency"] = urgency_options
if location:
    params["location"] = location
if start_date and end_date:
    params["start_date"] = str(start_date)
    params["end_date"] = str(end_date)

try:
    response = requests.get("http://127.0.0.1:5000/complaints", params=params)
    response.raise_for_status()
    complaints = response.json()

    if complaints:
        df = pd.DataFrame(complaints)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        st.dataframe(df, use_container_width=True)

        # Plot by urgency
        fig1 = px.histogram(df, x="urgency", color="urgency", title="Urgency Distribution")
        st.plotly_chart(fig1, use_container_width=True)

        # Plot by location
        fig2 = px.histogram(df, x="location", color="location", title="Complaints by Location")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No complaints found with current filters.")

except Exception as e:
    st.error(f"❌ Failed to load dashboard data: {e}")
