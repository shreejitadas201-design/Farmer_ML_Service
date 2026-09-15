from pydantic import BaseModel, Field
from typing import Tuple

# Defines the input structure for incoming requests
class WaitTimeRequest(BaseModel):
    center_id: str = Field(..., example="CNT-8821")
    current_queue_length: int = Field(..., ge=0, example=18)
    active_counters: int = Field(..., gt=0, example=2)
    avg_service_time_last_hr: float = Field(..., gt=0.0, example=8.5)
    hour_of_day: int = Field(..., ge=0, le=23, example=10)
    day_of_week: int = Field(..., ge=0, le=6, example=1) # 0=Monday, 6=Sunday

# Defines the output structure returned to the user
class WaitTimeResponse(BaseModel):
    center_id: str
    predicted_wait_minutes: float
    congestion_risk: str
    confidence_interval: Tuple[float, float]