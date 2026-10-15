# ADR-CSR-001: The skill ships a byte-identical copy of the module

## Status

Accepted by Roy Kollen Svendsen, 2026-10-15.

## Context

The reader has two audiences. An agent loads the skill from a folder, such as
`~/.agents/skills/chatgpt-share-reader`, and runs a script in it. It cannot be expected to
have installed a Python package first, and the folder is often copied on its own without the
rest of the repository. A person wants a normal command with tests, types and linting behind
it.

## Options considered

- **The script imports the package.** The skill would then fail wherever the package is not
  installed, which is most places a skill is copied to.
- **The script finds `src/` relative to itself.** This works for a symbolic link into a
  clone. It breaks as soon as the skill folder is copied without the repository.
- **A symbolic link from the skill folder into `src/`.** Git stores it, but copying the
  folder copies a link that points nowhere. Some installers do not follow links either.
- **Two independent scripts.** They would drift apart, and the skill would rot first, since
  nothing tests it.
- **One module, also stored as a byte-for-byte copy in the skill folder, with a test that
  fails when the two differ.** This is the option chosen.

## Decision

`src/chatgpt_share_reader/share.py` is the source. It uses only the standard library and
runs as a script. `skill/chatgpt-share-reader/scripts/read_chatgpt_share.py` is an exact
copy of it. `test_the_skill_script_is_the_module` fails when the two differ, and its message
gives the `cp` command that fixes the difference. A second test runs the copy in an isolated
interpreter, with the package out of reach.

## Consequences

- The skill folder is self-contained and works when copied anywhere.
- Every change to the reader has to be copied too. The test makes forgetting to do so loud
  rather than silent, but it is still a manual step.
- The module may never import anything outside the standard library. That rules out
  `requests`, an HTML parser and the like, even where they would make the code shorter.

## Related

- [`skill/chatgpt-share-reader/SKILL.md`](../skill/chatgpt-share-reader/SKILL.md)
- [`tests/test_share.py`](../tests/test_share.py)
