# Changelog

Every release, what changed in it, and why. Dates are the tag's date. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions follow [semantic versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- The reader: decodes the turbo-stream payload in a ChatGPT share page and prints
  the shared branch of the conversation as Markdown or JSON. It accepts a URL, a bare
  share ID or a saved page, and needs only the standard library.
- The agent skill, `skill/chatgpt-share-reader/`, which ships the reader as a
  standalone script.
- The command `chatgpt-share-reader read`.
