from __future__ import annotations

from fastapi import APIRouter, HTTPException

from netframework_core.exceptions import NotFoundError
from order_service.application.dto import CreateOrderRequest, OrderResponse
from order_service.application.services import OrderApplicationService


def create_router(service: OrderApplicationService) -> APIRouter:
    router = APIRouter(prefix="/orders", tags=["orders"])

    @router.post("", response_model=OrderResponse, status_code=201)
    async def create_order(request: CreateOrderRequest) -> OrderResponse:
        return await service.create_order(request)

    @router.get("/{order_id}", response_model=OrderResponse)
    async def get_order(order_id: str) -> OrderResponse:
        try:
            return await service.get_order(order_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("", response_model=list[OrderResponse])
    async def list_orders(limit: int = 100, offset: int = 0) -> list[OrderResponse]:
        return await service.list_orders(limit=limit, offset=offset)

    return router
