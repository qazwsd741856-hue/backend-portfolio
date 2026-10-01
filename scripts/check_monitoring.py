import json
import urllib.request
import sys
import time 

url="http://127.0.0.1:9090/api/v1/query?query=up"

max_tries=6
retry_interval=5

for i in range(max_tries):
    try:
        with urllib.request.urlopen(url,timeout=5) as response:
            data=json.load(response)
        
        results=data["data"]["result"]
        health_jobs=set()
        required_jobs={"fastapi","node-exporter","cadvisor"}

        for item in results:
            job=item["metric"].get("job")
            value=item["value"][1]

            if value=="1":
                health_jobs.add(job)

        if required_jobs.issubset(health_jobs):
            print("Monitoring check passed")
            sys.exit(0)
        if i < max_tries-1:
            print("Monitoring not ready, retrying...")
            time.sleep(retry_interval)
    except Exception as e:
        print(f"Prometheus request failed: {e}")
        if i < max_tries-1:
            print("Monitoring not ready, retrying...")
            time.sleep(retry_interval)
        
        
print("Monitoring check failed")
sys.exit(1)