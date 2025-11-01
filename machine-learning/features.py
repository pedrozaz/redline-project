import pandas as pd
from sqlalchemy import create_engine
import sys

from init_db import DB_NAME
from init_db import DB_USER
from init_db import DB_HOST
from init_db import DB_PORT
from init_db import DB_PASS

OUTPUT_CSV_FILE = "features_laps.csv"

def get_db_engine():
    try:
        conn_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(conn_string)
        engine.connect()
        return engine
    except Exception as e:
        print(f"Error: Unable to connect to database. {e}")
        sys.exit(1)

def engineer_features(engine):
    print("Reading PGSQL data...")
    try:
        query = """
        SELECT
            s.session_key,
            s.circuit_short_name,
            st.driver_number,
            st.compound,
            st.lap_start,
            st.stint_number,
            st.tyre_age_at_start,
            l.lap_number,
            l.lap_duration,
            l.is_pit_out_lap
        FROM 
            lap_data AS l 
        JOIN 
            stints AS st ON l.session_key = st.session_key AND l.driver_number = st.driver_number
            AND l.lap_number >= st.lap_start AND l.lap_number <= st.lap_end
        JOIN 
            sessions AS s ON l.session_key = s.session_key
        """
        df = pd.read_sql_query(query, engine)

        if df.empty:
            print("No data found.")
            return
        print(f"Success. {len(df)} rows read.")

    except Exception as e:
        print(f"Error: Unable to connect to database. {e}")
        return

    print(f"Cleaning data...")
    df_cleaned = df[df['is_pit_out_lap'] == False]

    median_lap_time = df_cleaned['lap_duration'].median()
    cutoff_time = median_lap_time * 1.2

    df_cleaned = df_cleaned[df_cleaned['lap_duration'] < cutoff_time]

    print(f"Cleaned {len(df_cleaned)} rows read.")
    print("Calculating tyre age...")

    df_cleaned['current_tyre_age'] = (
        df_cleaned['lap_number'] - df_cleaned['lap_start']
    ) + df_cleaned['tyre_age_at_start']

    features_df = df_cleaned[[
        'session_key',
        'circuit_short_name',
        'driver_number',
        'compound',
        'current_tyre_age',
        'lap_duration'
    ]]

    features_df.to_csv(OUTPUT_CSV_FILE, index=False)

    print(f"Features saved to {OUTPUT_CSV_FILE}")

if __name__ == "__main__":
    db_engine = get_db_engine()
    engineer_features(db_engine)