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

DRIVER_NUMBER_TO_ID_MAP = {
    1: "verstappen",
    11: "perez",
    44: "hamilton",
    63: "russell",
    16: "leclerc",
    55: "sainz",
    4: "norris",
    81: "piastri",
    14: "alonso",
    18: "stroll",
    10: "gasly",
    31: "ocon",
    22: "tsunoda",
    3: "ricciardo",
    77: "bottas",
    24: "zhou",
    23: "albon",
    2: "sargeant",
    27: "hulkenberg",
    20: "magnussen",
    38: "bearman",
    12: "antonelli",
    30: "lawson",
    6: "hadjar",
    5: "bortoleto",
    87: "bearman",
    43: "colapinto"

}

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
    conn_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(conn_string)
except Exception as e:
    logger.error(f"FATAL: Could not connect to database. {e}")
    sys.exit(1)

app = Flask(__name__)
logger.info("Loading features...")

def run_race_simulation(session_key: int, circuit_name: str):
    logger.info(f"[Sim] Starting simulation for Session Key: {session_key} ({circuit_name})")

    try:

        stints_query = text("SELECT * FROM stints WHERE session_key = :key")
        stints_df = pd.read_sql(stints_query, engine, params={"key": session_key})

        qualy_key = session_key - 4
        grid_query = text("SELECT driver_number, position "
                          "FROM session_results "
                          "WHERE session_key = :key AND session_type = 'Qualifying'")
        grid_df = pd.read_sql(grid_query, engine, params={"key": qualy_key})

    except Exception as e:
        logger.error(f"[Sim] ERROR fetching Postgres data: {e}")
        return {"error": "Failed to fetch race setup data from DB."}

    if stints_df.empty or grid_df.empty:
        logger.warning(f"No Stint or Grid data found. Returning empty.")
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
            grid_pos_row = grid_df[grid_df['driver_number'] == driver]
            if grid_pos_row.empty:
                continue

            grid_pos = grid_pos_row['position'].iloc[0]
            skill_factor = (grid_pos * 0.01)
            random_noise = np.random.uniform(-0.15, 0.15)

            final_lap_time = lap_time + skill_factor + random_noise
            race_times[driver] += final_lap_time

    final_results = {k: v for k, v in race_times.items() if v > 0}
    sorted_drivers_num = sorted(final_results, key=final_results.get)

    points_map = { 1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1 }

    final_driver_points_translated = {}
    for i, driver_number in enumerate(sorted_drivers_num):
        position = i + 1
        if position in points_map:
            driver_id_str = DRIVER_NUMBER_TO_ID_MAP.get(driver_number)

            if driver_id_str:
                final_driver_points_translated[driver_id_str] = points_map[position]
            else:
                logger.warning(f"Driver number {driver_number} not found in translation map.")

    logger.info(f"[Sim] Completed. P1 (Driver {sorted_drivers_num[0]}) received 25 points.")
    return final_driver_points_translated

@app.route("/simulate_race_results", methods=["POST"])
def simulate_race():
    try:
        data = request.json
        if not data or 'circuit_name' not in data or 'year' not in data:
            return jsonify({"error": "Missing 'circuit_name' or 'year' in request body"}), 400

        circuit_name_input = data['circuit_name']
        year_input = int(data['year'])

        logger.info(f"Received request for {circuit_name_input} ({year_input}). Finding session_key...")

        query = text("""
                     SELECT session_key
                     FROM sessions
                     WHERE circuit_short_name = :circuit_name
                       AND session_type = 'Race'
                       AND EXTRACT(YEAR FROM date_start) = :year
                     LIMIT 1
                     """)

        params = {"circuit_name": circuit_name_input, "year": year_input}

        with engine.connect() as conn:
            result = conn.execute(query, params).fetchone()

        if not result:
            logger.error(f"No 'Race' session_key found for {circuit_name_input} ({year_input})")
            return jsonify({"error": f"No 'Race' session found for {circuit_name_input} ({year_input})"}), 404

        session_key = result[0]
        logger.info(f"Found session_key: {session_key}. Starting simulation...")

        results = run_race_simulation(session_key, circuit_name_input)

        if "error" in results:
            return jsonify(results), 500

        return jsonify(results)

    except Exception as err:
        logger.error(f"FATAL ERROR during simulation: {err}")
        return jsonify({"error": str(err)}), 500

if __name__ == "__main__":
    app.run(port=5001, debug=False)

