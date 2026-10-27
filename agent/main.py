import time
import platform
import psutil
import json
import requests

SERVER_URL = "http://127.0.0.1:8000/api/v1/metrics"

def get_system_metrics():
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=True)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    return {
        "hostname": platform.node(),
        "os": platform.system(),
        "timestamp": int(time.time()),
        "metrics": {
            "cpu": {"usage_percent": cpu_usage, "cores": cpu_count},
            "ram": {"total_gb": round(ram.total / (1024**3), 2), "used_gb": round(ram.used / (1024**3), 2), "usage_percent": ram.percent},
            "disk": {"total_gb": round(disk.total / (1024**3), 2), "free_gb": round(disk.free / (1024**3), 2), "usage_percent": disk.percent},
            "network": {"bytes_sent_mb": round(net.bytes_sent / (1024**2), 2), "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)}
        }
    }

if __name__ == "__main__":
    print("--- MiniDog Agent Active ---")
    while True:
        payload = get_system_metrics()
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=3)
            if response.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] Metrics sent successfully to server!")
            else:
                print(f"Server error: {response.status_code}")
        except Exception as e:
            print(f"Could not connect to server: {e}")
        time.sleep(5)