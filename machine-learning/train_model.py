import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, InputLayer
import sys
import numpy as np

INPUT_CSV_FILE = "features_laps.csv"
MODEL_OUTPUT_FILE = "redline_model_degradation.h5"

def build_and_train_model():
    print("Training model...")

    try:
        df = pd.read_csv(INPUT_CSV_FILE)
    except FileNotFoundError:
        print(f"Error: file {INPUT_CSV_FILE} not found")
        print("Try running 'features.py'")
        sys.exit(1)

    if df.empty:
        print(f"Error: file {INPUT_CSV_FILE} is null")
        sys.exit(1)

    y = df["lap_duration"]
    x = df[['circuit_short_name', 'compound', 'current_tyre_age']]

    print("Initializing preprocessing pipeline...")
    numeric_features = ['current_tyre_age']
    categorical_features = ['circuit_short_name', 'compound']

    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    x_train_processed = preprocessor.fit_transform(x_train)
    x_test_processed = preprocessor.transform(x_test)

    input_shape = x_train_processed.shape[1]
    print(f"Preprocessing Complete. Feature number: {input_shape}")
    print("Training model...")

    model = Sequential()
    model.add(InputLayer(shape=(input_shape,)))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='linear'))

    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mean_absolute_error'])
    model.summary()

    print("\n Initializing model... Its may take a while...")
    history = model.fit(
        x_train_processed,
        y_train,
        epochs=500,
        batch_size=32,
        validation_data=(x_test_processed, y_test),
        verbose=2
    )

    print("Success. Training complete!")

    loss, mae = model.evaluate(x_test_processed, y_test, verbose=0)
    print(f"\n Classification result")
    print(f"MAE: {mae:.4f}")

    model.save(MODEL_OUTPUT_FILE)
    print(f"Model saved to {MODEL_OUTPUT_FILE}")

if __name__ == "__main__":
    build_and_train_model()
