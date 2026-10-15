#!/usr/bin/env python3
"""Read a public ChatGPT share link and print the conversation.

A share page (chatgpt.com/share/<id>) is server-rendered by React Router, and the
whole conversation is embedded in its HTML as a "turbo-stream" payload, inside
``window.__reactRouterContext.streamController.enqueue("...")`` calls. The payload
is one flat JSON array in which every value appears once and everything else
refers to it by index:

    {"_340": 341}   key = arr[340], value = decode(arr[341])
    [12, 13]        [decode(arr[12]), decode(arr[13])]
    -5, -7          null, undefined (other negatives are NaN, infinities, -0)

A decoder that skips the ``_N`` keys finds almost nothing and concludes that only
the last message is on the page. No login and no backend API are needed.

This file is self-contained and uses only the standard library, so the agent
skill can run it directly:

    read_chatgpt_share.py URL_OR_ID_OR_HTML_FILE [--format markdown|json]
                          [--include-hidden] [-o FILE]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
SHARE_ID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
ENQUEUE_RE = re.compile(r'streamController\.enqueue\(("(?:[^"\\]|\\.)*")\)')
SENTINELS: dict[int, Any] = {
    -1: None,  # hole
    -2: math.nan,
    -3: -math.inf,
    -4: -0.0,
    -5: None,  # null
    -6: math.inf,
    -7: None,  # undefined
}
# Inline citations are wrapped in private-use characters and render as junk.
CITE_RE = re.compile("\ue200(?:cite|filecite|navlist|image_group|entity)[^\ue201]*\ue201")
PRIVATE_USE_RE = re.compile("[\ue200-\ue2ff]")
HIDDEN_CONTENT_TYPES = frozenset(
    {"thoughts", "reasoning_recap", "model_editable_context", "user_editable_context"}
)
SILENT_PART_TYPES = frozenset({"audio_asset_pointer", "real_time_user_audio_video_asset_pointer"})
MAX_SEARCH_DEPTH = 40


class ShareError(Exception):
    """The page could not be read as a ChatGPT share."""


def load_html(source: str) -> tuple[str, str]:
    """Return ``(share_id, html)`` for a URL, a bare share ID, or a saved HTML file."""
    path = Path(source)
    if path.suffix.lower() in {".html", ".htm"} and path.is_file():
        html = path.read_text(encoding="utf-8")
        found = SHARE_ID_RE.search(html)
        return (found.group(0) if found else path.stem), html
    found = SHARE_ID_RE.search(source)
    if not found:
        msg = f"no share ID in {source!r}; expected https://chatgpt.com/share/<id>"
        raise ShareError(msg)
    share_id = found.group(0)
    request = urllib.request.Request(
        f"https://chatgpt.com/share/{share_id}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return share_id, response.read().decode("utf-8", "replace")


def flat_array(html: str) -> list[Any]:
    """Extract the turbo-stream payload from a share page as its flat array."""
    chunks = ENQUEUE_RE.findall(html)
    if not chunks:
        msg = (
            "no streamController.enqueue(...) on the page: not a share page, or a challenge "
            "or error page was served instead"
        )
        raise ShareError(msg)
    # RULE: every enqueued chunk is joined
    stream = "".join(json.loads(chunk) for chunk in chunks)
    # The first line is the payload; later lines resolve promises, like "P4809:[{}]".
    payload = json.loads(stream.split("\n", 1)[0])
    if not isinstance(payload, list):
        msg = "the stream payload is not an array"
        raise ShareError(msg)
    return payload


class Decoder:
    """Resolve index references in a flat turbo-stream array into plain values."""

    def __init__(self, arr: list[Any]) -> None:
        """Wrap the flat array; decoded values are memoised, so shared nodes stay shared."""
        self.arr = arr
        self.memo: dict[int, Any] = {}

    def ref(self, index: int) -> Any:  # noqa: ANN401 - the payload is untyped JSON
        """Decode the value stored at ``index``."""
        if index < 0:
            return SENTINELS.get(index)
        if index in self.memo:
            return self.memo[index]
        value = self.arr[index]
        if isinstance(value, dict):
            obj: dict[str, Any] = {}
            self.memo[index] = obj
            for key, ref in value.items():
                # RULE: object keys name an entry in the array
                name = self.arr[int(key[1:])] if key.startswith("_") else key
                obj[name] = self.ref(ref)
            return obj
        if isinstance(value, list):
            if value and isinstance(value[0], str):  # a typed value, like ["D", ts]
                self.memo[index] = value
                return value
            items: list[Any] = []
            self.memo[index] = items
            items.extend(self.ref(ref) for ref in value)
            return items
        self.memo[index] = value
        return value


def find_conversation(node: Any, depth: int = 0) -> dict[str, Any] | None:  # noqa: ANN401
    """Find the dict that holds ``mapping`` and ``current_node``."""
    if depth > MAX_SEARCH_DEPTH:
        return None
    children: list[Any] = []
    if isinstance(node, dict):
        if "mapping" in node and "current_node" in node:
            return node
        children = list(node.values())
    elif isinstance(node, list):
        children = node
    for child in children:
        found = find_conversation(child, depth + 1)
        if found is not None:
            return found
    return None


def clean(text: str) -> str:
    """Remove citation markers and surrounding whitespace."""
    # RULE: citation markers are removed
    return PRIVATE_USE_RE.sub("", CITE_RE.sub("", text)).strip()


def part_text(part: Any) -> str:  # noqa: ANN401
    """Return the readable text of one entry in ``content.parts``."""
    if isinstance(part, str):
        return part
    if not isinstance(part, dict):
        return ""
    kind = part.get("content_type")
    if kind in SILENT_PART_TYPES:
        return ""
    if kind == "image_asset_pointer":
        return "[image]"
    text = part.get("text")
    if isinstance(text, str):
        return text
    return f"[{kind or 'unknown part'}]"


def message_text(message: dict[str, Any]) -> str:
    """Return the readable text of a message, whatever its content type."""
    content = message.get("content") or {}
    kind = content.get("content_type")
    parts = content.get("parts")
    if isinstance(parts, list):
        return "\n".join(t for t in (part_text(p) for p in parts) if t)
    if kind in {"code", "execution_output"}:
        return f"```\n{content.get('text', '')}\n```"
    if kind == "thoughts":
        return "\n".join(t.get("content", "") for t in content.get("thoughts", []) if isinstance(t, dict))
    for field in ("text", "result"):
        if isinstance(content.get(field), str):
            return str(content[field])
    return ""


def is_hidden(message: dict[str, Any]) -> bool:
    """Whether the share page itself would hide this message from a reader."""
    role = (message.get("author") or {}).get("role")
    metadata = message.get("metadata") or {}
    kind = (message.get("content") or {}).get("content_type")
    return bool(
        role in {"system", "tool"}
        or metadata.get("is_visually_hidden_from_conversation")
        or kind in HIDDEN_CONTENT_TYPES
    )


def messages(conversation: dict[str, Any], *, include_hidden: bool = False) -> list[dict[str, Any]]:
    """Return the shared branch, oldest first: walk up from ``current_node``, then reverse."""
    mapping: dict[str, Any] = conversation["mapping"]
    node_id = conversation["current_node"]
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    while node_id in mapping and node_id not in seen:
        seen.add(node_id)
        chain.append(mapping[node_id])
        node_id = mapping[node_id].get("parent")
    out = []
    for node in reversed(chain):
        message = node.get("message")
        # RULE: hidden messages are left out
        if not message or (is_hidden(message) and not include_hidden):
            continue
        text = clean(message_text(message))
        if text:
            out.append(
                {
                    "role": (message.get("author") or {}).get("role"),
                    "content_type": (message.get("content") or {}).get("content_type"),
                    "text": text,
                    "create_time": message.get("create_time"),
                    "model": (message.get("metadata") or {}).get("model_slug"),
                }
            )
    return out


def read_share(source: str, *, include_hidden: bool = False) -> dict[str, Any]:
    """Return ``{share_id, title, messages}`` for a URL, share ID or saved share page."""
    share_id, html = load_html(source)
    conversation = find_conversation(Decoder(flat_array(html)).ref(0))
    if conversation is None:
        msg = (
            "no conversation (mapping/current_node) on the page: the link is most likely deleted, "
            "private or mistyped. If it opens in a browser, the page format has changed."
        )
        raise ShareError(msg)
    return {
        "share_id": share_id,
        "title": conversation.get("title") or "",
        "messages": messages(conversation, include_hidden=include_hidden),
    }


def to_markdown(share: dict[str, Any]) -> str:
    """Render a share as Markdown, one numbered block per message."""
    title = share["title"] or f"ChatGPT share {share['share_id']}"
    msgs = share["messages"]
    lines = [
        f"# {title}",
        "",
        f"Source: https://chatgpt.com/share/{share['share_id']} · {len(msgs)} messages",
        "",
    ]
    # Messages carry their own headings, so a turn is marked by a rule and a bold
    # label rather than a heading that would collide with them.
    for number, message in enumerate(msgs, 1):
        who = {"user": "USER", "assistant": "CHATGPT"}.get(message["role"], str(message["role"]).upper())
        lines += ["---", "", f"**[{number}] {who}:**", "", message["text"], ""]
    return "\n".join(lines)


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    """Return the argument parser shared by the script and the ``read`` verb."""
    parser = argparse.ArgumentParser(
        prog=prog, description="Print the conversation behind a ChatGPT share link."
    )
    parser.add_argument("source", help="share URL, bare share ID, or a saved share page (.html)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument(
        "--include-hidden", action="store_true", help="keep system, tool and reasoning messages"
    )
    parser.add_argument("-o", "--output", help="write to this file instead of standard output")
    return parser


def main(argv: list[str] | None = None, prog: str | None = None) -> int:
    """Run the reader. Returns 0 on success and 1 when the share cannot be read."""
    args = build_parser(prog).parse_args(argv)
    try:
        share = read_share(args.source, include_hidden=args.include_hidden)
    except (ShareError, OSError, ValueError) as error:
        sys.stderr.write(f"error: {error}\n")
        return 1
    if args.format == "json":
        text = json.dumps(share, ensure_ascii=False, indent=2) + "\n"
    else:
        text = to_markdown(share)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        sys.stderr.write(f"wrote {len(share['messages'])} messages to {args.output}\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
