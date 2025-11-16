import os

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

from src.model import data_loader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "data")
MODEL_PATH = os.path.join(MODEL_DIR, "model.keras")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
DRIVER_ENCODER_PATH = os.path.join(MODEL_DIR, "driver_encoder.joblib")
CONSTRUCTOR_ENCODER_PATH = os.path.join(MODEL_DIR, "constructor_encoder.joblib")

N_SIMULATIONS = 50000

def load_simulation_tools():
    try:
        model = load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        driver_encoder = joblib.load(DRIVER_ENCODER_PATH)
        constructor_encoder = joblib.load(CONSTRUCTOR_ENCODER_PATH)

        all_data = data_loader.feature_engineer(data_loader.fetch_all_data())
        noise_factor = all_data['points'].std()
        print(f"--- Noise factor (StDev) loaded: {noise_factor:.4f} ---")

        return model, scaler, driver_encoder, constructor_encoder, noise_factor
    except Exception as e:
        print(f"Error loading model or preprocessors: {e}")
        return None, None, None, None, None

def load_historical_data_for_features():
    all_data_raw = data_loader.fetch_all_data()
    all_data_features = data_loader.feature_engineer(all_data_raw)
    return all_data_features

def prepare_simulation_features(df_historical: pd.DataFrame, drivers_db_ids: list, constructors_db_map: dict):
    df_sorted = df_historical.sort_values(by=['race_year', 'race_round'])
    latest_features_base = df_sorted.groupby('driverid').last().reset_index()

    features_needed = ['driverid', 'constructorid']
    latest_features = latest_features_base[features_needed]

    active_drivers_df = pd.DataFrame({'driverid': drivers_db_ids})
    combined_df = pd.merge(active_drivers_df, latest_features, on='driverid', how='left')
    combined_df['constructorid'] = combined_df['driverid'].map(constructors_db_map).fillna(combined_df['constructorid'])

    driver_roll_5 = df_sorted.groupby('driverid')['points'].rolling(window=5, min_periods=1).mean().reset_index()
    driver_roll_5 = driver_roll_5.groupby('driverid').last()['points'].rename('driver_points_roll_5')
    combined_df = combined_df.merge(driver_roll_5, on='driverid', how='left')

    constructor_points = df_sorted.groupby(['race_year', 'race_round', 'constructorid'])['points'].sum().reset_index()
    constructor_roll_5 = constructor_points.groupby('constructorid')['points'].rolling(window=5, min_periods=1).mean().reset_index()
    constructor_roll_5 = constructor_roll_5.groupby('constructorid').last()['points'].rename('constructor_points_roll_5')
    combined_df = combined_df.merge(constructor_roll_5, on='constructorid', how='left')

    q_history = df_sorted.groupby('driverid')['quali_position'].rolling(window=10, min_periods=1)
    q_proxy = q_history.mean().reset_index().groupby('driverid').last()['quali_position'].rename('q_proxy')
    q_stdev = q_history.std().reset_index().groupby('driverid').last()['quali_position'].rename('q_stdev')

    combined_df = combined_df.merge(q_proxy, on='driverid', how='left')
    combined_df = combined_df.merge(q_stdev, on='driverid', how='left')

    dnf_rate = df_sorted.groupby('driverid')['dnf'].mean().rename('dnf_rate')
    combined_df = combined_df.merge(dnf_rate, on='driverid', how='left')

    combined_df['q_proxy'] = combined_df['q_proxy'].fillna(10.0)
    combined_df['q_stdev'] = combined_df['q_stdev'].fillna(3.0)
    combined_df['dnf_rate'] = combined_df['dnf_rate'].fillna(0.05)
    combined_df = combined_df.fillna(0)

    return combined_df.set_index('driverid')

(MODEL, SCALER, DRIVER_ENC, CONSTRUCTOR_ENC, NOISE_FACTOR) = load_simulation_tools()
ALL_DATA_FEATURES = load_historical_data_for_features()
SCALER_FEATURE_NAMES = [
    'grid', 'quali_position',
    'driver_points_roll_5', 'constructor_points_roll_5'
]

