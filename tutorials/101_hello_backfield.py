import marimo

__generated_with = "0.23.16"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Tutorial 101: Hello Backfield

    [Backfield](https://docs.backfield.news) turns stories into structured data, including geocoded locations, people and quotes, organizations, metadata and more.

    Developers can use its **public API** to build products and services based on that data. These tutorials are meant to showcase several examples of things newsrooms might build and how they can use Backfield data to approach them.

    ```
    Your notebook                              Backfield public API
    +-----------------------+                  +---------------------------+
    | Python / httpx        |  ------------->  | /public/v1/projects/...   |
    | Filters and display   |  <-------------  | articles, entities, stats |
    +-----------------------+                  +---------------------------+
    ```

    The tutorials draw from a small subset of articles published by the Guardian between the years of 2016 and 2022. The articles were [distributed for data science research](https://www.kaggle.com/datasets/adityakharosekar2/guardian-news-articles) on the platform Kaggle. We're using about 250 of them for these tutorials.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Authentication

    Public routes expect a **project API key** as a Bearer token:

    ```http
    Authorization: Bearer bfk_...
    ```

    The key is bound to one project. These tutorials use the demo project `workbooks`.

    Paste a key below, or set `BACKFIELD_PROJECT_API_KEY` in `.env`.
    """)
    return


@app.cell
def _(mo):
    api_key = mo.ui.text(kind="password", label="Paste your Backfield project API key")
    api_key  # noqa: B018
    return (api_key,)


@app.cell
def _(api_key, mo):
    import os

    import httpx
    from dotenv import load_dotenv

    load_dotenv()

    BASE_URL = "https://api.demo.backfield.news"
    PROJECT_SLUG = "workbooks"
    key = api_key.value or os.environ.get("BACKFIELD_PROJECT_API_KEY", "")

    mo.stop(not key, "Paste an API key above, or set BACKFIELD_PROJECT_API_KEY in .env")

    def get(path, **params):
        '''
        Simple helper function to make API requests.
        '''
        response = httpx.get(
            f"{BASE_URL}/public/v1{path}",
            params=params,
            headers={"Authorization": f"Bearer {key}"},
        )
        response.raise_for_status()
        return response.json()

    return BASE_URL, PROJECT_SLUG, get, httpx, key


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Project metadata

    `GET /public/v1/projects/{slug}` is an easy way to confirm that the key works. The response includes the project name, its assigned Stylebook, and counts of articles, mentions, and images.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get):
    project = get(f"/projects/{PROJECT_SLUG}")

    print(project["name"], project["slug"])
    print("Stylebook:", project.get("stylebook_name"))
    print("Articles:", project["stats"]["articles"])
    print("Mentions:", project["stats"]["mentions"])
    print("Images:", project["stats"]["images"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Simple article search

    The most familiar way to search articles is by keyword. We'll use that endpoint to begin exploring the data in our Backfield project.

    Keyword search: `GET /public/v1/projects/{slug}/articles/search`.

    - `q` matches headline, body, and URL
    - `limit` / `offset` paginate

    Returned items include `headline`, `pub_date`, `url`, and a short `preview`. Full body text can be returned via the article detail route using `include=text`.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get):
    search = get(f"/projects/{PROJECT_SLUG}/articles/search", q="Minnesota", limit=5)
    items = search["items"]

    print(f"{len(items)} of {search['pagination']['total']}")
    for item in items:
        print(f"- {item['headline']} ({item['pub_date']})")
    return (items,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Article detail

    Search hits are summaries. `GET /public/v1/projects/{slug}/articles/{id}` returns one article.

    Pass `include=text` to get the full body (without it you only get `preview`).
    """)
    return


@app.cell
def _(PROJECT_SLUG, get, items):
    article_id = items[0]["id"]
    article = get(
        f"/projects/{PROJECT_SLUG}/articles/{article_id}",
        include="text",
    )

    print(article["headline"])
    print(article["pub_date"])
    print(article["url"])
    print(article["text"][:500])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Errors and rate limits

    Failures use one envelope:

    ```json
    {"error": {"code": "not_found", "message": "...", "details": null}, "request_id": "..."}
    ```

    Successful responses also send rate-limit headers. Here's a raw request so you can see them:
    """)
    return


@app.cell
def _(BASE_URL, PROJECT_SLUG, httpx, key):
    response = httpx.get(
        f"{BASE_URL}/public/v1/projects/{PROJECT_SLUG}",
        headers={"Authorization": f"Bearer {key}"},
    )
    for header in ("RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset", "X-Request-ID"):
        print(f"{header}: {response.headers.get(header)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    You can authenticate, read project stats, and search articles.

    **Tutorial 102** (not written yet) will take one article id and walk through its mentions, people, organizations, and locations.
    """)
    return


if __name__ == "__main__":
    app.run()
