import sys
from datetime import datetime

import fastf1 as ff1
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection

from init_db import DB_HOST
from init_db import DB_NAME
from init_db import DB_PASS
from init_db import DB_PORT
from init_db import DB_USER

START_YEAR = 2018
END_YEAR = datetime.now().year
CACHE_PATH = 'ff1_cache'

print(f"Initializing FastF1... Cache directory: {CACHE_PATH}")
ff1.Cache.enable_cache(CACHE_PATH)

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

def upsert_circuits(cur, circuit_id, name, location, country):
    query = sql.SQL("""
                    INSERT INTO circuits (circuitId, name, location, country)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (circuitId) DO NOTHING;
                    """)
    cur.execute(query, (circuit_id, name, location, country))

def upsert_drivers(cur, driver_id, code, given_name, family_name, nationality):
    query = sql.SQL("""
                    INSERT INTO drivers (driverId, code, givenName, familyName, nationality)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (driverId) DO NOTHING;
                    """)
    cur.execute(query, (driver_id, code, given_name, family_name, nationality))

def upsert_constructors(cur, constructor_id, name, nationality):
    query = sql.SQL("""
                    INSERT INTO constructors (constructorId, name, nationality)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (constructorId) DO NOTHING;
                    """)
    cur.execute(query, (constructor_id, name, nationality))

def insert_race(cur, year, round_num, circuit_id, name, date):
    query = sql.SQL("""
                    INSERT INTO races (year, round, circuitId, name, date)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (year, round) DO NOTHING;
                    """)
    cur.execute(query, (year, round_num, circuit_id, name, date))

def insert_results(cur, results_df, year, round_num, session_type):
    query = sql.SQL("""
                    INSERT INTO results (
                        race_year, race_round, session_type, driverId, constructorId,
                        grid, position, points, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (race_year, race_round, session_type, driverId) DO NOTHING;
                    """)

    for row in results_df.itertuples():
        cur.execute(query, (
            year,
            round_num,
            session_type,
            row.DriverId,
            row.ConstructorId,
            int(row.GridPosition),
            int(row.Position),
            float(row.Points),
            row.Status
        ))

def insert_qualifying(cur, results_df, year, round_num, session_type):
    query = sql.SQL("""
                    INSERT INTO qualifying (
                        race_year, race_round, session_type, driverId, constructorId,
                        position, q1, q2, q3
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (race_year, race_round, session_type, driverId) DO NOTHING;
                    """)

    for row in results_df.itertuples():
        def format_time(time_val):
            if pd.isna(time_val) or not isinstance(time_val, pd.Timedelta):
                return None
            return str(time_val.to_pytimedelta())

        cur.execute(query, (
            year,
            round_num,
            session_type,
            row.DriverId,
            row.ConstructorId,
            int(row.Position),
            format_time(row.Q1),
            format_time(row.Q2),
            format_time(row.Q3)
        ))

def pre_populate_and_patch_df(cur, session, results_df):
    if results_df is None or results_df.empty:
        return None

    if 'ConstructorId' in results_df.columns:
        print("  > Processing modern data format (2018+).")
        for num in results_df['DriverNumber'].unique():
            if pd.isna(num): continue
            try:
                driver_info = session.get_driver(num)
                upsert_drivers(cur, driver_info['DriverId'], driver_info['Abbreviation'],
                               driver_info['GivenName'], driver_info['FamilyName'],
                               driver_info['Nationality'])
            except Exception as e:
                print(f"  > Warning (New Data): Could not upsert driver {num}. Error: {e}")

        for con_id in results_df['ConstructorId'].unique():
            if pd.isna(con_id): continue
            try:
                con_info = session.get_constructor(con_id)
                upsert_constructors(cur, con_info['ConstructorId'], con_info['Name'],
                                    con_info['Nationality'])
            except Exception as e:
                print(f"  > Warning (New Data): Could not upsert constructor {con_id}. Error: {e}")

        return results_df

    else:
        print("  > Patching historical data (Pre-2018)...")

        if 'DriverNumber' in results_df.columns:
            results_df['DriverId'] = results_df['DriverNumber'].astype(str)
            for driver_id in results_df['DriverId'].unique():
                if pd.isna(driver_id): continue
                upsert_drivers(cur, driver_id=driver_id, code=driver_id,
                               given_name=f"Driver_{driver_id}", family_name="", nationality="")

        team_col = 'TeamName' if 'TeamName' in results_df.columns else 'ConstructorName'
        if team_col in results_df.columns:
            results_df['ConstructorId'] = results_df[team_col]
            for con_id in results_df['ConstructorId'].unique():
                if pd.isna(con_id): continue
                upsert_constructors(cur, constructor_id=con_id, name=con_id, nationality="")

        if 'DriverId' not in results_df.columns or 'ConstructorId' not in results_df.columns:
            print("  > CRITICAL: Could not patch DataFrame. Missing Driver/Constructor columns.")
            return None

        return results_df


