from typing import Any

from fastapi import status
from httpx import AsyncClient, Response
from pytest import mark, param

from core.databases.models.utilities.types import TransactionType
from tests.base.router_endpoint_base_test_class import (
    RouterEndpointBaseTestClass,
)


@mark.anyio
async def test_get_summary(test_client: AsyncClient) -> None:
    response: Response = await test_client.get('/trend/summary')

    assert response.status_code == status.HTTP_200_OK, response.text
    assert isinstance(response.json(), list)
    assert len(response.json()) == 3

@mark.anyio
async def test_get_monthly_trend(
    test_client: AsyncClient,
    current_month_days_number: int,
) -> None:
    response: Response = await test_client.get('/trend/current-month')

    assert response.status_code == status.HTTP_200_OK, response.text
    assert isinstance(response.json(), list)
    assert len(response.json()) == current_month_days_number


class TestGetLastNDaysHighlight(RouterEndpointBaseTestClass, http_method='GET', endpoint='/trend/last-n-days'):
    @mark.parametrize('test_n_days', (
        param(4),
        param(None, id='default'),
        param(14),
    ))
    @mark.parametrize('test_type', (
        TransactionType.INCOME.value,
        TransactionType.OUTCOME.value,
        TransactionType.TRANSFER.value,
    ))
    @mark.anyio
    async def test_with_correct_data(
        self,
        test_client: AsyncClient,
        test_n_days: int | None,
        test_type: str,
    ) -> None:
        response: Response = await self.request(
            test_client=test_client,
            n_days=test_n_days,
            transaction_type=test_type,
        )

        assert response.status_code == status.HTTP_200_OK, response.text
        assert isinstance(response.json(), list)
        assert len(response.json()) == test_n_days or 7

    @mark.parametrize('test_n_days', (
        param(3, id='lower'),
        param(15, id='greater'),
        param('string'),
    ))
    @mark.anyio
    async def test_with_wrong_data(
        self,
        test_client: AsyncClient,
        test_n_days: Any,
    ) -> None:
        response: Response = await self.request(
            test_client=test_client,
            n_days=test_n_days,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
