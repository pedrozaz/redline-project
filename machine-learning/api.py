import sys
import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model

MODEL_FILE = "redline_model_degradation.h5"
PREPROCESSOR_FILE = "redline_preprocessor.joblib"

print("Initializing API...")

try:
    print(f"Loading model {MODEL_FILE} ...")
    model = load_model(MODEL_FILE)

    print(f"Loading preprocessor {PREPROCESSOR_FILE} ...")
    preprocessor = joblib.load(PREPROCESSOR_FILE)

except IOError:
    print(f"Error loading model files")
    sys.exit(1)

app = Flask(__name__)
print("Flask server and model loaded...")

@app.route("/predict_lap_duration", methods=["POST"])
def predict():
    try:
        input_data = request.json

        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        input_df = pd.DataFrame(input_data)
        input_processed = preprocessor.transform(input_df)
        prediction = model.predict(input_processed)
        output_data = [item[0] for item in prediction.tolist()]

        return jsonify({"predicted_laps_durations": output_data})

    except Exception as e:
        print(f"Error while predicting lap durations: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001, debug=True)
