# ADR-CSR-002: Tests use a synthetic share page, not a real one

## Status

Accepted by Roy Kollen Svendsen, 2026-10-15.

## Context

The reader is only as good as its match with the real page format, and the obvious test
fixture is a saved real share page. But a real page holds a real person's conversation.
The one that prompted this project is a personal one, about setting up a home device with
account passwords. This repository is public. A real page is also about 700 kB, almost all
of it unrelated page chrome.

## Options considered

- **Commit a real page.** This is the most faithful option, but it publishes someone's
  conversation, and nobody can review whether a 700 kB file is safe to publish.
- **Fetch a real page in CI.** This catches format changes, but it needs a stable public link
  that someone controls. It also makes CI red for reasons outside the repository, such as
  rate limits or a deleted link.
- **Commit a synthetic page that reproduces the real format.** This is the option chosen.

## Decision

`tests/fixture_share.py` builds a page from a made-up conversation. It uses the encoding a
real page uses: every key is an index into the array, every string is stored once, the
sentinels are the same, and the conversation sits at the same path. It also covers the cases
a reader gets wrong: a hidden system root, reasoning and tool messages, an abandoned edit
branch, a heading inside an answer, citation markers, a code message and a voice
transcription. The page is committed, so the README example can run against it, and a test
fails when the committed page differs from what the builder produces.

## Consequences

- The tests prove that the decoder handles the format as it was understood on 2026-10-15.
  They cannot notice when ChatGPT changes the format. A real link will be the first thing to
  break, and the fix needs someone to look at a real page again. The deferred list names
  what would make a live check worth adding.
- Making the synthetic page faithful is a claim with no test behind it: the encoder could
  share a misunderstanding with the decoder. It was checked by hand once, by decoding a real
  page (90 visible messages out of 180 nodes) with the same decoder.

## Related

- [`tests/fixture_share.py`](../tests/fixture_share.py)
- [`deferred.md`](deferred.md)
