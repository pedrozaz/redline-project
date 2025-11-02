import httpx
import psycopg2
import sys
import os
from typing import Dict, Any, List

# --- Configuration ---
DB_NAME = os.getenv("DB_NAME", "redline_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
# ------------------------------------

POINTS_MAP_RACE = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

POINTS_MAP_SPRINT = {
    1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1
}

BASE_API_URL = "https://api.openf1.org/v1"


def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        conn.autocommit = True
        return conn
    except psycopg2.OperationalError as e:
        print(f"ERROR: Could not connect to database '{DB_NAME}'. {e}")
        sys.exit(1)

def fetch_api_data(endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        with httpx.Client() as client:
            response = client.get(f"{BASE_API_URL}/{endpoint}", params=params, timeout=30.0)
            response.raise_for_status() 
            data = response.json()
            if not isinstance(data, list):
                print(f"WARNING: API did not return a list for endpoint '{endpoint}'.")
                return []
            return data
    except httpx.HTTPStatusError as e:
        print(f"HTTP ERROR {e.response.status_code} while fetching {e.request.url!r}: {e}")
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during API fetch: {e}")
    return []

def get_points(session_type: str, position: int) -> int:
    if position is None:
        return 0

    pos = int(position)

    if session_type == 'Race':
        return POINTS_MAP_RACE.get(pos, 0)
    elif session_type == 'Sprint':
        return POINTS_MAP_SPRINT.get(pos, 0)

    return 0

def ingest_sessions(conn, year: int):
    print(f"Fetching SESSIONS for {year}...")
    cursor = conn.cursor()

    sessions_data = fetch_api_data("sessions", {"year": year})
    if not sessions_data:
        print(f"No session data found for {year}.")
        return []

    inserted_sessions = []
    for s in sessions_data:
        if s.get('session_type') in ('Race', 'Qualifying', 'Sprint'):
            try:
                cursor.execute(
                    """
                    INSERT INTO sessions (session_key, session_name, session_type, country_name, circuit_key, circuit_short_name, date_start, year)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_key) DO NOTHING;
                    """,
                    (
                        s['session_key'], s.get('session_name'), s.get('session_type'),
                        s.get('country_name'), s.get('circuit_key'), s.get('circuit_short_name'),
                        s.get('date_start'), s.get('year')
                    )
                )
                inserted_sessions.append(s['session_key'])
            except Exception as e:
                print(f"Error inserting session {s.get('session_key')}: {e}")

    print(f"Ingested {len(inserted_sessions)} sessions (Race/Qualy/Sprint).")
    cursor.close()
    return inserted_sessions

def ingest_related_data(conn, session_keys: List[int]):

    if not session_keys:
        print("No session keys provided. Skipping related data ingestion.")
        return

    print(f"Fetching related data for {len(session_keys)} sessions...")
    cursor = conn.cursor()

    api_params = {"session_key": session_keys}

    print("Fetching SESSION_RESULTS...")
    results_data = fetch_api_data("session_result", api_params)
    print(f"  > Received {len(results_data)} session_result records.") # DEBUG

    for r in results_data:
        try:
            points = get_points(r.get('session_type'), r.get('position'))

            cursor.execute(
                """
                INSERT INTO session_results (session_key, driver_number, position, points, session_type, dnf, dns, dsq)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    r['session_key'], r.get('driver_number'), r.get('position'),
                    points,
                    r.get('session_type'), r.get('dnf'), r.get('dns'), r.get('dsq')
                )
            )
        except Exception as e:
            print(f"Error inserting session result for driver {r.get('driver_number')}: {e}")

    print("Fetching DRIVERS...")
    drivers_data = fetch_api_data("drivers", api_params)
    print(f"  > Received {len(drivers_data)} driver records.") # DEBUG

    for d in drivers_data:
        try:
            cursor.execute(
                """
                INSERT INTO drivers (driver_number, session_key, meeting_key, broadcast_name, full_name, team_name, team_colour, country_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (driver_number, session_key) DO NOTHING;
                """,
                (
                    d['driver_number'], d['session_key'], d.get('meeting_key'),
                    d.get('broadcast_name'), d.get('full_name'), d.get('team_name'),
                    d.get('team_colour'), d.get('country_code')
                )
            )
        except Exception as e:
            print(f"Error inserting driver {d.get('driver_number')}: {e}")

    print("Fetching WEATHER...")
    weather_data = fetch_api_data("weather", api_params)
    print(f"  > Received {len(weather_data)} weather records.") # DEBUG

    for w in weather_data:
        try:
            cursor.execute(
                """
                INSERT INTO weather (session_key, date, air_temperature, track_temperature, rainfall, humidity, pressure, wind_speed, wind_direction)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    w['session_key'], w.get('date'), w.get('air_temperature'),
                    w.get('track_temperature'), w.get('rainfall'), w.get('humidity'),
                    w.get('pressure'), w.get('wind_speed'), w.get('wind_direction')
                )
            )
        except Exception as e:
            print(f"Error inserting weather data: {e}")

    print("Related data ingestion complete.")
    cursor.close()

def main():
    # --- Configuration ---
    YEARS_TO_FETCH = [2023, 2024, 2025]
    # ---------------------

    connection = get_db_connection()
    if not connection:
        sys.exit(1)

    print(f"Starting OpenF1 data scraping for years: {YEARS_TO_FETCH}")

    for year in YEARS_TO_FETCH:
        print(f"\n--- Processing Year: {year} ---")

        session_keys = ingest_sessions(connection, year)

        if session_keys:
            ingest_related_data(connection, session_keys)
        else:
            print(f"No sessions found to process for {year}.")

    connection.close()
    print("\n--- Scraping process finished successfully. ---")

if __name__ == "__main__":
    main()