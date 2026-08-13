# Backfield Cookbook

Learn how to use the [Backfield API](https://docs.backfield.news) by working through practical newsroom examples.

Most tutorials are based on a a [sample of articles from the Guardian](https://www.kaggle.com/datasets/adityakharosekar2/guardian-news-articles) from between 2017 and 2022, which were released on the platform Kaggle for data science research.

Each tutorial is presented in an interactive [marimo](https://marimo.io/) notebook.
You can read the rendered versions without an API key, or open the notebooks in
molab when you want to edit and run them yourself.

## Get started

To run the tutorials locally, you will need Python 3.11 or newer and a Backfield project API key.

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

Marimo will open the notebook in your browser. Run the cells from top to bottom, experiment with the queries, and change values to see how the results respond.

## Tutorials

### Basics (1xx)

| # | Notebook | What you'll learn | Rendered | Try on molab |
|---|----------|-------------------|----------|--------------|
| 101 | [Hello Backfield](tutorials/101_hello_backfield.py) | Authentication, project metadata, article search and detail, entities, and mentions | [View rendered](https://localangle.github.io/backfield-cookbook/101_hello_backfield.html) | [![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/localangle/backfield-cookbook/blob/main/tutorials/101_hello_backfield.py) |

### Simple Applications (2xx)

| # | Notebook | What you'll learn | Rendered | Try on molab |
|---|----------|-------------------|----------|--------------|
| 201 | [Build a coverage map](tutorials/201_h3_coverage_map.py) | Build a simple coverage map using shaded H3 cells. | [View rendered](https://localangle.github.io/backfield-cookbook/201_h3_coverage_map.html) | [![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/localangle/backfield-cookbook/blob/main/tutorials/201_h3_coverage_map.py) |
| 202 | [Explore who appears in coverage](tutorials/202_source_audit.py) | List people, filter by mention nature, and chart one person's mentions over time. | [View rendered](https://localangle.github.io/backfield-cookbook/202_source_audit.html) | [![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/localangle/backfield-cookbook/blob/main/tutorials/202_source_audit.py) |
| 203 | [Build a Minneapolis news feed](tutorials/203_minneapolis_news_feed.py) | Combine keyword, geographic, and entity queries into a deduplicated local feed. | [View rendered](https://localangle.github.io/backfield-cookbook/203_minneapolis_news_feed.html) | [![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/localangle/backfield-cookbook/blob/main/tutorials/203_minneapolis_news_feed.py) |

There is no need to work through the tutorials in order. You can find API documentation [here](https://docs.backfield.news/api/). 

## About this repository

This is meant to be a collection of teaching notebooks and other examples. You can and should adapt them for your own use cases.

To verify that the notebooks load correctly:

```bash
pytest
```

## Questions?

Contact **backfield@localangle.co**.