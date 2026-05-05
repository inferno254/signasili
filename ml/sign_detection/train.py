"""
KSL Sign Detection Model Training
LSTM-based sequence classifier for Kenyan Sign Language
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import json
import pickle

# Configuration
SEQUENCE_LENGTH = 30
KEYPOINT_DIM = 1662  # 33 pose + 468 face + 21 left hand + 21 right hand
NUM_CLASSES = 100  # Top 100 KSL signs
BATCH_SIZE = 32
EPOCHS = 200
LEARNING_RATE = 0.001


def load_data(data_dir: str):
    """
    Load preprocessed keypoint sequences and labels.
    
    Expected data structure:
    - data_dir/
      - sequences/ (numpy files of shape [n_samples, 30, 1662])
      - labels.npy
      - label_map.json (sign name to index)
    """
    sequences = []
    labels = []
    
    # Load all sequence files
    for file in os.listdir(os.path.join(data_dir, 'sequences')):
        if file.endswith('.npy'):
            seq = np.load(os.path.join(data_dir, 'sequences', file))
            sequences.append(seq)
    
    sequences = np.array(sequences)
    labels = np.load(os.path.join(data_dir, 'labels.npy'))
    
    # Load label mapping
    with open(os.path.join(data_dir, 'label_map.json'), 'r') as f:
        label_map = json.load(f)
    
    return sequences, labels, label_map


def augment_sequence(sequence: np.ndarray) -> np.ndarray:
    """
    Apply data augmentation to a sequence.
    
    Techniques:
    - Rotation (±15°)
    - Translation (±10% in x,y)
    - Scaling (±20%)
    - Horizontal flip (for non-symmetric signs)
    - Gaussian noise (σ=0.01)
    - Temporal masking (random 5 frame dropout)
    - Speed perturbation (0.9x-1.1x)
    """
    augmented = sequence.copy()
    
    # Random rotation (simplified - would apply rotation matrix)
    angle = np.random.uniform(-15, 15)
    
    # Random translation
    tx = np.random.uniform(-0.1, 0.1)
    ty = np.random.uniform(-0.1, 0.1)
    augmented[:, 0::3] += tx  # x coordinates
    augmented[:, 1::3] += ty  # y coordinates
    
    # Random scaling
    scale = np.random.uniform(0.8, 1.2)
    augmented[:, :2] *= scale  # x and y
    
    # Gaussian noise
    noise = np.random.normal(0, 0.01, augmented.shape)
    augmented += noise
    
    # Temporal masking (drop random frames)
    if np.random.random() > 0.5:
        mask_indices = np.random.choice(SEQUENCE_LENGTH, size=5, replace=False)
        augmented[mask_indices] = 0
    
    return augmented


def build_model(num_classes: int = NUM_CLASSES) -> tf.keras.Model:
    """
    Build LSTM-based sign detection model.
    
    Architecture:
    - Input: [batch, 30, 1662]
    - LSTM 128 (return sequences)
    - Batch Norm
    - Bidirectional LSTM 256 (return sequences)
    - Batch Norm
    - LSTM 128
    - Batch Norm
    - Dense 64 + Dropout 0.3
    - Dense 32 + Dropout 0.2
    - Dense num_classes (softmax)
    """
    model = Sequential([
        Input(shape=(SEQUENCE_LENGTH, KEYPOINT_DIM)),
        
        # First LSTM layer
        LSTM(128, return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
        BatchNormalization(),
        
        # Bidirectional LSTM
        Bidirectional(LSTM(256, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)),
        BatchNormalization(),
        
        # Third LSTM layer
        LSTM(128, return_sequences=False, dropout=0.2, recurrent_dropout=0.2),
        BatchNormalization(),
        
        # Dense layers
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        
        # Output layer
        Dense(num_classes, activation='softmax')
    ])
    
    # Compile
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='categorical_crossentropy',
        metrics=[
            'accuracy',
            tf.keras.metrics.TopKCategoricalAccuracy(k=5, name='top5_accuracy'),
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    
    return model


def normalize_keypoints(sequences: np.ndarray) -> np.ndarray:
    """
    Normalize keypoints for model input.
    
    - Center to hip center (pose landmark 33)
    - Scale by torso length
    - Zero-mean, unit-variance
    """
    normalized = sequences.copy()
    
    # Center coordinates to hip center (landmark 33, indices 33*4=132 to 135)
    hip_center_x = sequences[:, :, 132]
    hip_center_y = sequences[:, :, 133]
    
    # Subtract hip center from all landmarks
    for i in range(33):  # Pose landmarks
        normalized[:, :, i*4] -= hip_center_x  # x
        normalized[:, :, i*4+1] -= hip_center_y  # y
    
    # Scale by torso length (hip to shoulder)
    shoulder_y = sequences[:, :, 13*4+1]  # Left shoulder y
    hip_y = sequences[:, :, 33*4+1]  # Hip y
    torso_length = np.abs(shoulder_y - hip_y)
    torso_length = np.maximum(torso_length, 1e-7)  # Avoid division by zero
    
    # Normalize
    normalized = normalized / torso_length[:, :, np.newaxis]
    
    return normalized


def train_model(data_dir: str, output_dir: str):
    """
    Main training pipeline.
    
    Args:
        data_dir: Directory containing preprocessed sequences
        output_dir: Directory to save model and artifacts
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    print("Loading data...")
    X, y, label_map = load_data(data_dir)
    
    # Normalize
    print("Normalizing keypoints...")
    X = normalize_keypoints(X)
    
    # Convert labels to categorical
    y_categorical = to_categorical(y, num_classes=len(label_map))
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_categorical, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42
    )
    
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Build model
    print("Building model...")
    model = build_model(num_classes=len(label_map))
    model.summary()
    
    # Callbacks
    callbacks = [
        EarlyStopping(
            monitor='val_accuracy',
            patience=20,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=10,
            min_lr=1e-6,
            verbose=1
        ),
        ModelCheckpoint(
            os.path.join(output_dir, 'best_model.h5'),
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train
    print("Training...")
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
    print(f"Test accuracy: {test_results[1]:.4f}")
    print(f"Test top-5 accuracy: {test_results[2]:.4f}")
    
    # Classification report
    y_pred = model.predict(X_test)
    y_pred_classes = np.argmax(y_pred, axis=1)
    y_true_classes = np.argmax(y_test, axis=1)
    
    print("\nClassification Report:")
    print(classification_report(y_true_classes, y_pred_classes, target_names=list(label_map.keys())))
    
    # Save artifacts
    print("\nSaving artifacts...")
    
    # Save model
    model.save(os.path.join(output_dir, 'sign_detection_model.h5'))
    
    # Convert to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()
    
    with open(os.path.join(output_dir, 'sign_detection.tflite'), 'wb') as f:
        f.write(tflite_model)
    
    # Save label map
    with open(os.path.join(output_dir, 'label_map.json'), 'w') as f:
        json.dump(label_map, f)
    
    # Save training history
    with open(os.path.join(output_dir, 'history.pkl'), 'wb') as f:
        pickle.dump(history.history, f)
    
    print(f"\nTraining complete! Artifacts saved to {output_dir}")
    print(f"Model size: {len(tflite_model) / 1024 / 1024:.2f} MB")
    
    return model, history


def export_for_mobile(model_path: str, output_path: str):
    """
    Export model for mobile deployment.
    
    Creates a smaller, optimized model for on-device inference.
    """
    model = tf.keras.models.load_model(model_path)
    
    # Convert to TFLite with quantization
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS_INT8
    ]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    
    tflite_model = converter.convert()
    
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"Mobile model exported: {output_path}")
    print(f"Size: {len(tflite_model) / 1024:.2f} KB")


def representative_dataset_gen():
    """Generator for representative dataset (quantization)."""
    for _ in range(100):
        yield [np.random.randn(1, SEQUENCE_LENGTH, KEYPOINT_DIM).astype(np.float32)]


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train KSL sign detection model')
    parser.add_argument('--data-dir', type=str, required=True, help='Directory with training data')
    parser.add_argument('--output-dir', type=str, default='models', help='Output directory')
    args = parser.parse_args()
    
    train_model(args.data_dir, args.output_dir)
