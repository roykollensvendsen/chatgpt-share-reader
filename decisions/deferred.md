# What is deliberately not done yet

A thing left undone with no trigger is a thing forgotten. Each row names what
would make it worth doing, so the question comes back on its own rather than
depending on someone remembering it. Nothing enforces a trigger; the list is
read whenever a decision record is written and when a phase ends.

| Not done | The trigger | Why not now |
|---|---|---|
| A coverage threshold in CI | Two months of measured coverage to set it below | A number picked before there is data is a guess with a gate on it |
| A code of conduct and issue templates | A second contributor, or the first outside issue | Boilerplate answering questions nobody has asked |
| A release workflow and publishing | The first release someone outside will install | A published name is claimed and a published version cannot be reused |
| `CODEOWNERS` | A second person who reviews | It would name one person as the owner of everything |
| `pre-commit` as a requirement rather than an option | A second contributor | The gates run in CI, and a hook one person installs is a hook one person maintains |
| A scheduled check against a real share link | A public share link whose content the maintainer controls and is happy to publish, or the first format change that reaches a user before the tests | The tests cannot see a format change, but a live check needs a stable link and goes red for reasons outside the repository (ADR-CSR-002) |
| Listing the skill in skill registries or marketplaces | Someone asks to install it from one | Each registry has its own format to keep in step with |
| Reading private or logged-in conversations | Never by scraping; only if OpenAI publishes an export API | That would need the user's session token, which a skill should not handle |
