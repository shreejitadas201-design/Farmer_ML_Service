from pydantic import BaseModel
from typing import Tuple


class WaitTimeRequest(BaseModel):
    center_id: str
    current_queue_length: int
    active_counters: int
    avg_service_time_last_hr: float
    hour_of_day: int
    day_of_week: int


class WaitTimeResponse(BaseModel):
    center_id: str
    predicted_wait_minutes: float
    congestion_risk: str
    confidence_interval: Tuple[float, float]


class FeedbackRequest(BaseModel):
    center_id: str
    current_queue_length: int
    active_counters: int
    avg_service_time_last_hr: float
    hour_of_day: int
    day_of_week: int
    actual_wait_minutes: float


class FeedbackResponse(BaseModel):
    status: str
    total_real_data_collected: int
    is_using_synthetic: bool
    message: str