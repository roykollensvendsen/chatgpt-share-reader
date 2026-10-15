# chatgpt-share-reader

Read the full text of a shared ChatGPT conversation link, as an agent skill and a command.

A ChatGPT share page (`https://chatgpt.com/share/<id>`) looks empty to a plain HTTP fetch,
and its backend API answers 403 without a browser session. So an agent that is handed such
a link usually gives up, or reads only the last message and decides that is all there is.
In fact the whole conversation is in the page, packed into React Router's "turbo-stream"
format. This project decodes it, using only the Python standard library and no login.

It comes in two forms:

- **An agent skill** in [`skill/chatgpt-share-reader/`](skill/chatgpt-share-reader/SKILL.md):
  a `SKILL.md` plus one standalone script. Any harness that reads skills from
  `~/.agents/skills` can use it, for example DeepSeek Harness and OpenCode.
- **A command**, `chatgpt-share-reader read`, for using it yourself.

## Install the skill

<!-- not run: it writes into the reader's home directory -->
```bash
git clone https://github.com/roykollensvendsen/chatgpt-share-reader ~/src/chatgpt-share-reader
mkdir -p ~/.agents/skills
ln -s ~/src/chatgpt-share-reader/skill/chatgpt-share-reader ~/.agents/skills/chatgpt-share-reader
```

The symbolic link means a `git pull` updates the skill. To install by copying instead, copy
the `skill/chatgpt-share-reader` folder. It needs nothing else from the repository.

## Use the command

Pass a share URL, a bare share ID, or a share page saved as HTML. Here are the first two of
five messages in the synthetic page the tests use:

```console
$ chatgpt-share-reader read tests/fixtures/share-page.html | head -n 17
# Listing files

Source: https://chatgpt.com/share/00000000-0000-4000-8000-000000000001 · 5 messages

---

**[1] USER:**

How do I list files?

---

**[2] CHATGPT:**

## Steps

Use `ls`.
```

`--format json` prints the messages as data, `--include-hidden` keeps the system, tool and
reasoning messages the share page hides, and `-o FILE` writes to a file.

## When ChatGPT changes the page

The format is undocumented and can change without notice. When it does, the reader stops
with `error: no conversation (mapping/current_node) on the page`. The format notes at the end
of the [skill](skill/chatgpt-share-reader/SKILL.md) explain the payload well enough to patch
the decoder. An issue with a share link that shows the problem is welcome.

## The gates

Every one of these runs in continuous integration, and all of them run here:

```console
$ uv run ruff check .
All checks passed!
```

<!-- not run: the workflow runs each of these; nesting them here would run the suite inside itself -->
```bash
uv run ruff format --check .   # layout
uv run mypy src                # types
uv run pytest -q               # behaviour
python scripts/mutate.py       # that each rule's own test can fail
```

`CONTRIBUTING.md` says what each one is for, and
[`decisions/`](decisions/README.md) records the choices that shaped them,
including how a change is made here.

## Licence

MIT. See [LICENSE](LICENSE).