def run_full_simulation(current_standings_json, remaining_races_json):

    if MODEL is None or ALL_DATA_FEATURES is None:
        return {"error": "Model or Data not loaded."}

    print(f"--- Starting Vectorized Monte Carlo ({N_SIMULATIONS} runs) ---")

    current_standings_map = {s['driver']['driverId']: s['points'] for s in current_standings_json}
    constructors_map = {s['driver']['driverId']: s['constructor']['constructorId'] for s in current_standings_json}
    driver_ids_ordered = list(current_standings_map.keys())

    remaining_events = []
    for race in remaining_races_json:
        try:
            round_num = int(race['round'])
        except KeyError: continue
        remaining_events.append((round_num, 'R'))
        if race.get('Sprint') is not None:
            remaining_events.append((round_num, 'S'))

    if not remaining_events:
        return {"error": "No remaining events."}

    n_events = len(remaining_events)
    n_drivers = len(driver_ids_ordered)

    base_features_df = prepare_simulation_features(ALL_DATA_FEATURES,
                                                   driver_ids_ordered,
                                                   constructors_map)
    base_features_df = base_features_df.reindex(driver_ids_ordered)

    total_samples = N_SIMULATIONS * n_events * n_drivers

    q_proxy = base_features_df['q_proxy'].values
    q_stdev = base_features_df['q_stdev'].values
    sim_q = np.random.normal(q_proxy, q_stdev, size=(N_SIMULATIONS, n_events, n_drivers))
    sim_q = np.round(np.clip(sim_q, 1, 20))

    driver_roll = base_features_df['driver_points_roll_5'].values
    constructor_roll = base_features_df['constructor_points_roll_5'].values

    num_features_batch = np.zeros((total_samples, 4))
    num_features_batch[:, 0] = sim_q.flatten()
    num_features_batch[:, 1] = sim_q.flatten()
    num_features_batch[:, 2] = np.tile(driver_roll, N_SIMULATIONS * n_events)
    num_features_batch[:, 3] = np.tile(constructor_roll, N_SIMULATIONS * n_events)

    num_df = pd.DataFrame(num_features_batch, columns=SCALER_FEATURE_NAMES)
    scaled_num_batch = SCALER.transform(num_df)

    driver_ids_encoded = DRIVER_ENC.transform(base_features_df.index.values)
    constructor_ids_encoded = CONSTRUCTOR_ENC.transform(base_features_df['constructorid'].values)

    cat_driver_batch = np.tile(driver_ids_encoded, N_SIMULATIONS * n_events)
    cat_constructor_batch = np.tile(constructor_ids_encoded, N_SIMULATIONS * n_events)

    print(f"Predicting {total_samples} samples (20 drivers * {n_events} events * {N_SIMULATIONS} sims)...")
    model_input = [scaled_num_batch, cat_driver_batch, cat_constructor_batch]

    predicted_points_batch = MODEL.predict(model_input, batch_size=4096, verbose=0)
    print("Prediction complete.")

    noise = np.random.normal(0, NOISE_FACTOR, size=predicted_points_batch.shape)
    simulated_points = np.maximum(0, predicted_points_batch + noise)

    dnf_rate = base_features_df['dnf_rate'].values
    dnf_rolls = np.random.rand(N_SIMULATIONS, n_events, n_drivers)
    dnf_chances = np.tile(dnf_rate, (N_SIMULATIONS, n_events, 1))
    is_dnf = (dnf_rolls < dnf_chances).flatten()
    simulated_points[is_dnf] = 0.0

    points_tensor = simulated_points.reshape((N_SIMULATIONS, n_events, n_drivers))
    total_sim_points = points_tensor.sum(axis=1)

    current_points = np.array([current_standings_map[driver_id] for driver_id in driver_ids_ordered])
    final_standings = total_sim_points + current_points

    winner_indices = np.argmax(final_standings, axis=1)
    unique_indices, counts = np.unique(winner_indices, return_counts=True)

    print("--- Simulation Complete ---")

    results = {}
    for idx, wins in zip(unique_indices, counts):
        driver_db_id = driver_ids_ordered[idx]
        probability = (wins / N_SIMULATIONS) * 100.0
        results[driver_db_id] = probability

    return results