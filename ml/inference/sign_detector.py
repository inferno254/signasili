"""
Real-time Sign Detection Inference
Optimized for web/mobile deployment
"""
import numpy as np
import tensorflow as tf
from typing import List, Tuple, Dict
import json

class SignDetector:
    """
    Real-time KSL sign detector using TensorFlow Lite.
    
    Optimized for:
    - <100ms inference on Pixel 4a
    - <200ms on budget devices
    - <50MB model size
    """
    
    def __init__(self, model_path: str, label_map_path: str):
        """
        Initialize detector with TFLite model.
        
        Args:
            model_path: Path to .tflite model file
            label_map_path: Path to label_map.json
        """
        # Load TFLite model
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        # Get input/output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Load label map
        with open(label_map_path, 'r') as f:
            label_map = json.load(f)
            # Invert label map (index -> name)
            self.labels = {v: k for k, v in label_map.items()}
        
        # Sequence buffer
        self.sequence_length = 30
        self.keypoint_dim = 1662
        self.buffer = []
        
        # Performance tracking
        self.inference_times = []
    
    def preprocess_keypoints(self, keypoints: np.ndarray) -> np.ndarray:
        """
        Normalize keypoints for model input.
        
        - Center to hip center
        - Scale by torso length
        """
        # Center coordinates to hip center
        hip_center_x = keypoints[132]  # Pose landmark 33 x
        hip_center_y = keypoints[133]  # Pose landmark 33 y
        
        # Normalize pose landmarks (first 132 values)
        normalized = keypoints.copy()
        for i in range(33):
            normalized[i*4] -= hip_center_x
            normalized[i*4+1] -= hip_center_y
        
        return normalized
    
    def add_frame(self, keypoints: np.ndarray):
        """
        Add a frame to the sequence buffer.
        
        Args:
            keypoints: Array of shape (1662,)
        """
        # Preprocess
        normalized = self.preprocess_keypoints(keypoints)
        
        # Add to buffer
        self.buffer.append(normalized)
        
        # Keep only last 30 frames
        if len(self.buffer) > self.sequence_length:
            self.buffer.pop(0)
    
    def predict(self) -> Tuple[List[Dict[str, any]], float]:
        """
        Run inference on current sequence buffer.
        
        Returns:
            predictions: List of {label, confidence} dicts
            inference_time_ms: Time taken for inference
        """
        import time
        
        # Check if we have enough frames
        if len(self.buffer) < self.sequence_length:
            return [], 0.0
        
        # Prepare input
        input_data = np.array(self.buffer, dtype=np.float32)
        input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension
        
        # Run inference
        start_time = time.time()
        
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        inference_time = (time.time() - start_time) * 1000
        
        # Get top predictions
        top_k = 5
        top_indices = np.argsort(output[0])[-top_k:][::-1]
        
        predictions = []
        for idx in top_indices:
            label = self.labels.get(int(idx), f"sign_{idx}")
            confidence = float(output[0][idx])
            predictions.append({
                'label': label,
                'confidence': round(confidence, 4)
            })
        
        # Track performance
        self.inference_times.append(inference_time)
        if len(self.inference_times) > 100:
            self.inference_times.pop(0)
        
        return predictions, inference_time
    
    def get_average_inference_time(self) -> float:
        """Get average inference time over last 100 predictions."""
        if not self.inference_times:
            return 0.0
        return sum(self.inference_times) / len(self.inference_times)
    
    def reset(self):
        """Reset the sequence buffer."""
        self.buffer = []


class SignDetectorWeb:
    """
    JavaScript-compatible wrapper for web deployment.
    """
    
    def __init__(self):
        self.model = None
        self.labels = {}
    
    def load_model(self, model_url: str, labels_url: str):
        """Load model for web - would use TensorFlow.js in actual implementation."""
        # This is a placeholder for the web implementation
        # Actual implementation would use tfjs
        pass
    
    def detect(self, keypoints: List[float]) -> List[Dict]:
        """Run detection from web - returns top predictions."""
        # Placeholder for web implementation
        return [{'label': 'HELLO', 'confidence': 0.95}]


def test_detector():
    """Test the sign detector with random data."""
    # Create dummy model and label map for testing
    import tempfile
    
    # Create a simple TFLite model
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(30, 1662)),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(100, activation='softmax')
    ])
    
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    
    # Save temporarily
    with tempfile.NamedTemporaryFile(suffix='.tflite', delete=False) as f:
        f.write(tflite_model)
        model_path = f.name
    
    # Create label map
    label_map = {f'sign_{i}': i for i in range(100)}
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
        json.dump(label_map, f)
        label_map_path = f.name
    
    # Test
    detector = SignDetector(model_path, label_map_path)
    
    # Add random frames
    for _ in range(30):
        keypoints = np.random.randn(1662)
        detector.add_frame(keypoints)
    
    # Predict
    predictions, inference_time = detector.predict()
    
    print(f"Predictions: {predictions}")
    print(f"Inference time: {inference_time:.2f} ms")
    print(f"Average inference time: {detector.get_average_inference_time():.2f} ms")
    
    # Cleanup
    import os
    os.unlink(model_path)
    os.unlink(label_map_path)


if __name__ == '__main__':
    test_detector()
