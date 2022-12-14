from fastapi import APIRouter, Depends, Query, status
from pydantic import PositiveInt
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.dependencies.sessions import define_postgres_session
from app.dependencies.user import identify_user
from app.schemas.transaction import (
    TransactionCreationData,
    TransactionOutputData,
    TransactionsPeriodData,
    TransactionUpdateData,
)
from app.utilities.exceptions.records import (
    CouldNotAccessRecord,
    CouldNotFindRecord,
)
from core.databases.models import Account, Category, Transaction, User
from core.databases.services import TransactionService


transaction_controller: APIRouter = APIRouter(prefix="/transaction", tags=["transaction"])


@transaction_controller.get("/periods", response_model=list[TransactionsPeriodData])
async def get_periods(
    current_user: User = Depends(identify_user),
    session: Session = Depends(define_postgres_session),
) -> list[TransactionsPeriodData]:
    transaction_service: TransactionService = TransactionService(session=session)
    periods_entities: list[tuple[int, int]] = transaction_service.get_user_transaction_periods(current_user)

    return [TransactionsPeriodData(year=year, month=month) for (year, month) in periods_entities]

@transaction_controller.get("/list", response_model=list[TransactionOutputData])
async def get_transactions(
    transactions_period: TransactionsPeriodData = Depends(),
    current_user: User = Depends(identify_user),
    session: Session = Depends(define_postgres_session),
) -> list[Transaction]:
    transaction_service: TransactionService = TransactionService(session=session)

    return transaction_service.get_list(
        Transaction.account.has(user=current_user),
        func.DATE_PART("YEAR", Transaction.due_date) == transactions_period.year,
        func.DATE_PART("MONTH", Transaction.due_date) == transactions_period.month,
    )

@transaction_controller.get("/item", response_model=TransactionOutputData)
async def get_transaction(
    transaction_id: PositiveInt = Query(..., alias="id"),
    current_user: User = Depends(identify_user),
    session: Session = Depends(define_postgres_session),
) -> Transaction:
    transaction_service: TransactionService = TransactionService(session=session)
    transaction: Transaction | None = transaction_service.get_by_id(transaction_id)

    if transaction is None:
        raise CouldNotFindRecord(transaction_id, Transaction)

    if transaction.account.user != current_user:
        raise CouldNotAccessRecord(transaction_id, Transaction)

    return transaction

@transaction_controller.post("/create", response_model=TransactionOutputData, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreationData,
    current_user: User = Depends(identify_user),
    session: Session = Depends(define_postgres_session),
) -> Transaction:
    if not any(transaction_data.account_id == account.id for account in current_user.accounts):
        raise CouldNotFindRecord(transaction_data.account_id, Account)

    if not any(transaction_data.category_id == category.id for category in current_user.categories):
        raise CouldNotFindRecord(transaction_data.category_id, Category)

    transaction_service: TransactionService = TransactionService(session=session)

    return transaction_service.create(
        record_data=transaction_data.dict(),
    )

@transaction_controller.patch("/update", response_model=TransactionOutputData)
async def update_transaction(
    transaction_data: TransactionUpdateData,
    transaction_id: PositiveInt = Query(..., alias="id"),
    current_user: User = Depends(identify_user),
    session: Session = Depends(define_postgres_session),
) -> Transaction:
    transaction_service: TransactionService = TransactionService(session=session)
    transaction: Transaction | None = transaction_service.get_by_id(transaction_id)

    if transaction is None:
        raise CouldNotFindRecord(transaction_id, Transaction)

    if transaction.account.user != current_user:
        raise CouldNotAccessRecord(transaction_id, Transaction)

    return transaction_service.update(
        record=transaction,
        record_data=transaction_data.dict(),
    )

@transaction_controller.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: PositiveInt = Query(..., alias="id"),
    current_user: User = Depends(identify_user),
    session: Session = Depends(define_postgres_session),
):
    transaction_service: TransactionService = TransactionService(session=session)
    transaction: Transaction | None = transaction_service.get_by_id(transaction_id)

    if transaction is None:
        raise CouldNotFindRecord(transaction_id, Transaction)

    if transaction.account.user != current_user:
        raise CouldNotAccessRecord(transaction_id, Transaction)

    transaction_service.delete(transaction)
