# Backfield Cookbook

Learn how to use the [Backfield API](https://docs.backfield.news) by working
through practical newsroom examples.

The tutorials use a sample of Guardian articles to explore questions such as:

- What stories mention Minnesota?
- What people, organizations, and places appear in an article?
- How can structured reporting data support new products and research?

Each tutorial is an interactive [marimo](https://marimo.io/) notebook. The
Python is intentionally short and visible: you will see the HTTP requests,
parameters, and responses rather than rely on a hidden SDK.

## Get started

You will need Python 3.11 or newer and a Backfield project API key.

Create a virtual environment and install the notebook dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and add your API key:

```bash
BACKFIELD_PROJECT_API_KEY=your-key-here
```

Then launch the first tutorial:

```bash
marimo edit tutorials/101_hello_backfield.py
```

Marimo will open the notebook in your browser. Run the cells from top to bottom,
experiment with the queries, and change values to see how the results respond.

## Tutorials

- **[101: Hello Backfield](tutorials/101_hello_backfield.py)** — Learn how to
  authenticate, inspect project metadata, search for articles, and retrieve one
  article's full details.  
  [Open 101 in molab](https://molab.marimo.io/github/localangle/backfield-cookbook/blob/main/tutorials/101_hello_backfield.py)

See the [tutorial guide](tutorials/README.md) as more examples are added.

## About this repository

This is a collection of teaching notebooks, not a Python package or SDK. The
tutorials call the public API directly with `httpx`, so the code can be adapted
to a script, application, or another notebook.

To verify that the notebooks load correctly:

```bash
pytest
```
