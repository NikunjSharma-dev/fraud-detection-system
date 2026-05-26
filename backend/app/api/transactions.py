from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.models.schemas import TransactionSubmitRequest, TransactionResponse, OTPVerifyRequest
from app.services.ledger_service import LedgerService
from app.services.fraud_service import FraudService
from uuid import UUID

router = APIRouter()

@router.post("/submit", response_model=TransactionResponse)
async def submit_transaction(
    payload: TransactionSubmitRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # 1. Instant Ledger Write (Triggers DB rules)
    txn = await LedgerService.create_transaction(db, payload)
    
    # 2. If DB approves it, evaluate ML risk asynchronously
    if txn.status == "Approved":
        background_tasks.add_task(
            FraudService.evaluate_transaction,
            db, txn.id, txn.account_id, txn.amount, txn.latitude, txn.longitude
        )
        msg = "Transaction processing. Risk evaluation in progress."
    else:
        msg = f"Transaction {txn.status} by database policy."

    return TransactionResponse(
        transaction_id=str(txn.id),
        status=txn.status,
        message=msg
    )

@router.patch("/{transaction_id}/verify")
async def verify_mfa(
    transaction_id: UUID, 
    payload: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    if payload.otp == "123456": # Mock OTP validation
        await LedgerService.update_transaction_status(db, transaction_id, "Verified")
        return {"message": "Identity verified. Transaction approved."}
    raise HTTPException(status_code=400, detail="Invalid OTP")