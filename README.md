Farmer Procurement ML Engine
This Machine Learning service predicts center wait times and congestion risk for procurement centers using FastAPI and Uvicorn.
🚀 Running with Docker (Recommended for Teammates)
If you have Docker installed, you can build and start the entire service with two simple commands:
1. Build the Docker Image
docker build -t farmer-ml-engine .
2. Run the Container
docker run -p 8000:8000 farmer-ml-engine
The service will now be live at: http://localhost:8000
Interactive Swagger API documentation: http://localhost:8000/docs
💻 Running Locally (Without Docker)
1. Install Dependencies:
pip install -r requirements.txt
2. Start the FastAPI Server:
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
📡 API Contract for App Integration
Endpoint Details
URL: http://localhost:8000/api/v1/predict/wait-time
Method: POST
Headers: Content-Type: application/json
Sample Input Payload (JSON)
{
  "center_id": "CNT-8821",
  "current_queue_length": 18,
  "active_counters": 2,
  "avg_service_time_last_hr": 8.5,
  "hour_of_day": 10,
  "day_of_week": 1
}
Sample Response (JSON)

{
  "center_id": "CNT-8821",
  "predicted_wait_minutes": 76.5,
  "congestion_risk": "MEDIUM",
  "confidence_interval": [
    68.9,
    84.2
  ]
}
🔗 Integration Snippets
JavaScript / React / Web App
async function getWaitTimePrediction(requestData) {
  const response = await fetch('http://localhost:8000/api/v1/predict/wait-time', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestData),
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}
Python / Mobile Backend
import requests

url = "http://localhost:8000/api/v1/predict/wait-time"
payload = {
    "center_id": "CNT-8821",
    "current_queue_length": 18,
    "active_counters": 2,
    "avg_service_time_last_hr": 8.5,
    "hour_of_day": 10,
    "day_of_week": 1
}

response = requests.post(url, json=payload)
print(response.json())