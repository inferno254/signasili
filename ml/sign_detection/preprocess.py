"""
Preprocess raw videos into keypoint sequences for model training.
Uses MediaPipe Holistic to extract pose, face, and hand landmarks.
"""
import os
import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
import json
from tqdm import tqdm
import pickle

# MediaPipe setup
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

# Configuration
SEQUENCE_LENGTH = 30
POSE_LANDMARKS = 33
FACE_LANDMARKS = 468
HAND_LANDMARKS = 21


def extract_keypoints(results) -> np.ndarray:
    """
    Extract keypoints from MediaPipe results.
    
    Returns:
        Array of shape (1662,) containing:
        - Pose: 33 landmarks * 4 values (x, y, z, visibility) = 132
        - Face: 468 landmarks * 3 values (x, y, z) = 1404
        - Left hand: 21 landmarks * 3 values = 63
        - Right hand: 21 landmarks * 3 values = 63
        Total: 1662
    """
    # Pose landmarks
    if results.pose_landmarks:
        pose = np.array([[lm.x, lm.y, lm.z, lm.visibility] 
                        for lm in results.pose_landmarks.landmark]).flatten()
    else:
        pose = np.zeros(POSE_LANDMARKS * 4)
    
    # Face landmarks
    if results.face_landmarks:
        face = np.array([[lm.x, lm.y, lm.z] 
                        for lm in results.face_landmarks.landmark]).flatten()
    else:
        face = np.zeros(FACE_LANDMARKS * 3)
    
    # Left hand landmarks
    if results.left_hand_landmarks:
        left_hand = np.array([[lm.x, lm.y, lm.z] 
                             for lm in results.left_hand_landmarks.landmark]).flatten()
    else:
        left_hand = np.zeros(HAND_LANDMARKS * 3)
    
    # Right hand landmarks
    if results.right_hand_landmarks:
        right_hand = np.array([[lm.x, lm.y, lm.z] 
                              for lm in results.right_hand_landmarks.landmark]).flatten()
    else:
        right_hand = np.zeros(HAND_LANDMARKS * 3)
    
    # Concatenate all keypoints
    keypoints = np.concatenate([pose, face, left_hand, right_hand])
    
    return keypoints


def process_video(video_path: str, sequence_length: int = SEQUENCE_LENGTH) -> np.ndarray:
    """
    Process a video into keypoint sequences.
    
    Args:
        video_path: Path to video file
        sequence_length: Number of frames per sequence
        
    Returns:
        Array of shape (n_sequences, sequence_length, 1662)
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate frame interval to get sequence_length frames
    frame_interval = max(1, total_frames // sequence_length)
    
    sequences = []
    current_sequence = []
    
    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every nth frame
            if frame_count % frame_interval == 0 and len(current_sequence) < sequence_length:
                # Convert to RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                
                # Process with MediaPipe
                results = holistic.process(image)
                
                # Extract keypoints
                keypoints = extract_keypoints(results)
                current_sequence.append(keypoints)
            
            frame_count += 1
            
            # If sequence is complete, save it
            if len(current_sequence) == sequence_length:
                sequences.append(current_sequence)
                current_sequence = []
    
    cap.release()
    
    if len(current_sequence) > 0:
        # Pad incomplete sequence
        while len(current_sequence) < sequence_length:
            current_sequence.append(current_sequence[-1] if current_sequence else np.zeros(1662))
        sequences.append(current_sequence)
    
    return np.array(sequences) if sequences else np.array([])


def process_dataset(
    raw_data_dir: str,
    output_dir: str,
    label_map: dict = None
):
    """
    Process entire dataset of videos.
    
    Args:
        raw_data_dir: Directory with structure:
            raw_data/
              hello/
                video1.mp4
                video2.mp4
              goodbye/
                video1.mp4
        output_dir: Directory to save processed sequences
        label_map: Dictionary mapping sign names to indices
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'sequences'), exist_ok=True)
    
    if label_map is None:
        # Create label map from directory names
        sign_names = [d for d in os.listdir(raw_data_dir) 
                     if os.path.isdir(os.path.join(raw_data_dir, d))]
        label_map = {name: idx for idx, name in enumerate(sorted(sign_names))}
    
    sequences = []
    labels = []
    
    print(f"Processing {len(label_map)} signs...")
    
    for sign_name, label_idx in tqdm(label_map.items(), desc="Signs"):
        sign_dir = os.path.join(raw_data_dir, sign_name)
        
        if not os.path.isdir(sign_dir):
            continue
        
        # Process all videos for this sign
        video_files = list(Path(sign_dir).glob('*.mp4'))
        
        for video_path in tqdm(video_files, desc=f"{sign_name} videos", leave=False):
            try:
                seq = process_video(str(video_path))
                
                if len(seq) > 0:
                    for s in seq:
                        sequences.append(s)
                        labels.append(label_idx)
            except Exception as e:
                print(f"Error processing {video_path}: {e}")
    
    # Convert to numpy arrays
    sequences = np.array(sequences)
    labels = np.array(labels)
    
    print(f"\nProcessed {len(sequences)} sequences")
    print(f"Sequence shape: {sequences.shape}")
    print(f"Labels shape: {labels.shape}")
    
    # Save
    np.save(os.path.join(output_dir, 'labels.npy'), labels)
    
    # Save sequences as individual files
    for i, seq in enumerate(sequences):
        np.save(os.path.join(output_dir, 'sequences', f'seq_{i:06d}.npy'), seq)
    
    # Save label map
    with open(os.path.join(output_dir, 'label_map.json'), 'w') as f:
        json.dump(label_map, f, indent=2)
    
    # Save metadata
    metadata = {
        'num_sequences': len(sequences),
        'num_classes': len(label_map),
        'sequence_length': SEQUENCE_LENGTH,
        'keypoint_dim': 1662,
        'signs': list(label_map.keys())
    }
    
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nSaved to {output_dir}")
    print(f"Classes: {len(label_map)}")
    
    return sequences, labels, label_map


def visualize_keypoints(video_path: str, output_path: str = None):
    """
    Visualize keypoints on video for debugging.
    """
    cap = cv2.VideoCapture(video_path)
    
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 30.0, 
                             (int(cap.get(3)), int(cap.get(4))))
    
    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(image)
            
            # Draw landmarks
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
            
            if results.left_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            
            if results.right_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            
            if results.face_landmarks:
                mp_drawing.draw_landmarks(
                    image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION)
            
            if output_path:
                out.write(image)
            else:
                cv2.imshow('MediaPipe Holistic', image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    
    cap.release()
    if output_path:
        out.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess KSL videos')
    parser.add_argument('--raw-data', type=str, required=True, help='Directory with raw videos')
    parser.add_argument('--output', type=str, default='processed_data', help='Output directory')
    parser.add_argument('--visualize', type=str, help='Visualize keypoints for a video')
    args = parser.parse_args()
    
    if args.visualize:
        visualize_keypoints(args.visualize)
    else:
        process_dataset(args.raw_data, args.output)
