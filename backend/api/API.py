import os
from fastapi import FastAPI
import sqlite3
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import cv2


app = FastAPI()
snapshot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"device", "snapshot")
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db","events.db")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/events")
def fetch_events():
    sqlconn = sqlite3.connect(db_path)
    cursor = sqlconn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    sqlconn.close()
    return rows

@app.get("/snapshot")

def take_snapshot():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        print("failed to capture")

    filename = "snapshot.png"
    file_path = os.path.join(snapshot_path, filename)
    cv2.imwrite(file_path, frame)
    return FileResponse(file_path, media_type="image/png")
