# Backfield Cookbook

Tutorials that show how to use the [Backfield public API](https://docs.backfield.news) on real newsroom problems.

These are [marimo](https://marimo.io/) notebooks — reactive Python files, not a packaged SDK. You talk to the API with `httpx`.

## Prerequisites

- Python 3.11+
- A project API key for the demo (or your own) Backfield project

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `BACKFIELD_PROJECT_API_KEY`. The defaults point at the public demo:

```bash
BACKFIELD_BASE_URL=https://api.demo.backfield.news
BACKFIELD_PROJECT_SLUG=workbooks
BACKFIELD_PROJECT_API_KEY=
```

## Run a tutorial

```bash
marimo edit tutorials/101_hello_backfield.py
```

See [tutorials/README.md](tutorials/README.md) for the full list.

## Tests

```bash
pytest
```
