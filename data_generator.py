import pandas as pd
import numpy as np

def generate_data():
    np.random.seed(42)
    n = 200

    data = pd.DataFrame({
        "distance_km": np.random.uniform(1, 15, n),
        "fare": np.random.uniform(30, 300, n),
        "lat": np.random.uniform(12.90, 13.05, n),
        "lon": np.random.uniform(77.50, 77.70, n)
    })

    # Inject anomalies
    for i in range(20):
        data.loc[i, "fare"] *= 2.5

    return data