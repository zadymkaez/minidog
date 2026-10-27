import time
import os
import platform
import psutil
import json
import subprocess
import requests

SERVER_URL = "http://127.0.0.1:8000/api/v1/metrics"
FAKE_HOSTNAME = os.getenv("FAKE_HOSTNAME", platform.node())

def get_system_logs(disk_percent, ram_percent):
    logs = []
    
    # 1. Automatyczne alerty progowe
    if disk_percent > 85:
        logs.append({
            "level": "CRITICAL",
            "message": f"Krytycznie mało miejsca na dysku głównym: {disk_percent}% zajętości!"
        })
    elif disk_percent > 75:
        logs.append({
            "level": "WARNING",
            "message": f"Ostrzeżenie: dysk zapełnia się w {disk_percent}%."
        })
        
    if ram_percent > 90:
        logs.append({
            "level": "CRITICAL",
            "message": f"Wysokie użycie pamięci RAM: {ram_percent}%!"
        })

    # 2. Pobieranie realnych błędów z systemu (jeśli to Linux)
    if platform.system() == "Linux":
        try:
            # Pobieramy ostatnie błędy z journalctl (poziom err)
            res = subprocess.run(
                ["journalctl", "-p", "err", "-n", "3", "--no-pager", "-o", "short"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    if line.startswith("--") or not line.strip():
                        continue
                    logs.append({
                        "level": "ERROR",
                        "message": f"[System Log] {line.strip()}"
                    })
        except Exception:
            pass

    # Jeśli brak błędów, dodaj wpis informacyjny
    if not logs:
        logs.append({
            "level": "INFO",
            "message": "System działa stabilnie, brak krytycznych alertów."
        })

    return logs

def get_system_metrics():
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=True)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    disk_pct = disk.percent
    ram_pct = ram.percent
    
    system_logs = get_system_logs(disk_pct, ram_pct)

    return {
        "hostname": FAKE_HOSTNAME,
        "os": platform.system(),
        "timestamp": int(time.time()),
        "metrics": {
            "cpu": {"usage_percent": cpu_usage, "cores": cpu_count},
            "ram": {"total_gb": round(ram.total / (1024**3), 2), "used_gb": round(ram.used / (1024**3), 2), "usage_percent": ram_pct},
            "disk": {"total_gb": round(disk.total / (1024**3), 2), "free_gb": round(disk.free / (1024**3), 2), "usage_percent": disk_pct},
            "network": {"bytes_sent_mb": round(net.bytes_sent / (1024**2), 2), "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)},
            "logs": system_logs
        }
    }

if __name__ == "__main__":
    print(f"--- MiniDog Agent Active [{FAKE_HOSTNAME}] ---")
    while True:
        payload = get_system_metrics()
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=3)
            if response.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] Pakiety wysłane pomyślnie.")
            else:
                print(f"Błąd serwera: {response.status_code}")
        except Exception as e:
            print(f"Błąd połączenia z serwerem: {e}")
        time.sleep(5)