"""Build a synthetic ChatGPT share page in the real page's format.

Nothing here comes from a real conversation. The shape copies a real share page
read on 2026-10-15: the conversation sits at
``loaderData["routes/share.$shareId.($action)"].serverResponse.data``, every
object key is an index into the flat array, every string is stored once, null
is -5, and the stream ends with a promise line such as ``P99:[{}]``.

The conversation exercises what a reader can get wrong: a hidden system root, a
reasoning message, a tool message, an edited question whose abandoned branch
must not be read, a heading inside an answer, citation markers, a code message,
and a voice turn whose text is an audio transcription.

Regenerate the committed page with ``python tests/fixture_share.py``; a test
fails when the two differ.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "share-page.html"
SHARE_ID = "00000000-0000-4000-8000-000000000001"
CITE = "\ue200cite\ue202turn0search0\ue202turn0search3\ue201"


class Encoder:
    """Flatten a value into a turbo-stream array, storing each scalar once."""

    def __init__(self) -> None:
        self.arr: list[Any] = []
        self.scalars: dict[tuple[type, Any], int] = {}

    def add(self, value: Any) -> int:
        if value is None:
            return -5
        if isinstance(value, dict):
            index = len(self.arr)
            self.arr.append(None)
            self.arr[index] = {f"_{self.add(key)}": self.add(item) for key, item in value.items()}
            return index
        if isinstance(value, list):
            index = len(self.arr)
            self.arr.append(None)
            self.arr[index] = [self.add(item) for item in value]
            return index
        key = (type(value), value)
        if key not in self.scalars:
            self.scalars[key] = len(self.arr)
            self.arr.append(value)
        return self.scalars[key]


def node(
    node_id: str, parent: str | None, children: list[str], role: str | None = None, **content: Any
) -> dict:
    message = None
    if role is not None:
        message = {
            "id": node_id,
            "author": {"role": role, "metadata": {}},
            "create_time": 1792050000.5,
            "content": content,
            "status": "finished_successfully",
            "metadata": {"model_slug": "gpt-test"} if role == "assistant" else {},
        }
    out: dict[str, Any] = {"id": node_id, "message": message, "children": children}
    if parent is not None:
        out["parent"] = parent
    return out


def conversation() -> dict:
    nodes = [
        node("root", None, ["sys"]),
        node("sys", "root", ["u1"], "system", content_type="text", parts=["You are ChatGPT."]),
        node("u1", "sys", ["think"], "user", content_type="text", parts=["How do I list files?"]),
        node(
            "think", "u1", ["a1"], "assistant", content_type="thoughts", thoughts=[{"content": "Easy one."}]
        ),
        node(
            "a1",
            "think",
            ["old", "u2"],
            "assistant",
            content_type="text",
            parts=[f"## Steps\n\nUse `ls`.{CITE}"],
        ),
        node("old", "a1", ["old-a"], "user", content_type="text", parts=["An abandoned question"]),
        node("old-a", "old", [], "assistant", content_type="text", parts=["An abandoned answer"]),
        node("u2", "a1", ["tool"], "user", content_type="text", parts=["And hidden files?"]),
        node("tool", "u2", ["code"], "tool", content_type="text", parts=["search results"]),
        node("code", "tool", ["voice"], "assistant", content_type="code", text="ls -a"),
        node(
            "voice",
            "code",
            [],
            "assistant",
            content_type="multimodal_text",
            parts=[
                {
                    "content_type": "audio_transcription",
                    "text": " That shows dotfiles too.",
                    "direction": "out",
                },
                {"content_type": "audio_asset_pointer", "asset_pointer": "sediment://x"},
            ],
        ),
    ]
    return {
        "title": "Listing files",
        "mapping": {n["id"]: n for n in nodes},
        "current_node": "voice",
        "is_public": True,
    }


def build_html() -> str:
    page = {
        "loaderData": {
            "root": {"authStatus": "logged_out"},
            "routes/share.$shareId.($action)": {
                "sharedConversationId": SHARE_ID,
                "serverResponse": {"type": "data", "data": conversation()},
            },
        },
        "actionData": None,
        "errors": None,
    }
    encoder = Encoder()
    encoder.add(page)
    payload = json.dumps(encoder.arr, ensure_ascii=False, separators=(",", ":"))
    # The real page sends the payload in one call; splitting it proves chunks are joined.
    middle = len(payload) // 2
    chunks = [payload[:middle], payload[middle:] + "\n", "P99:[{}]\n"]
    scripts = "".join(
        f"<script>window.__reactRouterContext.streamController.enqueue({json.dumps(c)});</script>"
        for c in chunks
    )
    return f"<!DOCTYPE html><html><head><title>Listing files</title></head><body>{scripts}</body></html>\n"


if __name__ == "__main__":
    FIXTURE.parent.mkdir(exist_ok=True)
    FIXTURE.write_text(build_html(), encoding="utf-8")
