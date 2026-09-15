import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import WaitTimeRequest, WaitTimeResponse, FeedbackRequest, FeedbackResponse
from ml_service import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.load_model()
    yield


app = FastAPI(title="Farmer Procurement ML Engine", lifespan=lifespan)

# Enable CORS for external frontend and mobile app connections
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
            payload.day_of_week,
        )

        predicted_mins = round(predicted_mins, 1)
        congestion_risk = calculate_congestion_level(predicted_mins)

        # Confidence interval estimation (+/- 10%)
        lower_bound = round(max(0.0, predicted_mins * 0.9), 1)
        upper_bound = round(predicted_mins * 1.1, 1)

        return WaitTimeResponse(
            center_id=payload.center_id,
            predicted_wait_minutes=predicted_mins,
            congestion_risk=congestion_risk,
            confidence_interval=(lower_bound, upper_bound),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/feedback", response_model=FeedbackResponse)
async def submit_actual_wait_time(payload: FeedbackRequest):
    try:
        real_count = await asyncio.to_thread(
            engine.add_feedback_and_check_retrain,
            payload.current_queue_length,
            payload.active_counters,
            payload.avg_service_time_last_hr,
            payload.hour_of_day,
            payload.day_of_week,
            payload.actual_wait_minutes,
        )

        using_synthetic = engine.is_using_synthetic
        msg = "Real farmer wait time recorded and model auto-retrained successfully."
        if not using_synthetic:
            msg += " Synthetic baseline data has been automatically removed!"

        return FeedbackResponse(
            status="SUCCESS",
            total_real_data_collected=real_count,
            is_using_synthetic=using_synthetic,
            message=msg,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
