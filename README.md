# Redline: F1 Championship Predictor

Redline is a hybrid web application that predicts the final Formula 1 World Drivers' Championship (WDC) standings. It uses a Java/Spring Boot backend to serve data and a Python/TensorFlow microservice to run a high-speed, vectorized Monte Carlo simulation.

The system calculates the win probability for each driver by simulating the remaining races of the season thousands of times and counting the outcomes.

## How It Works: System Architecture

The project is split into two main services that communicate via a REST API:

**1. Java (Spring Boot) Backend:** The main application server.

**2. Python (Flask) ML Service:** A dedicated microservice that handles all complex calculations.

### **1. The Java Backend (The "Conductor")**

   The Java service is responsible for handling user requests and orchestrating the simulation.

1. A user request hits the `ChampionshipController`.

2. The ChampionshipSimulatorService is called.

3. This service uses the `F1ClientService` (which uses the Jolpica API) to fetch the current, live state of the championship:

   - The list of DriverStanding (current points).

   - The list of Race objects remaining on the calendar.

4. A DriverIdMapper utility class translates the data from Jolpica IDs (e.g., "max_verstappen", "mercedes") to the internal Database IDs (e.g., "1", "Red Bull") that the ML model was trained on.

5. The SimulationClient makes a single POST request to the Python API (http://localhost:5000/simulate), sending the translated standings and remaining races.

6. The Python service runs the full simulation and returns a final JSON map of probabilities (e.g., `{"1": 12.5, "44": 80.2, ...}`).

7. The Java service receives this response, uses the DriverIdMapper again to translate the results back into full driver names, and serves the final probabilities to the frontend.

### **2. The Python ML Service (The "Engine")**

   This service is responsible for all heavy lifting. It is built with Flask, NumPy, and TensorFlow.

1. **On Startup:** The Flask `app.py` loads the trained TensorFlow model (.keras) and the Scikit-learn preprocessors (`.joblib`) into memory one time.

2. **API Endpoint:** It exposes a single endpoint (`/simulate`).

3. **Simulation:** When called, it does not run a for loop. It performs a fully vectorized, NumPy-based simulation to achieve high speed.

4. **Response:** It returns the final probability map to the Java service.

## The Data & Model

#### **Offline Data Pipeline**

The model's training data is stored in a PostgreSQL database, which was populated by a separate Python pipeline:

- **init_db.py:** Creates the database schema.

- **ingest_data.py:** Uses the FastF1 Python library (not Jolpica) to fetch and backfill historical race data from 2018 to the present.

- **ID Mismatch:** Because the FastF1 API (for older data) and the Jolpica API (for live data) use different ID formats, the `ingest_data.py` script uses placeholder IDs (like DriverNumber "44" and TeamName "Mercedes") as the database keys. This is why the DriverIdMapper in the Java service is critical.


#### The Prediction Model

The core of the system is a Keras/TensorFlow neural network, trained in `model_trainer.py`.

- **Goal:** The model does not predict a "winner". It predicts the specific number of points a single driver will score in a single event.

- **Features:** The model uses the following inputs to make a prediction:

  - **Categorical (Embeddings):** `driverId`, `constructorId`.

  - **Numerical (Scaled):**

    - `quali_position` (The simulated qualifying position).

    - `driver_points_roll_5` (The driver's recent "form").

    - `constructor_points_roll_5` (The team's recent "form").

## The Simulation Logic

The simulation (`simulate_championship.py`) is the most complex part of the system. It runs 50,000+ "universes" simultaneously without looping, using NumPy's vectorization.

1. **Load Base Features:** It loads the "base features" for all 20 drivers from the historical database (e.g., their average quali position (`q_proxy`), their quali consistency (`q_stdev`), their DNF rate (`dnf_rate`), and their recent point averages).

2. **Create Random Inputs:** It creates three massive NumPy arrays, one for each "random" element of a race:

- **Qualifying:** It generates `N_SIMULATIONS * N_EVENTS` random qualifying positions for each driver, based on their `q_proxy` and `q_stdev`.

- **DNF Risk:** It "rolls a die" (`np.random.rand()`) for every driver in every simulated event.

- **Race Day Noise:** It generates a random "luck" factor (from a normal distribution) for every driver in every event.

3. **Build Batch:** It combines these random inputs with the static features (like driver_points_roll_5) into a single, massive batch array (`(N_SIMS * N_EVENTS * N_DRIVERS, 4)`).

4. **Predict (One Call):** It calls `model.predict()` one time on this giant batch. This is the step that uses the GPU (if available) and provides the speed.

5. **Apply Randomness:**

- The "Race Day Noise" is added to the model's prediction.

- If a driver's "DNF Roll" was lower than their `dnf_rate`, their predicted points for that event are set to 0.

6. **Calculate Winners:** The script reshapes the final points array, adds the driver's current points, and uses `np.argmax()` to find the winner of each of the 50,000 simulated seasons. The counts are then returned as percentages.



USAGE EXAMPLE VIDEO: https://youtu.be/eLeIsGyF1dI
