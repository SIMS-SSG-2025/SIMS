import os
from fastapi import FastAPI
import sqlite3

from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db","events.db")

def fetch_events():
    sqlconn = sqlite3.connect(db_path)
    cursor = sqlconn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    sqlconn.close()
    return rows

@app.get("/events")
def get_events():
    return fetch_events()
