import streamlit as st
import requests
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Airport APOC Dashboard", layout="wide")

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        .main {background-color: #f0f2f6;}
        .stButton>button {
            background: linear-gradient(90deg, #1f77b4, #4dabf7);
            color: white; padding: 0.5em 1.5em; border-radius: 8px; border: none;
        }
        .stButton>button:hover {background: linear-gradient(90deg, #004999, #1f77b4);}
        .stSelectbox>div>div>div, .stTextInput>div>div>input {border-radius: 8px;}
        .stFileUploader>div {border: 2px dashed #4dabf7; padding: 10px; border-radius: 8px;}
        .metric-container {
            background: white; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: 0.3s ease-in-out;
        }
        .metric-container:hover {transform: translateY(-5px); box-shadow: 0 6px 15px rgba(0,0,0,0.2);}
        .stDataFrame {border-radius: 10px; overflow: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("✈️ APOC - Airport Operations Complaint Dashboard")
st.markdown("### 🎙️ Real-time Complaint Monitoring & Voice-to-Text System")

# --- Upload Audio ---
st.header("📤 Upload Complaint Audio")
audio_file = st.file_uploader("Upload Audio File (wav/mp3)", type=["wav", "mp3"])
if audio_file is not None:
    with st.spinner("Processing Audio..."):
        files = {"file": (audio_file.name, audio_file, "audio/wav")}
        try:
            response = requests.post("http://127.0.0.1:5000/upload", files=files)
            response.raise_for_status()
            result = response.json()
            st.success("✅ Complaint uploaded and processed successfully!")
            
            # 🔵 Show transcribed speech text
            st.subheader("📝 Transcribed Complaint")
            st.info(result.get("transcription", "No transcription available."))
            
            # 🔵 Show extracted details
            st.subheader("📋 Extracted Complaint Details")
            st.json(result.get("data"))
        except Exception as e:
            st.error(f"❌ Error connecting to backend: {e}")

st.divider()

# --- Filters ---
with st.sidebar:
    st.header("🎛️ Filters")
    date_option = st.selectbox("Date Range", ["Last 7 days", "Last 30 days", "All Time"])
    urgency_filter = st.multiselect("Urgency", ["low", "normal", "high", "urgent"], default=[])
    location_filter = st.text_input("Location (e.g., Terminal 1)", value="")

# --- Fetch Complaints ---
params = {}
if date_option == "Last 7 days":
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    params["date"] = start_date.isoformat()
elif date_option == "Last 30 days":
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    params["date"] = start_date.isoformat()

if urgency_filter:
    params["urgency"] = urgency_filter

if location_filter:
    params["location"] = location_filter

response = requests.get("http://127.0.0.1:5000/complaints", params=params)

try:
    data = response.json()
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        # --- Metrics ---
        st.subheader("📊 Dashboard Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Total Complaints", len(df))
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Urgent Complaints", len(df[df['urgency'] == 'urgent']))
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("High Urgency", len(df[df['urgency'] == 'high']))
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Unique Locations", df['location'].nunique())
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Complaint Data Table ---
        st.subheader("📄 Complaint Records")
        st.dataframe(df[["date", "issue", "urgency", "location", "raw_text", "status"]], use_container_width=True)

        # --- Visualizations ---
        st.subheader("📈 Trends & Insights")

        col5, col6 = st.columns(2)
        with col5:
            # Complaints by Location
            loc_chart = df['location'].value_counts().reset_index()
            loc_chart.columns = ['Location', 'Count']
            fig1 = px.bar(loc_chart, x='Location', y='Count', color='Location',
                          color_discrete_sequence=px.colors.qualitative.Set2,
                          title="Complaints by Location")
            st.plotly_chart(fig1, use_container_width=True)

        with col6:
            # Complaints by Issue Type
            issue_chart = df['issue'].value_counts().reset_index()
            issue_chart.columns = ['Issue', 'Count']
            fig2 = px.pie(issue_chart, names='Issue', values='Count', hole=0.4,
                          title="Complaint Distribution by Issue (Donut)",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, use_container_width=True)

        # Line chart for complaint trends
        st.subheader("📅 Complaints Over Time")
        daily = df.groupby('date').size().reset_index(name="Complaints")
        fig3 = px.line(daily, x='date', y='Complaints', markers=True, title="Complaint Trends Over Time")
        st.plotly_chart(fig3, use_container_width=True)

        # --- Heatmap for Location vs Urgency ---
        st.subheader("🔥 Heatmap: Location vs Urgency")
        heat_df = df.groupby(['location', 'urgency']).size().reset_index(name='count')
        fig4 = px.density_heatmap(
            heat_df, x='location', y='urgency', z='count', color_continuous_scale="Viridis",
            title="Complaint Density Heatmap"
        )
        st.plotly_chart(fig4, use_container_width=True)

        # --- Donut Chart for Complaint Status ---
        st.subheader("🟢 Complaint Status Overview")
        status_chart = df['status'].value_counts().reset_index()
        status_chart.columns = ['Status', 'Count']
        fig5 = px.pie(status_chart, names='Status', values='Count', hole=0.5,
                      title="Complaint Status Distribution",
                      color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig5, use_container_width=True)

    else:
        st.info("⚠️ No complaints found for the selected filters.")
except Exception as e:
    st.error(f"❌ Backend error: {e}")
    st.error(f"Response content: {response.text}")
