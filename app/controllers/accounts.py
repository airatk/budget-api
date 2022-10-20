from sqlalchemy.orm import Session

from pydantic import BaseModel
from pydantic import Field

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.dependencies.session import define_local_session
from app.dependencies.user import identify_user

from app.models import User
from app.models import Account
from app.models.account import CurrencyType
from app.models.transaction import TransactionType


accounts_controller: APIRouter = APIRouter(prefix="/accounts")


class AccountData(BaseModel):
    id: int | None
    name: str = Field(min_length=1)
    currency: CurrencyType
    openning_balance: float = 0.00

    class Config:
        orm_mode = True

class AccountBalance(BaseModel):
    account: str
    balance: float

class AccountsSummary(BaseModel):
    balance: float
    incomes: float
    outcomes: float


@accounts_controller.get("/summary")
async def get_summary(current_user: User = Depends(identify_user), session: Session = Depends(define_local_session)):
    # TODO: There should be summary for current period & all the time.
    #       It should include `Balance`, `Income` & `Outcome` only.
    pass

@accounts_controller.get("/last-7-days")
async def get_last_7_days_highlight(current_user: User = Depends(identify_user)):
    pass

@accounts_controller.get("/monthly-trend")
async def get_monthly_trend(current_user: User = Depends(identify_user)):
    pass

@accounts_controller.get("/balances", response_model=list[AccountBalance])
async def get_balances(current_user: User = Depends(identify_user)):
    balances: list[AccountBalance] = []

    for account in current_user.accounts:
        account_incomes: float = sum(
            transaction.amount for transaction in account.transactions
            if transaction.type == TransactionType.INCOME.value
        )
        account_outcomes: float = sum(
            transaction.amount for transaction in account.transactions
            if transaction.type == TransactionType.OUTCOME.value
        )

        account_balance: AccountBalance = AccountBalance(
            account=account.name,
            balance=(account.openning_balance + account_incomes) - account_outcomes
        )

        balances.append(account_balance)
    
    return balances

@accounts_controller.get("/list", response_model=list[AccountData])
async def get_accounts(current_user: User = Depends(identify_user)):
    return [ AccountData.from_orm(obj=account) for account in current_user.accounts ]

@accounts_controller.post("/create", response_model=str)
async def create_account(account_data: AccountData, current_user: User = Depends(identify_user), session: Session = Depends(define_local_session)):
    account: Account = Account(
        user=current_user,
        name=account_data.name,
        currency=account_data.currency,
        openning_balance=account_data.openning_balance
    )

    session.add(account)
    session.commit()

    return "Account was created"

@accounts_controller.put("/update", response_model=str)
async def update_account(account_data: AccountData, current_user: User = Depends(identify_user), session: Session = Depends(define_local_session)):
    account: Account | None = session.query(Account).filter(
        Account.id == account_data.id,
        Account.id.in_(account.id for account in current_user.accounts)
    ).one_or_none()

    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account with given `id` was found")

    account.name = account_data.name
    account.currency = account_data.currency
    account.openning_balance = account_data.openning_balance

    session.commit()

    return "Account was updated"

@accounts_controller.delete("/delete", response_model=str)
async def delete_account(id: int, current_user: User = Depends(identify_user), session: Session = Depends(define_local_session)):
    account: Account | None = session.query(Account).filter(
        Account.id == id,
        Account.id.in_(account.id for account in current_user.accounts)
    ).one_or_none()

    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account with given `id` was found")

    session.delete(account)
    session.commit()

    return "Account was deleted"
