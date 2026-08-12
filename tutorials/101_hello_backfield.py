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

    Developers can use its [**public API**](https://docs.backfield.news/api/) to build products and services based on that data. These tutorials are meant to showcase several examples of things newsrooms might build and how they can use Backfield data to approach them.

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

    Public routes expect a [**project API key**](https://docs.backfield.news/api/authentication/) as a Bearer token:

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

    # Load values from a local .env file into the process environment.
    # This lets you keep the API key outside the notebook.
    load_dotenv()

    # These tutorials all use the same public demo project.
    BASE_URL = "https://api.demo.backfield.news"
    PROJECT_SLUG = "workbooks"

    # Prefer a key pasted into the notebook. If that field is empty, use the
    # BACKFIELD_PROJECT_API_KEY value loaded from .env.
    key = api_key.value or os.environ.get("BACKFIELD_PROJECT_API_KEY", "")

    # Pause dependent cells until the reader provides a key.
    mo.stop(not key, "Paste an API key above, or set BACKFIELD_PROJECT_API_KEY in .env")

    def get(path, **params):
        """Send an authenticated GET request to the Backfield public API.

        Args:
            path: The part of the API path after ``/public/v1``. For example,
                ``/projects/workbooks``.
            **params: Optional query-string parameters such as ``q="Minnesota"``
                or ``limit=5``.

        Returns:
            The JSON response converted to Python dictionaries and lists.

        This helper deliberately stays small so each tutorial keeps the HTTP
        request visible. ``raise_for_status()`` stops the notebook and shows the
        HTTP error if Backfield returns an unsuccessful response.
        """
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

    [`GET /public/v1/projects/{slug}`](https://docs.backfield.news/api/projects/get-project/) is an easy way to confirm that the key works. The response includes the project name, its assigned Stylebook, and counts of articles, mentions, and images.
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

    Keyword search uses [`GET /public/v1/projects/{slug}/articles/search`](https://docs.backfield.news/api/articles/search/).

    - `q` matches headline, body, and URL
    - [`limit` and `offset`](https://docs.backfield.news/api/conventions/pagination/) paginate

    Returned items include `headline`, `pub_date`, `url`, and a short `preview`. Full body text can be returned via the article detail route using `include=text`.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get):
    # Ask for only five results so the notebook output stays easy to scan.
    search = get(f"/projects/{PROJECT_SLUG}/articles/search", q="Minnesota", limit=5)
    items = search["items"]

    # The pagination object tells us how many matches exist across all pages.
    print(f"{len(items)} of {search['pagination']['total']}")
    for item in items:
        print(f"- {item['headline']} ({item['pub_date']})")
    return (items,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Article detail

    Search hits are summaries. [`GET /public/v1/projects/{slug}/articles/{id}`](https://docs.backfield.news/api/articles/get-article/) returns one article.

    Pass `include=text` to get the full body (without it you only get `preview`).
    """)
    return


@app.cell
def _(PROJECT_SLUG, get, items):
    # Search results include the numeric article id needed by the detail route.
    article_id = items[0]["id"]
    article = get(
        f"/projects/{PROJECT_SLUG}/articles/{article_id}",
        include="text",
    )

    print(article["headline"])
    print(article["pub_date"])
    print(article["url"])
    # Show only the opening 500 characters so the full story does not take
    # over the notebook output.
    print(article["text"][:500])
    return (article_id,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Entities in an article

    Backfield identifies the people, organizations, and locations mentioned in each article. Each entity type has its own endpoint:

    - [`/people`](https://docs.backfield.news/api/articles/hub/people/) includes details such as a person's title and affiliation.
    - [`/organizations`](https://docs.backfield.news/api/articles/hub/organizations/) includes the type of organization.
    - [`/locations`](https://docs.backfield.news/api/articles/hub/locations/) includes map-friendly addresses and geometry when available.

    These endpoints are useful when an application needs one particular type of entity.
    """)
    return


@app.cell
def _(PROJECT_SLUG, article_id, get):
    # Entity-specific endpoints use the same article id as the detail endpoint.
    people = get(f"/projects/{PROJECT_SLUG}/articles/{article_id}/people", limit=5)
    organizations = get(
        f"/projects/{PROJECT_SLUG}/articles/{article_id}/organizations",
        limit=5,
    )
    locations = get(
        f"/projects/{PROJECT_SLUG}/articles/{article_id}/locations",
        limit=5,
    )

    # Each response is paginated. For this introduction, we print the labels
    # from only the first page of each entity type.
    # Leading underscores keep these temporary loop variables local to this
    # cell, which prevents name collisions with variables in other cells.
    for _heading, _entity_response in (
        ("People", people),
        ("Organizations", organizations),
        ("Locations", locations),
    ):
        print(
            f"\n{_heading} "
            f"({_entity_response['pagination']['total']} total)"
        )
        for _entity in _entity_response["items"]:
            print(f"- {_entity['label']}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Mentions and evidence

    An entity is the person, organization, or place itself. A **mention** describes how that entity appears in a particular article.

    The [`/mentions`](https://docs.backfield.news/api/articles/hub/mentions/) endpoint combines all three entity types into one list. Each mention has a [`nature`](https://docs.backfield.news/api/taxonomy/mention-meta/) describing the entity's role in this particular story. The available natures depend on the entity type.

    A mention may also include an evidence span. Its `mention_text` points back to the relevant text in the article.

    Use this unified endpoint when you want to answer a question such as “What entities appear in this story?” without making separate requests for each type.
    """)
    return


@app.cell
def _(PROJECT_SLUG, article_id, get):
    mentions = get(f"/projects/{PROJECT_SLUG}/articles/{article_id}/mentions")

    print(f"{len(mentions)} mentions")
    # Keep the example compact even when an article contains many mentions.
    for _mention in mentions[:10]:
        _nature = _mention["nature"] or "not set"
        _evidence = _mention["evidence"]

        print(
            f"- {_mention['entity_type']}: {_mention['label']} "
            f"(nature: {_nature})"
        )

        # Evidence can be absent when Backfield has no saved text span for a
        # mention. When present, mention_text is the source text to highlight.
        if _evidence:
            print(f"  Text: {_evidence['mention_text']}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Errors and rate limits

    [API errors](https://docs.backfield.news/api/conventions/errors/) use one envelope:

    ```json
    {"error": {"code": "not_found", "message": "...", "details": null}, "request_id": "..."}
    ```

    Successful responses also send [rate-limit headers](https://docs.backfield.news/api/conventions/rate-limits/). Here's a raw request so you can see them:
    """)
    return


@app.cell
def _(BASE_URL, PROJECT_SLUG, httpx, key):
    # Make this request without the helper because we want both the response
    # body and the HTTP headers. The helper normally returns only JSON.
    response = httpx.get(
        f"{BASE_URL}/public/v1/projects/{PROJECT_SLUG}",
        headers={"Authorization": f"Bearer {key}"},
    )

    # Header names are case-insensitive. A missing header prints as None.
    for header in ("RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset", "X-Request-ID"):
        print(f"{header}: {response.headers.get(header)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    You can authenticate, search articles, retrieve full article details, and inspect the entities and mentions found in a story.

    Future tutorials will build on these calls to search across the whole project and explore canonical entities shared by many articles.
    """)
    return


if __name__ == "__main__":
    app.run()
