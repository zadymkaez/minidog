import time
import os
import platform
import psutil
import json

def get_system_metrics():
    # Pobieranie statystyk CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=True)
    
    # Pobieranie statystyk pamięci RAM
    ram = psutil.virtual_memory()
    
    # Pobieranie statystyk dysku głównego
    disk = psutil.disk_usage('/')
    
    # Pobieranie statystyk sieci (wysłane/odebrane bajty)
    net = psutil.net_io_counters()

    payload = {
        "hostname": platform.node(),
        "os": platform.system(),
        "timestamp": int(time.time()),
        "metrics": {
            "cpu": {
                "usage_percent": cpu_usage,
                "cores": cpu_count
            },
            "ram": {
                "total_gb": round(ram.total / (1024**3), 2),
                "used_gb": round(ram.used / (1024**3), 2),
                "usage_percent": ram.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": disk.percent
            },
            "network": {
                "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)
            }
        }
    }
    return payload

if __name__ == "__main__":
    print("--- MiniDog Agent Started ---")
    try:
        while True:
            data = get_system_metrics()
            print(json.dumps(data, indent=2))
            print("-" * 40)
            time.sleep(5)  # Pobieraj metryki co 5 sekund
    except KeyboardInterrupt:
        print("\nAgent stopped.")