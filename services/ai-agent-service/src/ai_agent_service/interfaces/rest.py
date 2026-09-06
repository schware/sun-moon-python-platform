from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ai_agent_service.application.assistant_service import AssistantService


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


def create_router(service: AssistantService) -> APIRouter:
    router = APIRouter(prefix="/assistant", tags=["assistant"])

    @router.post("/ask", response_model=AskResponse)
    async def ask(request: AskRequest) -> AskResponse:
        return AskResponse(answer=await service.ask(request.question))

    return router
