from typing import Protocol, runtime_checkable

from app.llm.schemas import NarrativeTurnRequest, TurnResult


@runtime_checkable
class NarrativeProvider(Protocol):
    async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult: ...
