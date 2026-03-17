"""
Application state and mirror persistence.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class MirrorState:
    def __init__(self, path: Path | None = None):
        self._path = path or PROJECT_ROOT / "mirror_state.json"
        self._data: dict = {"politicians": [], "funds": []}

    def load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except Exception:
                pass

    def save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2))
        except Exception:
            pass

    @property
    def politicians(self) -> list[str]:
        return self._data.get("politicians", [])

    @property
    def funds(self) -> list[str]:
        return self._data.get("funds", [])

    def toggle_politician(self, name: str) -> list[str]:
        arr = self._data.get("politicians", [])
        if name in arr:
            arr = [x for x in arr if x != name]
        else:
            arr = arr + [name]
        self._data["politicians"] = arr
        self.save()
        return arr

    def toggle_fund(self, name: str) -> list[str]:
        arr = self._data.get("funds", [])
        if name in arr:
            arr = [x for x in arr if x != name]
        else:
            arr = arr + [name]
        self._data["funds"] = arr
        self.save()
        return arr

    def toggle(self, type_: str, name: str) -> dict:
        if type_ == "politicians":
            self._data["politicians"] = self.toggle_politician(name)
        else:
            self._data["funds"] = self.toggle_fund(name)
        return dict(self._data)

    def get(self) -> dict:
        return dict(self._data)
