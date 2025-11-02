import pandas as pd
import psycopg2
import sys
import os

# --- Database Configuration ---
DB_NAME = os.getenv("DB_NAME", "redline_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
# ------------------------------------

OUTPUT_CSV_FILE = "model_features.csv"
ROLLING_WINDOW_SIZE = 5


def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"ERROR: Could not connect to database '{DB_NAME}'. {e}")
        sys.exit(1)

def engineer_features(conn):

    print(f"Starting feature engineering (Window: {ROLLING_WINDOW_SIZE} races)...")

    query = f"""
    WITH 
    base_races AS (
        SELECT 
            s.session_key,
            s.date_start,
            s.circuit_short_name,
            s.year,
            sr.driver_number,
            sr.position AS finishing_position,
            sr.points AS finishing_points,
            (sr.dnf OR sr.dns OR sr.dsq) AS did_not_finish
        FROM session_results AS sr
        JOIN sessions AS s ON sr.session_key = s.session_key
        WHERE s.session_type = 'Race'
    ),
    
    qualy_results AS (
        SELECT 
            s.session_key AS qualy_session_key,
            s.year,
            s.circuit_short_name,
            sr.driver_number,
            sr.position AS grid_position
        FROM session_results AS sr
        JOIN sessions AS s ON sr.session_key = s.session_key
        WHERE s.session_type = 'Qualifying'
    ),
    
    team_mapping AS (
        SELECT DISTINCT
            d.year,
            d.circuit_short_name,
            d.driver_number,
            t.team_name
        FROM base_races AS d
        JOIN drivers AS t ON d.session_key = t.session_key AND d.driver_number = t.driver_number
    ),
    
    weather_data AS (
        SELECT 
            session_key,
            MAX(CASE WHEN rainfall > 0 THEN 1 ELSE 0 END) AS was_rainy
        FROM weather
        GROUP BY session_key
    ),

    combined_data AS (
        SELECT
            br.session_key,
            br.date_start,
            br.year,
            br.circuit_short_name,
            br.driver_number,
            tm.team_name,
            qr.grid_position,
            COALESCE(wd.was_rainy, 0) AS was_rainy,
            br.finishing_position,
            br.finishing_points,
            br.did_not_finish
        FROM base_races AS br

        LEFT JOIN qualy_results AS qr 
            ON br.year = qr.year 
            AND br.circuit_short_name = qr.circuit_short_name 
            AND br.driver_number = qr.driver_number

        LEFT JOIN team_mapping AS tm
            ON br.year = tm.year 
            AND br.circuit_short_name = tm.circuit_short_name 
            AND br.driver_number = tm.driver_number

        LEFT JOIN weather_data AS wd ON br.session_key = wd.session_key
    ),

    rolling_skill AS (
        SELECT
            *,
            AVG(finishing_points) OVER (
                PARTITION BY driver_number 
                ORDER BY date_start 
                ROWS BETWEEN {ROLLING_WINDOW_SIZE} PRECEDING AND 1 PRECEDING
            ) AS driver_rolling_avg_points,
            
            AVG(CASE WHEN did_not_finish THEN 1.0 ELSE 0.0 END) OVER (
                PARTITION BY driver_number 
                ORDER BY date_start 
                ROWS BETWEEN {ROLLING_WINDOW_SIZE} PRECEDING AND 1 PRECEDING
            ) AS driver_rolling_dnf_rate,

            AVG(finishing_points) OVER (
                PARTITION BY team_name 
                ORDER BY date_start 
                ROWS BETWEEN {ROLLING_WINDOW_SIZE} PRECEDING AND 1 PRECEDING
            ) AS team_rolling_avg_points,

            AVG(finishing_points) OVER (
                PARTITION BY driver_number, circuit_short_name
                ORDER BY date_start
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ) AS driver_circuit_avg_points

        FROM combined_data
    )

    SELECT * FROM rolling_skill
    WHERE grid_position IS NOT NULL
    ORDER BY date_start, driver_number;
    """

    try:
        df = pd.read_sql_query(query, conn)
        print("SQL query executed successfully.")

        df['driver_rolling_avg_points'] = df['driver_rolling_avg_points'].fillna(0)
        df['driver_rolling_dnf_rate'] = df['driver_rolling_dnf_rate'].fillna(0)
        df['team_rolling_avg_points'] = df['team_rolling_avg_points'].fillna(0)

        df['driver_circuit_avg_points'] = df['driver_circuit_avg_points'].fillna(0)

        df.to_csv(OUTPUT_CSV_FILE, index=False)

        print(f"\n--- Feature Engineering Complete ---")
        print(f"Features dataset saved to: {OUTPUT_CSV_FILE}")
        print(f"Total {len(df)} valid race entries (rows) generated.")

    except Exception as e:
        print(f"ERROR executing feature engineering query: {e}")
        sys.exit(1)


if __name__ == "__main__":
    connection = get_db_connection()
    if connection:
        engineer_features(connection)
        connection.close()
        print("Feature engineering process complete.")