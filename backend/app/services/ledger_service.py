from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.database import TransactionORM
from app.models.schemas import TransactionSubmitRequest
from uuid import UUID

class LedgerService:
    @staticmethod
    async def create_transaction(db: AsyncSession, payload: TransactionSubmitRequest) -> TransactionORM:
        """Inserts transaction. The PostgreSQL trigger will automatically set 'Approved' or 'Declined'."""
        new_txn = TransactionORM(
            account_id=payload.account_id,
            amount=payload.amount,
            latitude=payload.lat,
            longitude=payload.lon
        )
        db.add(new_txn)
        await db.commit()
        await db.refresh(new_txn)
        return new_txn

    @staticmethod
    async def update_transaction_status(
        db: AsyncSession, 
        txn_id: UUID, 
        status: str, 
        is_fraudulent: bool = False, 
        risk_score: float = 0.0
    ):
        """Updates transaction after ML evaluation or OTP verification."""
        query = select(TransactionORM).where(TransactionORM.id == txn_id)
        result = await db.execute(query)
        txn = result.scalar_one_or_none()
        
        if txn:
            txn.status = status
            txn.is_fraudulent = is_fraudulent
            if risk_score > 0:
                txn.risk_score = risk_score
            await db.commit()
            
    @staticmethod
    async def get_ledger_summary(db: AsyncSession):
        """Fetches the aggregated data from the PostgreSQL View."""
        result = await db.execute(text("SELECT * FROM vw_ledger_summary LIMIT 24"))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
