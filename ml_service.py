import joblib
import numpy as np
import os

class PredictionEngine:
    def __init__(self, model_path: str = "models/wait_time_model.pkl"):
        self.model = None
        self.model_path = model_path

    def load_model(self):
        """Loads the trained model if available."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            self.model = None

    def predict(self, current_queue: int, active_counters: int, avg_service_time: float, hour: int, day: int) -> float:
        """Calculates queue wait time."""
        if self.model is None:
            # Heuristic calculation if model file isn't loaded
            return (current_queue / max(1, active_counters)) * avg_service_time

        features = np.array([[current_queue, active_counters, avg_service_time, hour, day]])
        prediction = self.model.predict(features)[0]
        return max(0.0, float(prediction))

engine = PredictionEngine()