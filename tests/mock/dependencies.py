from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.sessions import define_postgres_session
from models import User

from .databases import TestPostgresSession


def define_test_postgres_session() -> Generator[TestPostgresSession, None, None]:
    with TestPostgresSession() as test_postgres_session:
        yield test_postgres_session


def identify_test_user(
    # MARK: The original session getter should be used for correct dependency override
    session: Session = Depends(define_postgres_session)
) -> User:
    return session.query(User).\
        filter(User.username == "test-user").\
        one_or_none()