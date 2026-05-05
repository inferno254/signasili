"""
Lip Sync Scoring Model Training
Temporal CNN + LSTM for lip synchronization scoring
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import json

# Configuration
SEQUENCE_LENGTH = 30
LIP_FEATURES = 40  # Extracted lip features
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.001


def extract_lip_features(face_landmarks: np.ndarray) -> np.ndarray:
    """
    Extract lip-related features from 468 face landmarks.
    
    Features (40 total):
    - Lip aperture: 1 (distance between upper and lower lip)
    - Mouth corners: 2 (left and right displacement)
    - Jaw drop: 1 (angle measurement)
    - Tongue visibility: 1 (binary)
    - Lip rounding: 1 (corner distance)
    - Lip protrusion: 1 (depth)
    - Labial closure: 1 (for /p/, /b/, /m/)
    - Dental placement: 1 (for /t/, /d/, /n/)
    - Velar approximation: 1 (for /k/, /g/, /ng/)
    - + additional shape descriptors
    """
    features = []
    
    # Lip aperture (distance between upper and lower lip)
    # Upper lip: landmarks 0-12 (approximate)
    # Lower lip: landmarks 13-25 (approximate)
    upper_lip = face_landmarks[0:13].mean(axis=0)
    lower_lip = face_landmarks[13:26].mean(axis=0)
    lip_aperture = np.linalg.norm(upper_lip - lower_lip)
    features.append(lip_aperture)
    
    # Mouth corners displacement
    left_corner = face_landmarks[61]  # Approximate left corner
    right_corner = face_landmarks[291]  # Approximate right corner
    features.extend([left_corner[0], right_corner[0]])
    
    # Jaw drop (angle between jaw and chin)
    jaw = face_landmarks[152]
    chin = face_landmarks[0]
    jaw_drop = np.arctan2(jaw[1] - chin[1], jaw[0] - chin[0])
    features.append(jaw_drop)
    
    # Tongue visibility (simplified - would need more sophisticated detection)
    tongue_visible = 0  # Binary: 0 or 1
    features.append(tongue_visible)
    
    # Lip rounding (distance between corners)
    lip_rounding = np.linalg.norm(left_corner - right_corner)
    features.append(lip_rounding)
    
    # Fill remaining features with derived measurements
    # This is a simplified version - full implementation would have more sophisticated feature extraction
    while len(features) < LIP_FEATURES:
        features.append(0.0)
    
    return np.array(features[:LIP_FEATURES])


def build_model() -> tf.keras.Model:
    """
    Build lip sync scoring model.
    
    Architecture:
    - Input: [batch, 30, 40]
    - Conv1D(64, kernel=3) → ReLU → MaxPool
    - Conv1D(128, kernel=3) → ReLU → MaxPool
    - LSTM(64)
    - Dense(32) → Dropout(0.3)
    - Dense(1, sigmoid) → Scale to 0-100
    """
    model = Sequential([
        # Temporal CNN layers
        Conv1D(64, kernel_size=3, activation='relu', input_shape=(SEQUENCE_LENGTH, LIP_FEATURES)),
        MaxPooling1D(pool_size=2),
        
        Conv1D(128, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        
        # LSTM layer
        LSTM(64),
        
        # Dense layers
        Dense(32, activation='relu'),
        Dropout(0.3),
        
        # Output: 0-1, scaled to 0-100
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='mse',
        metrics=['mae']
    )
    
    return model


def train_lip_sync_model(data_dir: str, output_dir: str):
    """
    Train lip sync scoring model.
    
    Args:
        data_dir: Directory containing preprocessed lip sequences
        output_dir: Directory to save model
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))  # Scores 0-100, normalized to 0-1
    
    # Normalize scores to 0-1
    y = y / 100.0
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42
    )
    
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Build model
    model = build_model()
    model.summary()
    
    # Callbacks
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        ModelCheckpoint(
            os.path.join(output_dir, 'best_lip_sync.h5'),
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate
    print("\nEvaluating on test set...")
    test_results = model.evaluate(X_test, y_test, verbose=1)
    
    y_pred = model.predict(X_test) * 100  # Scale back to 0-100
    y_true = y_test * 100
    
    print(f"\nTest MSE: {test_results[0]:.4f}")
    print(f"Test MAE: {test_results[1]*100:.2f} points")
    print(f"RMSE: {np.sqrt(mean_squared_error(y_true, y_pred)):.2f}")
    
    # Save model
    model.save(os.path.join(output_dir, 'lip_sync_model.h5'))
    
    # Convert to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    with open(os.path.join(output_dir, 'lip_sync.tflite'), 'wb') as f:
        f.write(tflite_model)
    
    print(f"\nModel saved to {output_dir}")
    print(f"TFLite model size: {len(tflite_model)/1024:.2f} KB")
    
    return model, history


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train lip sync model')
    parser.add_argument('--data-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='models/lip_sync')
    args = parser.parse_args()
    
    train_lip_sync_model(args.data_dir, args.output_dir)
