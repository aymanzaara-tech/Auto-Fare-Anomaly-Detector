import pandas as pd
from sklearn.ensemble import IsolationForest
import folium
from data_generator import generate_data

# Step 1: Generate data
data = generate_data()

# Step 2: Feature engineering
data["fare_per_km"] = data["fare"] / data["distance_km"]

# Step 3: Train model
model = IsolationForest(contamination=0.1, random_state=42)
data["anomaly"] = model.fit_predict(data[["distance_km", "fare", "fare_per_km"]])

# Step 4: Create map
m = folium.Map(location=[12.97, 77.59], zoom_start=12)

for _, row in data.iterrows():
    color = "red" if row["anomaly"] == -1 else "green"
    
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=5,
        color=color,
        fill=True
    ).add_to(m)

# Step 5: Save map
m.save("output_map.html")

print("✅ Map generated: open output_map.html")