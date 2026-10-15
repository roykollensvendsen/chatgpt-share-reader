"""The share reader, against a synthetic page in the real page's format."""

import json
import pathlib
import subprocess
import sys

import pytest
from fixture_share import FIXTURE, SHARE_ID, build_html

from chatgpt_share_reader import cli, share

ROOT = pathlib.Path(__file__).parent.parent
SKILL_SCRIPT = ROOT / "skill/chatgpt-share-reader/scripts/read_chatgpt_share.py"


@pytest.fixture
def page(tmp_path):
    path = tmp_path / "share.html"
    path.write_text(build_html(), encoding="utf-8")
    return path


def test_reads_the_shared_branch_in_order(page):
    result = share.read_share(str(page))
    assert result["share_id"] == SHARE_ID
    assert result["title"] == "Listing files"
    assert [(m["role"], m["text"]) for m in result["messages"]] == [
        ("user", "How do I list files?"),
        ("assistant", "## Steps\n\nUse `ls`."),
        ("user", "And hidden files?"),
        ("assistant", "```\nls -a\n```"),
        ("assistant", "That shows dotfiles too."),
    ]


def test_an_abandoned_branch_is_not_read(page):
    texts = [m["text"] for m in share.read_share(str(page))["messages"]]
    assert not any("abandoned" in t for t in texts)


def test_hidden_messages_are_left_out(page):
    roles = [m["role"] for m in share.read_share(str(page))["messages"]]
    assert "system" not in roles
    assert "tool" not in roles
    hidden = share.read_share(str(page), include_hidden=True)["messages"]
    assert {"system", "tool"} <= {m["role"] for m in hidden}
    assert "Easy one." in [m["text"] for m in hidden]


def test_object_keys_name_an_entry_in_the_array():
    """The defect that made a first reader see one message out of ninety."""
    arr = [{"_1": 2, "_3": -5}, "role", "user", "parent"]
    assert share.Decoder(arr).ref(0) == {"role": "user", "parent": None}


def test_every_enqueued_chunk_is_joined(page):
    assert len(share.read_share(str(page))["messages"]) == 5


def test_citation_markers_are_removed(page):
    answer = share.read_share(str(page))["messages"][1]["text"]
    assert answer == "## Steps\n\nUse `ls`."
    assert not any("\ue200" <= ch <= "\ue2ff" for ch in answer)


def test_markdown_marks_turns_without_headings_that_collide(page):
    text = share.to_markdown(share.read_share(str(page)))
    assert "· 5 messages" in text
    assert "**[1] USER:**" in text
    assert "**[5] CHATGPT:**" in text
    assert "## Steps" in text


def test_json_output_has_every_message(page, capsys):
    assert cli.main(["read", str(page), "--format", "json"]) == 0
    assert len(json.loads(capsys.readouterr().out)["messages"]) == 5


def test_a_page_with_no_payload_is_an_error(tmp_path, capsys):
    path = tmp_path / "x.html"
    path.write_text("<html>Just a moment...</html>", encoding="utf-8")
    assert cli.main(["read", str(path)]) == 1
    assert "no streamController.enqueue" in capsys.readouterr().err


def test_a_page_with_no_conversation_is_an_error(tmp_path, capsys):
    path = tmp_path / "x.html"
    path.write_text(f"<script>streamController.enqueue({json.dumps('[{}]')})</script>", encoding="utf-8")
    assert cli.main(["read", str(path)]) == 1
    assert "most likely deleted" in capsys.readouterr().err


def test_a_source_without_a_share_id_is_an_error(capsys):
    assert cli.main(["read", "https://example.com/nothing"]) == 1
    assert "no share ID" in capsys.readouterr().err


def test_the_skill_script_is_the_module():
    """The skill ships the module as a standalone file; the two must not drift apart."""
    assert SKILL_SCRIPT.read_bytes() == (ROOT / "src/chatgpt_share_reader/share.py").read_bytes(), (
        "run: cp src/chatgpt_share_reader/share.py " + str(SKILL_SCRIPT.relative_to(ROOT))
    )


def test_the_skill_script_runs_without_the_package_installed(page, tmp_path):
    r = subprocess.run(
        [sys.executable, "-I", str(SKILL_SCRIPT), str(page)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "· 5 messages" in r.stdout


def test_the_committed_fixture_is_current():
    assert FIXTURE.read_text(encoding="utf-8") == build_html(), "run: python tests/fixture_share.py"
