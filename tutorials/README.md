# Backfield tutorials

A guided introduction to the Backfield public API, from your first authenticated call to applied newsroom queries.

These tutorials are [marimo](https://marimo.io/) notebooks — reactive Python notebooks stored as `.py` files.

## Prerequisites

- Python 3.11+
- A Backfield project API key

## Setup

From the repo root:

```bash
pip install -r requirements.txt
cp .env.example .env
# set BACKFIELD_PROJECT_API_KEY in .env
```

## Running a tutorial

```bash
marimo edit tutorials/101_hello_backfield.py
```

This opens the notebook in your browser. You can also paste a key into the password field in 101 if you have not exported one.

## Tutorials

### Basics (1xx)

| # | Notebook | What you'll learn |
|---|----------|-------------------|
| 101 | [Hello Backfield](101_hello_backfield.py) | Auth, project metadata, and a first article search |

Work through them in order — each builds on concepts from the previous one.
