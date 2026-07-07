import streamlit as st
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

import folium
from streamlit_folium import st_folium

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Auto Fare Anomaly Detector",
    layout="centered"
)

st.markdown(
    "<h1 style='text-align:center;'>Auto Fare Anomaly Detector</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center; color:gray;'>Hybrid Machine Learning Based Fare Validation System</p>",
    unsafe_allow_html=True
)

st.divider()

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "distance" not in st.session_state:
    st.session_state.distance = None

if "expected_fare" not in st.session_state:
    st.session_state.expected_fare = None

if "prediction" not in st.session_state:
    st.session_state.prediction = None

if "map" not in st.session_state:
    st.session_state.map = None

# ---------------------------------------------------
# SYNTHETIC DATASET
# ---------------------------------------------------
np.random.seed(42)

samples = 500

distance = np.random.uniform(1, 20, samples)

traffic = np.random.randint(1, 4, samples)
# 1 = Low, 2 = Medium, 3 = High

peak_hour = np.random.randint(0, 2, samples)
# 0 = No, 1 = Yes

weather = np.random.randint(0, 2, samples)
# 0 = Normal, 1 = Rainy

fare = (
    distance * 20
    + traffic * 15
    + peak_hour * 20
    + weather * 10
    + np.random.normal(0, 10, samples)
)

# Add anomalies
for i in range(40):
    fare[i] *= 2.5

# ---------------------------------------------------
# DATAFRAME
# ---------------------------------------------------
df = pd.DataFrame({
    "distance": distance,
    "traffic": traffic,
    "peak_hour": peak_hour,
    "weather": weather,
    "fare": fare
})

# ---------------------------------------------------
# REGRESSION MODEL
# ---------------------------------------------------
X = df[["distance", "traffic", "peak_hour", "weather"]]
y = df["fare"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

regressor = LinearRegression()
regressor.fit(X_train, y_train)

# Predictions for metrics
y_pred = regressor.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

# ---------------------------------------------------
# ISOLATION FOREST
# ---------------------------------------------------
fare_per_km = fare / distance

anomaly_features = np.column_stack((
    distance,
    fare,
    fare_per_km
))

isolation_model = IsolationForest(
    contamination=0.08,
    random_state=42
)

isolation_model.fit(anomaly_features)

# ---------------------------------------------------
# INPUT UI
# ---------------------------------------------------
st.subheader("Enter Ride Details")

with st.form("fare_form"):

    col1, col2 = st.columns(2)

    with col1:
        pickup = st.text_input(
            "Pickup Location",
            placeholder="e.g., BTM Layout"
        )

    with col2:
        drop = st.text_input(
            "Drop Location",
            placeholder="e.g., MG Road"
        )

    fare_input = st.number_input(
        "Enter Fare (₹)",
        min_value=1.0
    )

    col3, col4 = st.columns(2)

    with col3:
        traffic_input = st.selectbox(
            "Traffic Level",
            ["Low", "Medium", "High"]
        )

    with col4:
        weather_input = st.selectbox(
            "Weather",
            ["Normal", "Rainy"]
        )

    peak_input = st.selectbox(
        "Peak Hour",
        ["No", "Yes"]
    )

    submit = st.form_submit_button(
        "Check Fare",
        use_container_width=True
    )

# ---------------------------------------------------
# ENCODING
# ---------------------------------------------------
traffic_map = {
    "Low": 1,
    "Medium": 2,
    "High": 3
}

weather_map = {
    "Normal": 0,
    "Rainy": 1
}

peak_map = {
    "No": 0,
    "Yes": 1
}

# ---------------------------------------------------
# PREDICTION
# ---------------------------------------------------
if submit:

    geolocator = Nominatim(user_agent="fare_app")

    try:
        loc1 = geolocator.geocode(pickup)
        loc2 = geolocator.geocode(drop)

        if loc1 and loc2:

            coord1 = (loc1.latitude, loc1.longitude)
            coord2 = (loc2.latitude, loc2.longitude)

            # Distance
            distance_km = geodesic(coord1, coord2).km

            st.session_state.distance = distance_km

            # Encode inputs
            traffic_encoded = traffic_map[traffic_input]
            weather_encoded = weather_map[weather_input]
            peak_encoded = peak_map[peak_input]

            # ---------------------------------------------------
            # REGRESSION PREDICTION
            # ---------------------------------------------------
            expected_fare = regressor.predict([[
                distance_km,
                traffic_encoded,
                peak_encoded,
                weather_encoded
            ]])[0]

            st.session_state.expected_fare = expected_fare

            # ---------------------------------------------------
            # ANOMALY DETECTION
            # ---------------------------------------------------
            fare_per_km_input = fare_input / distance_km

            anomaly_result = isolation_model.predict([[
                distance_km,
                fare_input,
                fare_per_km_input
            ]])

            st.session_state.prediction = anomaly_result[0]

            # ---------------------------------------------------
            # MAP
            # ---------------------------------------------------
            m = folium.Map(
                location=coord1,
                zoom_start=13
            )

            folium.Marker(
                coord1,
                tooltip="Pickup",
                icon=folium.Icon(color="green")
            ).add_to(m)

            folium.Marker(
                coord2,
                tooltip="Drop",
                icon=folium.Icon(color="red")
            ).add_to(m)

            folium.PolyLine(
                [coord1, coord2],
                color="blue",
                weight=5
            ).add_to(m)

            st.session_state.map = m

        else:
            st.error("Invalid locations entered.")

    except:
        st.error("Error fetching location data.")

# ---------------------------------------------------
# OUTPUT
# ---------------------------------------------------
st.divider()

if st.session_state.distance:

    st.markdown(
        f"### 📏 Distance: `{st.session_state.distance:.2f} km`"
    )

    st.markdown(
        f"### 💰 Predicted Fare: `₹{st.session_state.expected_fare:.2f}`"
    )

if st.session_state.prediction == 1:
    st.success("✅ This fare looks FAIR")

elif st.session_state.prediction == -1:
    st.error("🚨 This fare seems OVERPRICED")

# ---------------------------------------------------
# METRICS
# ---------------------------------------------------
st.divider()

st.subheader("📊 Model Evaluation")

col5, col6 = st.columns(2)

with col5:
    st.metric("MAE", f"{mae:.2f}")

with col6:
    st.metric("RMSE", f"{rmse:.2f}")

# ---------------------------------------------------
# MAP DISPLAY
# ---------------------------------------------------
if st.session_state.map:

    st.subheader("📍 Route Map")

    st_folium(
        st.session_state.map,
        width=700
    )