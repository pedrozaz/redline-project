import sys
import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from sqlalchemy import create_engine, text
import logging

from init_db import DB_USER
from init_db import DB_HOST
from init_db import DB_NAME
from init_db import DB_PASS
from init_db import DB_PORT

MODEL_FILE = "redline_model_degradation.h5"
PREPROCESSOR_FILE = "redline_preprocessor.joblib"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing redline machine learning api....")
try:
    logger.info(f"Loading model from {MODEL_FILE}...")
    model = load_model(MODEL_FILE)

    logger.info(f"Loading preprocessor from {PREPROCESSOR_FILE}...")
    preprocessor = joblib.load(PREPROCESSOR_FILE)

except IOError:
    logger.error(f"FATAL: Could not load model files.")
    logger.error(f"Run train_model.py first.")
    sys.exit(1)

try:
    logger.info("Connecting to database...")
    conn_string = f"postgres://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(conn_string)
except Exception as e:
    logger.error(f"FATAL: Could not connect to database. {e}")
    sys.exit(1)

app = Flask(__name__)
logger.info("Loading features...")

def run_race_simulation(session_key: int):
    logger.info(f"[SIM] Starting simulation for session {session_key}")

    try:
        circuit_query = text("""
                             SELECT circuit_short_name 
                             FROM sessions
                             WHERE session_key = :key AND session_type = 'Race' """)
        circuit_df = pd.read_sql_query(circuit_query, engine, params={'key': session_key})
        if circuit_df.empty:
            raise Exception(f"No circuits for session {session_key}")
        circuit_name = circuit_df.iloc[0]['circuit_short_name']

        stints_query = text("""
        SELECT * FROM stints WHERE session_key = :key
        """)
        stints_df = pd.read_sql_query(stints_query, engine, params={'key': session_key})

        qualy_key = session_key - 4
        grid_query = text("""
        SELECT driver_number, position FROM session_results 
        WHERE session_key = :key AND session_type = 'Quality' """)
        grid_df = pd.read_sql_query(grid_query, engine, params={'key': qualy_key})

        logger.info(f"[SIM] Data for {circuit_name} loaded.")
    except Exception as e:
        logger.error(f"FATAL: Could not load data for session {session_key}. {e}")
        return {"error": "Failed to fetch race setup data from database"}

    if stints_df.empty:
        logger.warning(f"No stints for session {session_key}")
        return {}
    if grid_df.empty:
        logger.warning(f"No stints for session {session_key}")
        return {}

    total_laps = int(stints_df['lap_end'].quantile(0.95))
    drivers = grid_df['driver_number'].unique()

    race_times = {driver: 0.0 for driver in drivers}

    for lap in range(1, total_laps + 1):
        lap_inputs = []
        drivers_in_lap = []

        for driver in drivers:
            current_stint = stints_df[
                (stints_df['driver_number'] == driver) &
                (stints_df['lap_start'] <= lap) &
                (stints_df['lap_end'] >= lap)
            ]

            if current_stint.empty:
                continue

            stint = current_stint.iloc[0]
            tyre_age = (lap - stint['lap_start']) + stint['tyre_age_at_start']
            lap_inputs.append({
                "circuit_short_name": circuit_name,
                "compound": stint['compound'],
                "current_tyre_age": tyre_age
            })
            drivers_in_lap.append(driver)

        if not lap_inputs:
            continue

        input_df = pd.DataFrame(lap_inputs)
        input_processed = preprocessor.transform(input_df)
        predicted_durations = model.predict(input_processed, verbose=0)

        for i, driver in enumerate(drivers_in_lap):
            lap_time = predicted_durations[i][0]
            grid_pos = grid_df[grid_df['driver_number'] == driver]['position'].iloc[0]
            skill_factor = (grid_pos * 0.01)
            random_noise = np.random.uniform(-0.15, 0.15)

            final_lap_time = lap_time + skill_factor + random_noise
            race_times[driver] += final_lap_time

        final_results = {k: v for k, v in race_times.items() if v > 0}
        sorted_drivers = sorted(final_results, key=final_results.get)

        points_map = {
            1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
        }
    final_driver_points = {}
    for i, driver_number in enumerate(sorted_drivers):
        position = i + 1
        if position in points_map:
            final_driver_points[int(driver_number)] = points_map[position]

    logger.info(f"[SIM] Completed. P1 ({sorted_drivers[0]}) received 25 points.")
    return final_driver_points

@app.route("/simulate_race_results", methods=["POST"])
def simulate_race():
    try:
        data = request.json
        if not data or 'session_key' not in data:
            return jsonify({"error": "No session key provided"}), 400
        session_key = int(data['session_key'])
        results = run_race_simulation(session_key)

        if "error" in results:
            return jsonify(results), 500

        return jsonify(results), 200

    except Exception as err:
        logger.error(f"FATAL during simulation {err}")
        return jsonify({"error": str(err)}), 500


if __name__ == "__main__":
    app.run(port=5001, debug=False)


