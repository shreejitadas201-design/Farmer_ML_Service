import os
import sqlite3
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

DB_FILE = "farmer_data.db"
MODEL_FILE = "farmer_model.pkl"
REAL_DATA_THRESHOLD = 20  # Minimum real data points required to discard synthetic data


class MLEngine:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_using_synthetic = True
        self._init_db()

    def _init_db(self):
        """Initializes SQLite table for storing feedback data and syncs synthetic flag."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS procurement_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_length INTEGER,
                active_counters INTEGER,
                avg_service_time REAL,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                actual_wait_mins REAL,
                is_synthetic INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        # Seed initial synthetic data if database is empty
        cursor.execute("SELECT COUNT(*) FROM procurement_records")
        if cursor.fetchone()[0] == 0:
            self._seed_synthetic_data(cursor)
            conn.commit()

        # Sync the synthetic flag with actual DB state upon startup
        cursor.execute("SELECT COUNT(*) FROM procurement_records WHERE is_synthetic = 1")
        self.is_using_synthetic = cursor.fetchone()[0] > 0

        conn.close()

    def _seed_synthetic_data(self, cursor):
        """Inserts baseline synthetic data so model works on day 1."""
        np.random.seed(42)
        synthetic_rows = []
        for _ in range(100):
            q_len = np.random.randint(1, 50)
            counters = np.random.randint(1, 5)
            avg_service = np.random.uniform(3.0, 15.0)
            hour = np.random.randint(8, 18)
            day = np.random.randint(0, 6)
            # Simulated physics formula: queue * service_time / counters
            actual_wait = (q_len * avg_service) / max(1, counters) + np.random.normal(0, 5)
            actual_wait = max(1.0, actual_wait)
            synthetic_rows.append((q_len, counters, avg_service, hour, day, actual_wait, 1))

        cursor.executemany("""
            INSERT INTO procurement_records 
            (queue_length, active_counters, avg_service_time, hour_of_day, day_of_week, actual_wait_mins, is_synthetic)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, synthetic_rows)

    def load_model(self):
        """Loads model and scaler from file if exists, otherwise trains initial baseline."""
        if os.path.exists(MODEL_FILE):
            self.model = joblib.load(MODEL_FILE)
        else:
            self.retrain_model()

        # Load scaler if available
        if os.path.exists("scaler.pkl"):
            self.scaler = joblib.load("scaler.pkl")
        else:
            self.scaler = None

    def predict(self, queue_length, active_counters, avg_service_time, hour_of_day, day_of_week):
        """Makes wait time prediction."""
        X = np.array([[queue_length, active_counters, avg_service_time, hour_of_day, day_of_week]])

        # Apply scaling if scaler exists
        if hasattr(self, 'scaler') and self.scaler is not None:
            X = self.scaler.transform(X)

        prediction = self.model.predict(X)[0]
        return max(1.0, float(prediction))

    def add_feedback_and_check_retrain(self, queue_length, active_counters, avg_service_time, hour_of_day, day_of_week, actual_wait_mins):
        """Stores actual farmer wait time and triggers auto-retraining when threshold is hit."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Save real data point
        cursor.execute("""
            INSERT INTO procurement_records 
            (queue_length, active_counters, avg_service_time, hour_of_day, day_of_week, actual_wait_mins, is_synthetic)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (queue_length, active_counters, avg_service_time, hour_of_day, day_of_week, actual_wait_mins))
        conn.commit()

        # Check total real data count
        cursor.execute("SELECT COUNT(*) FROM procurement_records WHERE is_synthetic = 0")
        real_count = cursor.fetchone()[0]

        # Auto-delete synthetic data if real data threshold is reached
        if real_count >= REAL_DATA_THRESHOLD:
            cursor.execute("DELETE FROM procurement_records WHERE is_synthetic = 1")
            conn.commit()
            self.is_using_synthetic = False

        conn.close()

        # Auto retrain model with updated data
        self.retrain_model()
        return real_count

    def retrain_model(self):
        """Retrains Random Forest model on stored data and updates saved file."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT queue_length, active_counters, avg_service_time, hour_of_day, day_of_week, actual_wait_mins 
            FROM procurement_records
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return

    data = np.array(rows)
    X = data[:, :-1]
    y = data[:, -1]

    # Fit scaler on new database records
    from sklearn.preprocessing import StandardScaler
    self.scaler = StandardScaler()
    X_scaled = self.scaler.fit_transform(X)

    # Fit model on scaled data and save both
    self.model.fit(X_scaled, y)
    joblib.dump(self.model, MODEL_FILE)
    joblib.dump(self.scaler, "scaler.pkl")

engine = MLEngine()