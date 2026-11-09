import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Page Config
st.set_page_config(
    page_title="Live Weather Anomaly Dashboard",
    page_icon="🌤️",
    layout="wide"
)

st.title("🌤️ Automated Public Weather & Anomaly Dashboard")
st.markdown("This micro-app fetches live hourly weather data from the public [Open-Meteo API](https://open-meteo.com/), processes it with Pandas, and highlights statistical anomalies.")

@st.cache_data(ttl=3600)
def fetch_weather_data():
    # Free public API endpoint for Berlin (or change latitude/longitude to your city)
    url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&past_days=7&forecast_days=3"
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["hourly"]["time"]),
        "temperature": data["hourly"]["temperature_2m"],
        "humidity": data["hourly"]["relative_humidity_2m"],
        "wind_speed": data["hourly"]["wind_speed_10m"]
    })
    return df

# Load data
with st.spinner("Fetching live data from public API..."):
    df = fetch_weather_data()

# Data Transformation & Anomaly Detection
df["rolling_mean"] = df["temperature"].rolling(window=24, min_periods=1).mean()
df["anomaly"] = abs(df["temperature"] - df["rolling_mean"]) > (2 * df["temperature"].std())

# Sidebar Filters
st.sidebar.header("Dashboard Controls")
metric_choice = st.sidebar.selectbox("Select Metric to Visualize", ["temperature", "humidity", "wind_speed"])
show_anomalies = st.sidebar.checkbox("Highlight Statistical Anomalies", value=True)

# Main Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Latest Temperature", f"{df['temperature'].iloc[-1]} °C")
col2.metric("Average Humidity", f"{df['humidity'].mean():.1f}%")
col3.metric("Max Wind Speed", f"{df['wind_speed'].max()} km/h")

st.divider()

# Interactive Plotly Chart
fig = px.line(
    df, 
    x="timestamp", 
    y=metric_choice, 
    title=f"Hourly {metric_choice.capitalize()} with Rolling Trend",
    labels={"timestamp": "Time", metric_choice: metric_choice.capitalize()}
)

if show_anomalies and metric_choice == "temperature":
    anomalies = df[df["anomaly"]]
    fig.add_scatter(
        x=anomalies["timestamp"], 
        y=anomalies[metric_choice], 
        mode="markers", 
        marker=dict(color="red", size=8),
        name="Anomaly"
    )

fig.update_layout(template="plotly_white", height=450)
st.plotly_chart(fig, use_container_width=True)

# Raw Data Preview
with st.expander("View Raw Processed Dataset"):
    st.dataframe(df, use_container_width=True)