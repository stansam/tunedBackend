from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import Transaction, TransactionType, TransactionStatus
from tuned.dtos.payment import TransactionCreateDTO, TransactionResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class CreateTransaction:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: TransactionCreateDTO) -> TransactionResponseDTO:
        try:
            try:
                type = TransactionType(data.type.lower()) if data.type else TransactionType.PAYMENT
            except ValueError:
                raise ValueError(f"Invalid transaction type: {data.type}")
            try:
                status = TransactionStatus(data.status.lower()) if data.status else TransactionStatus.PENDING
            except ValueError:
                raise ValueError(f"Invalid transaction status: {data.status}")
            transaction = Transaction(
                payment_id=data.payment_id,
                transaction_id=data.transaction_id,
                type=type,
                amount=data.amount,
                status=status,
            )
            self.session.add(transaction)
            self.session.flush()
            return TransactionResponseDTO.from_model(transaction)
        except IntegrityError as e:
            logger.error(f"[CreateTransaction] Integrity error: {e}")
            raise AlreadyExists("Transaction could not be created due to an integrity conflict.") from e
        except SQLAlchemyError as e:
            logger.error(f"[CreateTransaction] DB error: {e}")
            raise DatabaseError("Database error while creating transaction.") from e

class GetTransactionByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, transaction_id: str) -> TransactionResponseDTO:
        try:
            stmt = select(Transaction).where(Transaction.id == transaction_id)
            transaction = self.session.scalar(stmt)
            if not transaction:
                raise NotFound("Transaction not found.")
            return TransactionResponseDTO.from_model(transaction)
        except SQLAlchemyError as e:
            logger.error(f"[GetTransactionByID] DB error: {e}")
            raise DatabaseError("Database error while fetching transaction.") from e

class GetTransactionsByPaymentID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, payment_id: str) -> list[TransactionResponseDTO]:
        try:
            stmt = select(Transaction).where(Transaction.payment_id == payment_id)
            transactions = self.session.scalars(stmt).all()
            return [TransactionResponseDTO.from_model(t) for t in transactions]
        except SQLAlchemyError as e:
            logger.error(f"[GetTransactionsByPaymentID] DB error: {e}")
            raise DatabaseError("Database error while fetching transactions.") from e
