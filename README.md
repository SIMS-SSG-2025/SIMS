# SIMS - SSG - WorkSight

> **Note**: This is a prototype system developed for research and educational purposes.

A real-time AI-powered safety monitoring system that detects persons, tracks them across frames, monitors restricted zones, and enforces PPE (Personal Protective Equipment) compliance using YOLO11 object detection models.

## Architecture

The system consists of three main components:

1. **Device Runtime** (`device/`) - Edge AI system running YOLO11 models with object tracking
2. **Backend API** (`backend/`) - FastAPI server managing SQLite database and REST endpoints
3. **Frontend Dashboard** (`frontend/`) - SvelteKit application for monitoring and configuration

### Deployment Architecture

- **Edge Device (Nvidia Jetson Nano Orin)**: Runs the Backend API and Device Runtime
- **Monitoring Computer**: Runs the Frontend Dashboard, connects to edge device via network

The frontend communicates with the backend API over the network using the Jetson's IP address.

## Prerequisites

## Quick Start

### 1. Initial Setup

#### Initialize Database
```powershell
# From project root
python -m backend.db.init_db
```

This creates the SQLite database with required tables at `backend/db/events.db`.

#### Install Frontend Dependencies
```powershell
cd frontend
npm install
```

### 2. Start the System

The system requires **two processes on the edge device** and **one process on your monitoring computer**.

#### On Edge Device (Nvidia Jetson Nano Orin)

**Terminal 1: Start Backend API**
```bash
# From project root
uvicorn backend.api.API:app --host 0.0.0.0 --port 8000
```
Note: `--host 0.0.0.0` allows connections from other computers on the network.
API will be available at `http://<JETSON_IP>:8000`

**Terminal 2: Start Device Runtime**
```bash
# From project root
python -m device.main
```
This starts the AI processing system with camera capture, object detection, and tracking.

#### On Monitoring Computer (Windows/Mac/Linux)

**Terminal 3: Start Frontend Dashboard**
```powershell
cd frontend
npm run dev
```

### 3. Initial Configuration

1. **Capture Snapshot**: Visit the dashboard and click "Setup Configuration"
2. **Draw Zones**: Use the zone drawer to define restricted areas on the camera snapshot
3. **Save Configuration**: Name the location and save
4. **Start AI Processing**: Click "Start System" in the dashboard

## Configuration & Tuning

### Detection Model Parameters

Edit `device/DeviceRuntime.py` to tune detection parameters:

```python
detections = run_inference(rgb_frame, self.model, conf=0.25, iou=0.5)
```

**Key Parameters:**
- **`conf`** (0.0-1.0, default: 0.25): Confidence threshold for detections
  - Lower values = more detections (including false positives)
  - Higher values = fewer but more confident detections

- **`iou`** (0.0-1.0, default: 0.5): Intersection over Union threshold for NMS (Non-Maximum Suppression)
  - Lower values = more aggressive suppression of overlapping boxes
  - Higher values = allow more overlapping detections

### Tracker Parameters

Edit `device/inference/tracker.py` to tune tracking behavior:

```python
args = SimpleNamespace(
    track_buffer=300,           # Frames to keep lost tracks (30s at 10fps)
    track_high_thresh=0.7,      # High confidence threshold for track confirmation
    track_low_thresh=0.05,      # Low confidence threshold (tracks below are removed)
    new_track_thresh=0.8,       # Confidence threshold to start new track
    match_thresh=0.5,           # Matching threshold for data association
    fuse_score=True,            # Fuse detection and tracking scores
    proximity_thresh=0.35,      # Distance threshold for association (ReID)
    appearance_thresh=0.2,      # Appearance similarity threshold (ReID)
)
```

**Important Tracker Parameters:**

1. **`track_buffer`**: How long to remember lost tracks (in frames)
   - Increase if objects frequently leave and re-enter frame
   - Default 300 frames ≈ 30 seconds at 10fps

2. **`track_high_thresh`**: Confidence required to activate a track
   - Higher = more stable tracks but may miss objects
   - Recommended: 0.6-0.8

3. **`new_track_thresh`**: Confidence required to start new track
   - Higher = fewer false positive tracks
   - Recommended: 0.7-0.9

4. **`proximity_thresh`**: Maximum distance for matching (with ReID)
   - Increase for fast-moving objects
   - Decrease for static scenes

5. **`appearance_thresh`**: ReID similarity threshold
   - Lower = stricter appearance matching
   - Higher = more lenient matching

### Frame Sampling

Edit `device/DeviceRuntime.py` to control frame sampling:

```python
self.FRAME_SAMPLE = 6  # Store object positions every N frames
```

- **Lower values** = more frequent position storage (higher database load)
- **Higher values** = less frequent storage (lower database load, coarser movement data)

### Camera Source

Edit `device/DeviceRuntime.py` to change camera source:

```python
self.cam = cv2.VideoCapture(0)  # USB camera connected to Jetson
```

### API Configuration (Frontend)

**CRITICAL**: Configure the frontend to connect to your Jetson's IP address.

Edit `frontend/src/lib/api/config.ts` on your monitoring computer:

```typescript
export const API_BASE_URL = "http://10.10.67.44:8000"; // Nvidia Jetson
```

```

### Model Selection

Edit `device/DeviceRuntime.py` to change detection models:

```python
def _load_model(self):
    # Primary detection model (line ~155)
    self.model = YOLO("device/training/models/yolo11_person_only.pt")

    # PPE classification model (line ~157)
    # Loaded in EventManager - see device/logic/events.py
```
