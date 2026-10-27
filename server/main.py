from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import os

app = FastAPI(title="MiniDog Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "metrics.db"

# Inicjalizacja bazy danych SQLite
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            os TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            data JSON NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Schemat danych przyjmowanych od Agenta (Pydantic)
class MetricPayload(BaseModel):
    hostname: str
    os: str
    timestamp: int
    metrics: dict

@app.get("/")
def read_root():
    return {"status": "online", "system": "MiniDog Server"}

# Endpoint do odbierania danych od Agentów
@app.post("/api/v1/metrics")
def receive_metrics(payload: MetricPayload):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO metrics (hostname, os, timestamp, data) VALUES (?, ?, ?, ?)",
            (payload.hostname, payload.os, payload.timestamp, json.dumps(payload.metrics))
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Metrics recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/hosts")
def get_hosts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT hostname, os, MAX(timestamp) as last_seen 
        FROM metrics 
        GROUP BY hostname
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    hosts = [{"hostname": r[0], "os": r[1], "last_seen": r[2]} for r in rows]
    return {"hosts": hosts}

@app.get("/api/v1/metrics/history")
def get_metrics_history(hostname: str = None, limit: int = 20):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if hostname:
        cursor.execute('''
            SELECT hostname, os, timestamp, data 
            FROM metrics WHERE hostname = ?
            ORDER BY id DESC LIMIT ?
        ''', (hostname, limit))
    else:
        cursor.execute('''
            SELECT hostname, os, timestamp, data 
            FROM metrics 
            ORDER BY id DESC LIMIT ?
        ''', (limit,))
        
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in reversed(rows):
        history.append({
            "hostname": r[0],
            "os": r[1],
            "timestamp": r[2],
            "data": json.loads(r[3])
        })
    return history