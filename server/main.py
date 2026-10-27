from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import os

app = FastAPI(title="MiniDog Server")

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

# Endpoint dla Dashboardu - lista hostów i ich ostatnie metryki
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