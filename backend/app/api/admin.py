from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, TransactionORM
from sqlalchemy import select, func
from app.services.ledger_service import LedgerService

router = APIRouter()

@router.get("/ledger-summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    # Get hourly aggregate view
    hourly_stats = await LedgerService.get_ledger_summary(db)
    
    # Get total fraud count for today
    fraud_query = select(func.count(TransactionORM.id)).where(TransactionORM.is_fraudulent == True)
    fraud_count = (await db.execute(fraud_query)).scalar() or 0
    
    # Get latest 10 raw transactions for the live table
    raw_tx_query = select(TransactionORM).order_by(TransactionORM.created_at.desc()).limit(10)
    raw_tx_result = await db.execute(raw_tx_query)
    raw_transactions = [
        {
            "id": str(t.id), "account_id": t.account_id, "amount": t.amount, 
            "status": t.status, "risk_score": t.risk_score
        } 
        for t in raw_tx_result.scalars().all()
    ]

    return {
        "total_volume": sum([stat.get('total_volume', 0) for stat in hourly_stats if stat.get('total_volume')]),
        "fraud_count": fraud_count,
        "hourly_stats": hourly_stats,
        "transactions": raw_transactions
    }