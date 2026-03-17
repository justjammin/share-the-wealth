"""
AI insights routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from share_the_wealth.api.deps import mirror_state
from share_the_wealth.api.services import ContextBuilder
from share_the_wealth.ai import AIAnalyst

router = APIRouter(prefix="/api/ai", tags=["ai"])
_context_builder = ContextBuilder(mirror_state)
_analyst = AIAnalyst()


@router.post("/analyze")
def analyze():
    context = _context_builder.build()
    return {"insight": _analyst.analyze_portfolio(context)}


class ChatRequest(BaseModel):
    messages: list[dict]
    question: str


@router.post("/chat")
def chat(body: ChatRequest):
    context = _context_builder.build()
    return {"reply": _analyst.chat(context, body.messages, body.question)}
