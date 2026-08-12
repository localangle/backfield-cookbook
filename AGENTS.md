# Agent notes

This repo is a set of marimo tutorials that call the Backfield public API. It is not an SDK and should not grow a pip-installable package.

## Tutorials

- Live under `tutorials/` as numbered marimo notebooks (`101_…`, `201_…`).
- Work through them in order. Each notebook should build on the previous one.
- Teaching cells use `@app.cell(hide_code=True)` and `mo.md(...)`.
- Code cells stay short and runnable.
- End each notebook with a “Next steps” cell that links to the following tutorial.
- Link concepts, endpoints, parameters, and conventions to the most specific relevant page on `docs.backfield.news` wherever possible.

Do not invent endpoints, query parameters, or response fields. The contract is `/public/v1` as documented at https://docs.backfield.news and served from `{BASE_URL}/public/v1/openapi.json`.

## Writing style

- Write for a reasonably technical reader, but use plain language.
- Explain unfamiliar terms when they first appear.
- Prefer short sentences and concrete examples.
- Overdocument rather than underdocument. Add comments before code whose purpose may not be immediately obvious.
- Function docstrings should explain what the function does, its arguments, its return value, and any behavior a reader needs to understand.
- Comments should explain **why** a line or block exists, not merely repeat its syntax.

## Readability over correctness

Tutorials are teaching material, not production clients.

- Optimize for **readability**. Prefer obvious code over defensive error handling.
- Skip elaborate try/except, path normalization, and custom error classes unless the tutorial is *about* that topic.
- `response.raise_for_status()` is enough for failures.
- Prefer direct key access (`project["stats"]`) over chains of `.get(...) or {}` when the happy path is the point.
- Demo constants (`BASE_URL`, `PROJECT_SLUG`) can be fixed strings in the notebook. Do not build a config layer.

## API calls (style)

Prefer **visible HTTP** over a shared client library.

- Do **not** put API helpers in `lib/` or import a `BackfieldClient`.
- A tiny transparent `get` near the top of the notebook is fine — keep it to a few lines (request, raise, return JSON). Or call `httpx` / `requests` inline.
- Readers should see the URL, Bearer header, and JSON handling without jumping to another module.
- It is fine to repeat a short `get` across tutorials; clarity beats DRY here.

## Environment

- `BACKFIELD_PROJECT_API_KEY` is required (paste into the notebook UI or set in `.env`).
- Tutorials may hardcode the demo `BASE_URL` and `PROJECT_SLUG`.

Copy `.env.example` to `.env` for local work. Never commit `.env` or any `bfk_` secret.

## Tests

`tests/test_tutorials.py` checks that every `tutorials/*.py` loads as a marimo app and that the committed tree contains no `bfk_` keys. Do not add live API calls to the default test run.
