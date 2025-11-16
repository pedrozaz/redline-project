import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Embedding, Concatenate, Flatten, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import os

from src.model import data_loader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "data")
MODEL_PATH = os.path.join(MODEL_DIR, "model.keras")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
DRIVER_ENCODER_PATH = os.path.join(MODEL_DIR, "driver_encoder.joblib")
CONSTRUCTOR_ENCODER_PATH = os.path.join(MODEL_DIR, "constructor_encoder.joblib")

def preprocess_data(df: pd.DataFrame):

    print("Starting preprocessing...")

    os.makedirs(MODEL_DIR, exist_ok=True)

    target = 'points'

    cat_features = ['driverid', 'constructorid']
    num_features = [
        'grid',
        'quali_position',
        'driver_points_roll_5',
        'constructor_points_roll_5'
    ]

    features = cat_features + num_features

    df[num_features] = df[num_features].fillna(0)
    df[cat_features] = df[cat_features].fillna('unknown')

    X = df[features]
    y = df[target]

    driver_encoder = LabelEncoder()
    X_cat_driver = driver_encoder.fit_transform(X['driverid'])
    joblib.dump(driver_encoder, DRIVER_ENCODER_PATH)

    constructor_encoder = LabelEncoder()
    X_cat_constructor = constructor_encoder.fit_transform(X['constructorid'])
    joblib.dump(constructor_encoder, CONSTRUCTOR_ENCODER_PATH)

    scaler = StandardScaler()
    X_num = scaler.fit_transform(X[num_features])
    joblib.dump(scaler, SCALER_PATH)

    print("Preprocessors saved.")

    (
        X_num_train, X_num_test,
        X_cat_driver_train, X_cat_driver_test,
        X_cat_constructor_train, X_cat_constructor_test,
        y_train, y_test
    ) = train_test_split(
        X_num,
        X_cat_driver,
        X_cat_constructor,
        y,
        test_size=0.2,
        random_state=42
    )

    X_train_list = [X_num_train, X_cat_driver_train, X_cat_constructor_train]
    X_test_list = [X_num_test, X_cat_driver_test, X_cat_constructor_test]

    vocab_sizes = {
        'driverid': len(driver_encoder.classes_),
        'constructorid': len(constructor_encoder.classes_)
    }

    return (X_train_list, X_test_list, y_train, y_test), vocab_sizes


def build_model(vocab_sizes: dict, num_features_shape: int) -> Model:

    print("Building model architecture...")

    input_num = Input(shape=(num_features_shape,), name="input_numerical")
    input_driver = Input(shape=(1,), name="input_driverid")
    input_constructor = Input(shape=(1,), name="input_constructorid")

    emb_driver = Embedding(input_dim=vocab_sizes['driverid'], output_dim=10, name="embedding_driver")(input_driver)
    emb_constructor = Embedding(input_dim=vocab_sizes['constructorid'], output_dim=8, name="embedding_constructor")(input_constructor)

    flat_driver = Flatten()(emb_driver)
    flat_constructor = Flatten()(emb_constructor)

    concat = Concatenate()([input_num, flat_driver, flat_constructor])

    x = Dense(128, activation='relu')(concat)
    x = Dropout(0.3)(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.2)(x)
    x = Dense(32, activation='relu')(x)

    output = Dense(1, activation='linear', name="output_points")(x)

    model = Model(
        inputs=[input_num, input_driver, input_constructor],
        outputs=output
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='mean_squared_error',
        metrics=['mean_absolute_error']
    )

    return model

def train_model():

    raw_data = data_loader.fetch_all_data()
    if raw_data.empty:
        print("No data loaded. Exiting.")
        return

    processed_data = data_loader.feature_engineer(raw_data)

    (X_train_list, X_test_list, y_train, y_test), vocabs = preprocess_data(processed_data)

    model = build_model(vocabs, num_features_shape=X_train_list[0].shape[1])
    model.summary()

    print("\nStarting model training...")
    early_stopping = EarlyStopping(monitor='val_loss', patience=100, restore_best_weights=True)

    history = model.fit(
        X_train_list,
        y_train,
        validation_data=(X_test_list, y_test),
        epochs=500,
        batch_size=32,
        callbacks=[early_stopping],
        verbose=1
    )

    model.save(MODEL_PATH)
    print(f"\nModel training complete. Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()