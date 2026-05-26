"""
Fraud Detection System — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import transactions, admin
from app.models.database import init_db
from app.services.fraud_service import FraudService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # Initialize DB connection pool
    await init_db()
    # Warm up ML model
    FraudService.load_models()
    print("✅ Fraud Detection Backend is ready.")
    yield
    print("⏹️  Shutting down...")


app = FastAPI(
    title="Fraud Detection API",
    description="Real-time fraud detection with ML inference, PostgreSQL ledger, and Redis feature store.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(transactions.router, prefix="/transaction", tags=["Transactions"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "fraud-detection-api"}