def populate_database():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print("Database connection successful. Starting population...")

                for year in range(START_YEAR, END_YEAR + 1):
                    print(f"\n--- Processing Year: {year} ---")

                    try:
                        schedule = ff1.get_event_schedule(year)
                    except Exception as e:
                        print(f"Could not fetch schedule for {year}. Error: {e}")
                        continue

                    for index, event in schedule.iterrows():
                        if event['EventDate'].to_pydatetime() > datetime.now():
                            print(f"Skipping Round {event['RoundNumber']} ({event['EventName']}) - Event in future.")
                            break

                        round_num = int(event['RoundNumber'])

                        if round_num == 0:
                            print(f"Skipping event: {event['EventName']} (Round 0)")
                            continue

                        event_name = event['EventName']
                        print(f"Processing: {year} Round {round_num} - {event_name}")

                        try:
                            session_race = ff1.get_session(year, round_num, 'R')

                            try:
                                circuit_data = session_race.event['Circuit']
                                circuit_id = circuit_data['circuitId']
                                circuit_name = circuit_data['Location']['locality']
                                circuit_loc = circuit_data['Location']['country']
                                circuit_country = circuit_data['Location']['country']
                            except KeyError:
                                print(f"  > Using fallback circuit data for {year}")
                                circuit_id = event['Location'].lower().replace(" ", "_").replace("-", "_")
                                circuit_name = event['Location']
                                circuit_loc = event['Location']
                                circuit_country = event['Country']
                            except Exception as e:
                                print(f"  > CRITICAL: Unhandled error getting circuit info. Skipping. Error: {e}")
                                continue

                            upsert_circuits(cur, circuit_id, circuit_name, circuit_loc, circuit_country)

                            session_race.load(telemetry=False, weather=False, messages=False)
                            insert_race(cur, year, round_num, circuit_id, event_name, session_race.date)

                            race_results_df = pre_populate_and_patch_df(cur, session_race, session_race.results)

                            if race_results_df is not None and not race_results_df.empty:
                                insert_results(cur, race_results_df, year, round_num, 'R')
                            else:
                                print(f"  > No Race results found for {year} R{round_num}.")

                            try:
                                session_quali = ff1.get_session(year, round_num, 'Q')
                                session_quali.load(telemetry=False, weather=False, messages=False)

                                quali_results_df = pre_populate_and_patch_df(cur, session_quali, session_quali.results)

                                if quali_results_df is not None and not quali_results_df.empty:
                                    insert_qualifying(cur, quali_results_df, year, round_num, 'Q')
                                else:
                                    print(f"  > No Qualifying results found for {year} R{round_num}.")
                            except Exception as e:
                                print(f"  > Error loading Qualifying data for {year} R{round_num}: {e}")

                            sprint_check = (str(event.get('Session1', '')) == 'Sprint'
                                            or str(event.get('Session2', '')) == 'Sprint'
                                            or str(event.get('Session3', '')) == 'Sprint'
                                            or str(event.get('Session4', '')) == 'Sprint'
                                            or str(event.get('Session5', '')) == 'Sprint')

                            if year >= 2021 and sprint_check:
                                print(f"  > Sprint weekend detected.")
                                try:
                                    session_sprint = ff1.get_session(year, round_num, 'S')
                                    session_sprint.load(telemetry=False, weather=False, messages=False)

                                    sprint_results_df = pre_populate_and_patch_df(cur, session_sprint, session_sprint.results)

                                    if sprint_results_df is not None and not sprint_results_df.empty:
                                        insert_results(cur, sprint_results_df, year, round_num, 'S')
                                    else:
                                        print(f"  > No Sprint results found for {year} R{round_num}.")
                                except Exception as e:
                                    print(f"  > Error loading Sprint data for {year} R{round_num}: {e}")

                                try:
                                    sq_session_name = 'SQ' if year < 2023 else 'Sprint Shootout'
                                    session_sq = ff1.get_session(year, round_num, sq_session_name)
                                    session_sq.load(telemetry=False, weather=False, messages=False)

                                    sq_results_df = pre_populate_and_patch_df(cur, session_sq, session_sq.results)

                                    if sq_results_df is not None and not sq_results_df.empty:
                                        insert_qualifying(cur, sq_results_df, year, round_num, 'SQ')
                                    else:
                                        print(f"  > No Sprint Qualifying results found for {year} R{round_num}.")
                                except Exception as e:
                                    print(f"  > Error loading Sprint Qualifying data for {year} R{round_num}: {e}")


                            conn.commit()
                            print(f"  > Successfully committed {year} R{round_num}.")

                        except Exception as e:
                            print(f"Error processing {year} Round {round_num}: {e}")
                            print("Rolling back transaction for this event.")
                            conn.rollback()

                print("\n--- Population complete. ---")

    except (Exception, psycopg2.DatabaseError) as e:
        print(f"\n--- FATAL ERROR ---")
        print(f"A critical error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    populate_database()