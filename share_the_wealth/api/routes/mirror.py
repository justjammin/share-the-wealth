"""
Mirror state routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from share_the_wealth.api.deps import mirror_state

router = APIRouter(prefix="/api", tags=["mirror"])


@router.get("/mirrored")
def get_mirrored():
    return {"mirrored": mirror_state.get()}


class MirrorToggle(BaseModel):
    type: str
    name: str


@router.post("/mirror")
def toggle_mirror(body: MirrorToggle):
    result = mirror_state.toggle(body.type, body.name)
    return {"mirrored": result}
