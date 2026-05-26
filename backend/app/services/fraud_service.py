import os
import time
import math
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.ml.predict import FraudPredictor
from app.services.ledger_service import LedgerService
from uuid import UUID

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two geo-coordinates in km."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

class FraudService:
    @staticmethod
    def load_models():
        FraudPredictor.load()

    @staticmethod
    async def evaluate_transaction(
        db: AsyncSession, 
        txn_id: UUID, 
        account_id: str, 
        amount: float, 
        current_lat: float, 
        current_lon: float
    ):
        """Async background task to run ML inference without blocking the API."""
        now = time.time()
        
        # 1. Fetch historical context from Redis
        last_lat = float(await redis_client.get(f"user:{account_id}:lat") or current_lat)
        last_lon = float(await redis_client.get(f"user:{account_id}:lon") or current_lon)
        
        # Calculate features
        geo_velocity = haversine(last_lat, last_lon, current_lat, current_lon)
        tx_count_10m = await redis_client.incr(f"user:{account_id}:tx_count")
        if tx_count_10m == 1:
            await redis_client.expire(f"user:{account_id}:tx_count", 600) # 10 min window
            
        hour_of_day = int(time.strftime("%H", time.localtime(now)))
        is_weekend = 1 if time.localtime(now).tm_wday >= 5 else 0
        
        # Simple local Z-score mock (In prod, fetch historical avg/std from DB)
        amount_z_score = (amount - 500) / 200.0 

        # 2. Predict via ML Model
        prediction = FraudPredictor.predict(
            amount=amount,
            geo_velocity=geo_velocity,
            tx_count_10m=tx_count_10m,
            hour_of_day=hour_of_day,
            is_weekend=is_weekend,
            amount_z_score=amount_z_score
        )

        # 3. Update DB if Fraud is detected
        if prediction and prediction.is_fraudulent:
            await LedgerService.update_transaction_status(
                db, txn_id, "Awaiting Verification", True, prediction.risk_score
            )
        else:
            # Update cache with safe coordinates
            await redis_client.set(f"user:{account_id}:lat", current_lat, ex=3600)
            await redis_client.set(f"user:{account_id}:lon", current_lon, ex=3600)