from typing import Iterable

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.services import CategoryService
from app.utilities.exceptions import CouldNotAccessRecords
from models import Category, Transaction, User
from models.utilities.types import TransactionType


def sum_transactions_of_given_type(
    transactions: Iterable[Transaction],
    transaction_type: TransactionType,
    initial_amount: float = 0,
) -> float:
    return sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.type == transaction_type
        ),
        start=initial_amount,
    )


def get_validated_user_categories_by_ids(
    category_ids: list[int],
    user: User,
    session: Session,
) -> list[Category]:
    category_service: CategoryService = CategoryService(session=session)
    categories: list[Category] = category_service.get_list(
        or_(
            Category.id.in_(category_ids),
            Category.base_category_id.in_(category_ids),
        ),
        Category.user == user,
    )
    bad_category_ids: set[int] = set(category_ids) - {category.id for category in categories}

    if bad_category_ids:
        raise CouldNotAccessRecords(list(bad_category_ids), Category)

    return categories
