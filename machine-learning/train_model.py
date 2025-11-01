import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, InputLayer, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import sys
import numpy as np
import joblib

INPUT_CSV_FILE = "features_laps.csv"
MODEL_OUTPUT_FILE = "redline_model_degradation.h5"

def build_and_train_model():
    print("Training...")

    try:
        df = pd.read_csv(INPUT_CSV_FILE)
    except FileNotFoundError:
        print(f"ERROR: File '{INPUT_CSV_FILE}' not found.")
        print("Did you run 'engineer_features.py' first?")
        sys.exit(1)

    if df.empty:
        print(f"ERROR: The file '{INPUT_CSV_FILE}' is empty.")
        sys.exit(1)

    print(f"Success. {len(df)} clean laps loaded from CSV.")

    y = df['lap_duration']
    x = df[['circuit_short_name', 'compound', 'current_tyre_age']]

    print("Starting preprocessing...")
    numeric_features = ['current_tyre_age']
    categorical_features = ['circuit_short_name', 'compound']

    numeric_transformer = Pipeline(steps=[('scaler', StandardScaler())])
    categorical_transformer = Pipeline(steps=[('onehot', OneHotEncoder(handle_unknown='ignore'))])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    x_train_processed = preprocessor.fit_transform(x_train)
    x_test_processed = preprocessor.transform(x_test)

    input_shape = x_train_processed.shape[1]
    print(f"Preprocessing completed. Number of input features: {input_shape}")


    model = Sequential()
    model.add(InputLayer(shape=(input_shape,)))
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.1))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='linear'))

    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mean_absolute_error'])

    model.summary()

    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=100,
        restore_best_weights=True
    )

    print("\nStarting model training...")

    history = model.fit(
        x_train_processed,
        y_train,
        epochs=500,
        batch_size=32,
        validation_data=(x_test_processed, y_test),
        callbacks=[early_stopping],
        verbose=2
    )

    print("Training completed.")

    loss, mae = model.evaluate(x_test_processed, y_test, verbose=0)
    print(f"\nEvaluation Results:")
    print(f"  Mean Absolute Error (MAE): {mae:.3f} seconds")
    print(f"  (The model misses, on average, by {mae:.3f} seconds when predicting lap time)")

    model.save(MODEL_OUTPUT_FILE)
    print(f"\n--- TRAINED MODEL SAVED ---")
    print(f"Brain saved at: {MODEL_OUTPUT_FILE}")

    PREPROCESSOR_FILE = "redline_preprocessor.joblib"
    joblib.dump(preprocessor, PREPROCESSOR_FILE)
    print(f"Preprocessor saved at: {PREPROCESSOR_FILE}")

if __name__ == "__main__":

    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        print(f"Success! {len(gpus)} GPU(s) detected by TensorFlow:")
        for gpu in gpus:
            print(f"  {gpu.name}")
    else:
        print("WARNING: No GPU detected. Training on CPU (may be slow).")

    build_and_train_model()
