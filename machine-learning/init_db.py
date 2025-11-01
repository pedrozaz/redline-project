import psycopg2
import sys

# --- (Suas credenciais do DB aqui) ---
DB_NAME = "redline_db"
DB_USER = "admin"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"
# ------------------------------------

def create_database():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.OperationalError as e:
        print(f"ERRO: Não foi possível conectar ao banco de dados '{DB_NAME}'.")
        print("Verifique se o Postgres está rodando.")
        print(f"Erro original: {e}")
        sys.exit(1)

    cursor = conn.cursor()
    print("Conectado ao Postgres. Limpando (DROP) e recriando tabelas...")

    cursor.execute("DROP TABLE IF EXISTS stints CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS pit_stops CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS lap_data CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS weather CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS session_results CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS sessions CASCADE;")


    cursor.execute('''
                   CREATE TABLE sessions (
                     session_key INTEGER PRIMARY KEY,
                     session_name TEXT,
                     session_type TEXT,
                     country_name TEXT,
                     circuit_key INTEGER,
                     circuit_short_name TEXT,
                     date_start TIMESTAMP
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE lap_data (
                     id SERIAL PRIMARY KEY,
                     session_key INTEGER REFERENCES sessions(session_key),
                     lap_number INTEGER,
                     driver_number INTEGER,
                     lap_duration REAL,
                     duration_sector_1 REAL,
                     duration_sector_2 REAL,
                     duration_sector_3 REAL,
                     is_pit_out_lap BOOLEAN
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE pit_stops (
                      id SERIAL PRIMARY KEY,
                      session_key INTEGER REFERENCES sessions(session_key),
                      date TIMESTAMP,
                      driver_number INTEGER,
                      lap_number INTEGER,
                      pit_duration REAL
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE stints (
                       id SERIAL PRIMARY KEY,
                       session_key INTEGER REFERENCES sessions(session_key),
                       driver_number INTEGER,
                       stint_number INTEGER,
                       compound TEXT,
                       lap_start INTEGER,
                       lap_end INTEGER,
                       tyre_age_at_start INTEGER
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE weather (
                        id SERIAL PRIMARY KEY,
                        session_key INTEGER REFERENCES sessions(session_key),
                        date TIMESTAMP,
                        air_temperature REAL,
                        track_temperature REAL,
                        rainfall INTEGER,
                        humidity REAL,
                        pressure REAL,
                        wind_speed REAL,
                        wind_direction INTEGER
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE session_results (
                        id SERIAL PRIMARY KEY,
                        session_key INTEGER REFERENCES sessions(session_key),
                        driver_number INTEGER,
                        position INTEGER,
                        session_type TEXT,
                        dnf BOOLEAN,
                        dns BOOLEAN,
                        dsq BOOLEAN
                   )
                   ''')

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Banco de dados '{DB_NAME}' e tabelas criados com sucesso.")

if __name__ == "__main__":
    create_database()