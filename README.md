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

### Detection Model

YOLO11s: https://github.com/ultralytics/ultralytics
License: https://www.gnu.org/licenses/agpl-3.0.en.html

Modifications: Fine-tuned on custom datasets.

### Datasets

**Helmet + Vest:**

Huang, Mei-Ling; Cheng, Ying (2025), “Dataset of Personal Protective Equipment (PPE)”, Mendeley Data, V6, doi: 10.17632/zkzghjvpn2.6
https://data.mendeley.com/datasets/zkzghjvpn2/6

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)

Modifications: Removed negative class labels; NO-Helmet, NO-Vest

**Helmet only:**

Safety Helmet Dataset
https://universe.roboflow.com/workplace-rchqz/safety-helmet-dataset-ueg5o

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)

Modifications: Removed class labels; head, person.

**Person only:**

Person Computer Vision Dataset
https://universe.roboflow.com/vnpt-wm4cs/person-2ktoq

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)

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


**Important Tracker Parameters:**

1. **`track_buffer`**: For how long time in frames the system will remember a track until it is removed.
   - ↑ Can recover objects from longer occlusions.
   - ↓ Smaller buffer and faster clean up. Can result in losing tracks during occlusions.

2. **`track_high_thresh`**: Threshold of detection confidence in order to be associated/matched with existing tracks.
   - ↑ More robust to false matches but can miss matches of lower confidence objects that for instance are occluded.
   - ↓ Allows more detections for matching with existing objects. Fewer lost tracks but can result in an increased number of ID switches. 

3. **`new_track_thresh`**: Threshold of detection confidence in order for the tracker to create a new track.
   - ↑ More robust to creating tracks from false detections. Can delay the number of frames until a new track is created.
   - ↓ Faster creations of new track but can increase risks of false positives and ID switches.

4. **`track_low_thresh`**: Minimum detection confidence to be used in association with unmatched tracks.
   - ↑ Reduces the number of false positives but may miss to recover tracks that for instance are occluded.
   - ↓ Can help to recover heavily occluded objects but could also cause false matches.
   
5. **`appearance_thresh`**: Threshold in appearance similarity of tracks inbetween frames.
   - ↑ Stricter visual similarity in order to match objects inbetween frames, can fail to recover occluded or changed objects. 
   - ↓ Looser visual similarity but may result in an increase of ID switches of similar-looking objects.
   
6. **`proximity_thresh`**: Threshold for spatial matching of tracks between frames.
   - ↑ Stricter spatial matching, reduces the number of wrong matches but could drop occluded or fast-moving objects.
   - ↓ More robust to various motions such as inconsistent movement.

7. **`match_thresh`**: Combines proximity_thresh and appearance_thresh to confirm a match.
   - ↑ Stricter matching, fewer false positives but may miss lower confident matches.
   - ↓ Looser matching, better continuity at keeping matches but more prone to ID switches.

8. **`frame_age_threshold`**: Minimum number of frames until a track is being considered confirmed/alive.
   - ↑ More robust to false tracks but takes longer time to be confirmed.
   - ↓ Faster confirmation of new tracks, but may confirm false tracks. 

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
