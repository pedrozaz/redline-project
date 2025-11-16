import psycopg2
import os
import sys
import pandas as pd
from psycopg2.extensions import connection

from database.init_db import DB_USER
from database.init_db import DB_PORT
from database.init_db import DB_PASS
from database.init_db import DB_HOST
from database.init_db import DB_NAME

def get_db_connection() -> connection:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to database '{DB_NAME}' as user '{DB_USER}'.")
        print(f"Details: {e}")
        sys.exit(1)

def fetch_all_data() -> pd.DataFrame:

    results_query = """
                    SELECT
                        race_year,
                        race_round,
                        session_type,
                        driverId,
                        constructorId,
                        grid,
                        position,
                        points,
                        status
                    FROM results; \
                    """

    quali_query = """
                  SELECT
                      race_year,
                      race_round,
                      session_type AS quali_session_type,
                      driverId,
                      position AS quali_position
                  FROM qualifying; \
                  """

    try:
        with get_db_connection() as conn:
            print("Fetching results data...")
            results_df = pd.read_sql_query(results_query, conn)

            print("Fetching qualifying data...")
            quali_df = pd.read_sql_query(quali_query, conn)

        print("Data fetched successfully. Merging dataframes...")

        q_to_r = quali_df[quali_df['quali_session_type'] == 'Q'].copy()
        q_to_r['session_type'] = 'R'

        sq_to_s = quali_df[quali_df['quali_session_type'].isin(['SQ', 'Sprint Shootout'])].copy()
        sq_to_s['session_type'] = 'S'

        combined_quali_df = pd.concat([q_to_r, sq_to_s])
        combined_quali_df = combined_quali_df.drop(columns=['quali_session_type'])

        merged_df = pd.merge(
            results_df,
            combined_quali_df,
            on=['race_year', 'race_round', 'session_type', 'driverid'],
            how='left'
        )

        return merged_df

    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def feature_engineer(df: pd.DataFrame) -> pd.DataFrame:

    print("Starting feature engineering...")

    df = df.sort_values(by=['race_year', 'race_round'])

    df['driver_points_roll_5'] = df.groupby('driverid')['points'].shift(1).rolling(window=5, min_periods=1).mean().fillna(0)

    constructor_points = df.groupby(['race_year', 'race_round', 'constructorid'])['points'].sum().reset_index()
    constructor_points['constructor_points_roll_5'] = constructor_points.groupby('constructorid')['points'].shift(1).rolling(window=5, min_periods=1).mean().fillna(0)

    df = pd.merge(
        df,
        constructor_points[['race_year', 'race_round', 'constructorid', 'constructor_points_roll_5']],
        on=['race_year', 'race_round', 'constructorid'],
        how='left'
    )

    df['dnf'] = (df['status'] != 'Finished').astype(int)

    df['quali_position'] = df['quali_position'].fillna(df['grid'])

    print("Feature engineering complete.")
    return df


if __name__ == "__main__":
    raw_data = fetch_all_data()

    if not raw_data.empty:
        print(f"Successfully loaded {len(raw_data)} results.")

        processed_data = feature_engineer(raw_data)

        print("\n--- Processed Data Sample (Head) ---")
        print(processed_data.head())

        print("\n--- Columns ---")
        print(processed_data.columns)