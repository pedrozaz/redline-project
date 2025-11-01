import json
import sys
import time

import pandas as pd
import requests
from sqlalchemy import create_engine

# --- CONFIGURAÇÃO ---
YEAR_TO_SCRAPE = 2024
BASE_API_URL = "https://api.openf1.org/v1"

# Dados de conexão (os mesmos do init_db.py)
DB_NAME = "redline_db"
DB_USER = "admin"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"
# --------------------

def get_db_engine():
    try:
        conn_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(conn_string)
        engine.connect()
        return engine
    except Exception as e:
        print(f"ERRO: Não foi possível criar a engine do SQLAlchemy. {e}")
        sys.exit(1)

def fetch_data(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return data
    except requests.exceptions.RequestException as e:
        print(f"ERRO ao buscar dados de: {url} | Erro: {e}")
        return None
    except json.JSONDecodeError:
        print(f"ERRO: Resposta inválida (não-JSON) de: {url}")
        return None

def scrape_data(engine):
    print(f"Iniciando o garimpo de dados para a temporada de {YEAR_TO_SCRAPE}...")

    print("Buscando sessões de corrida...")
    sessions_url = f"{BASE_API_URL}/sessions?year={YEAR_TO_SCRAPE}&session_type=Race"
    sessions_data = fetch_data(sessions_url)

    if not sessions_data:
        print("Falha ao buscar sessões. Abortando.")
        return

    sessions_df = pd.DataFrame(sessions_data)
    sessions_df = sessions_df[[
        'session_key', 'session_name', 'country_name',
        'circuit_key', 'circuit_short_name', 'date_start'
    ]]

    sessions_df.to_sql('sessions', engine, if_exists='append', index=False)
    print(f"Sucesso. {len(sessions_df)} sessões salvas.")

    session_keys = sessions_df['session_key'].tolist()

    for i, key in enumerate(session_keys):
        session_name = sessions_df[sessions_df['session_key'] == key]['session_name'].values[0]
        print(f"\n--- Processando Sessão {i+1}/{len(session_keys)}: {session_name} (Key: {key}) ---")

        print("Buscando dados de voltas (laps)...")
        laps_data = fetch_data(f"{BASE_API_URL}/laps?session_key={key}")
        if laps_data:
            laps_df = pd.DataFrame(laps_data)
            laps_df = laps_df[[
                'session_key', 'lap_number', 'driver_number', 'lap_duration',
                'duration_sector_1', 'duration_sector_2', 'duration_sector_3',
                'is_pit_out_lap'
            ]]
            laps_df.to_sql('lap_data', engine, if_exists='append', index=False, chunksize=1000)
            print(f"Sucesso. {len(laps_df)} registros de voltas salvos.")
        else:
            print(f"Nenhum dado de volta para a sessão {key}.")


        print("Buscando dados de pit stops...")
        pits_data = fetch_data(f"{BASE_API_URL}/pit?session_key={key}")
        if pits_data:
            pits_df = pd.DataFrame(pits_data)
            pits_df = pits_df[[
                'session_key', 'date', 'driver_number', 'lap_number', 'pit_duration'
            ]]
            pits_df.to_sql('pit_stops', engine, if_exists='append', index=False)
            print(f"Sucesso. {len(pits_df)} registros de pit stop salvos.")
        else:
            print(f"Nenhum pit stop para a sessão {key}.")


        print("Buscando dados de stints...")
        stints_data = fetch_data(f"{BASE_API_URL}/stints?session_key={key}")
        if stints_data:
            stints_df = pd.DataFrame(stints_data)
            stints_df = stints_df[[
                'session_key', 'driver_number', 'stint_number', 'compound',
                'lap_start', 'lap_end', 'tyre_age_at_start'
            ]]
            stints_df.to_sql('stints', engine, if_exists='append', index=False)
            print(f"Sucesso. {len(stints_df)} registros de stint salvos.")
        else:
            print(f"Nenhum dado de stint para a sessão {key}.")

        print("Buscando dados do grid de largada...")
        grid_data = fetch_data(f"{BASE_API_URL}/starting_grid?session_key={key}")
        if grid_data:
            grid_df = pd.DataFrame(grid_data)
            grid_df = grid_df[[
                'session_key', 'driver_number', 'position', 'lap_duration'
            ]]
            grid_df.to_sql('starting_grid', engine, if_exists='append', index=False)
            print(f"Sucesso. {len(grid_df)} registros de grid salvos.")
        else:
            print(f"Nenhum dado de grid para a sessão {key}.")


        print("Buscando dados de clima...")
        weather_data = fetch_data(f"{BASE_API_URL}/weather?session_key={key}")
        if weather_data:
            weather_df = pd.DataFrame(weather_data)
            weather_df = weather_df[[
                'session_key', 'date', 'air_temperature', 'track_temperature',
                'rainfall', 'humidity', 'pressure', 'wind_speed', 'wind_direction'
            ]]
            weather_df.to_sql('weather', engine, if_exists='append', index=False, chunksize=1000)
            print(f"Sucesso. {len(weather_df)} registros de clima salvos.")
        else:
            print(f"Nenhum dado de clima para a sessão {key}.")

        print("Buscando resultados da sessão...")
        results_data = fetch_data(f"{BASE_API_URL}/session_result?session_key={key}")
        if results_data:
            results_df = pd.DataFrame(results_data)
            results_df = results_df[[
                'session_key', 'driver_number', 'position', 'dnf', 'dns', 'dsq'
            ]]
            results_df.to_sql('session_results', engine, if_exists='append', index=False)
            print(f"Sucesso. {len(results_df)} registros de resultado salvos.")
        else:
            print(f"Nenhum dado de resultado para a sessão {key}.")

        print("Aguardando 1s para respeitar a API...")
        time.sleep(5)

    print("\n--- GARIMPO DE DADOS CONCLUÍDO ---")

if __name__ == "__main__":
    db_engine = get_db_engine()

    scrape_data(db_engine)