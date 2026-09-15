
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import WaitTimeRequest, WaitTimeResponse
from ml_service import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.load_model()
    yield

app = FastAPI(title="Farmer Procurement ML Engine", lifespan=lifespan)
#Enable CORS for external frontend and mobile app connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_congestion_level(wait_time_mins: float) -> str:
    if wait_time_mins < 30:
        return "LOW"
    elif wait_time_mins <= 90:
        return "MEDIUM"
    return "HIGH"

@app.post("/api/v1/predict/wait-time", response_model=WaitTimeResponse)
async def predict_wait_time(payload: WaitTimeRequest):
    try:
        predicted_mins = await asyncio.to_thread(
            engine.predict,
            payload.current_queue_length,
            payload.active_counters,
            payload.avg_service_time_last_hr,
            payload.hour_of_day,
            payload.day_of_week
        )
        
        predicted_mins = round(predicted_mins, 1)
        risk = calculate_congestion_level(predicted_mins)
        
        lower_bound = round(max(0.0, predicted_mins * 0.9), 1)
        upper_bound = round(predicted_mins * 1.1, 1)

        return WaitTimeResponse(
            center_id=payload.center_id,
            predicted_wait_minutes=predicted_mins,
            congestion_risk=risk,
            confidence_interval=(lower_bound, upper_bound)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )