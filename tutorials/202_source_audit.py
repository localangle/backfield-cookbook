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
    # Tutorial 202: Audit the people used as sources

    Newsrooms often want to understand whose voices appear in their coverage. In this tutorial, we will build a simple source audit that answers two questions:

    1. Which people are referenced as sources most often?
    2. When and where was the most frequent source mentioned?

    Backfield stores a person's role in each story as the mention's [`nature`](https://docs.backfield.news/api/taxonomy/mention-meta/people/). A person with `nature=source` was quoted or provided information in that article.

    We will count those source mentions across the project, rank the people, and display every mention of the top source in a GitHub-style timeline.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Connect to Backfield

    Paste a [project API key](https://docs.backfield.news/api/authentication/) below, or set `BACKFIELD_PROJECT_API_KEY` in `.env`.
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

    # Load the API key from .env when the notebook field is empty.
    load_dotenv()

    BASE_URL = "https://api.demo.backfield.news"
    PROJECT_SLUG = "workbooks"
    key = api_key.value or os.environ.get("BACKFIELD_PROJECT_API_KEY", "")

    # Cells that depend on this one will wait until an API key is available.
    mo.stop(not key, "Paste an API key above, or set BACKFIELD_PROJECT_API_KEY in .env")

    def get(path, **params):
        """Send an authenticated GET request to the Backfield public API.

        Args:
            path: The part of the URL after ``/public/v1``.
            **params: Query-string parameters to send with the request.

        Returns:
            The JSON response converted to Python dictionaries and lists.

        This small helper keeps the URL, Bearer header, and JSON conversion
        visible in the tutorial.
        """
        response = httpx.get(
            f"{BASE_URL}/public/v1{path}",
            params=params,
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    return PROJECT_SLUG, get


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Find source mentions

    The project-wide [`/mentions/search`](https://docs.backfield.news/api/mentions/search/) endpoint can filter mentions by entity type and nature.

    We will request:

    - `entity_type=person` because sources are people;
    - `nature=source` because we want people who supplied information;
    - `has_canonical=true` so repeated mentions can be grouped under one canonical person; and
    - `limit=100`, the largest available page size.

    The response is [paginated](https://docs.backfield.news/api/conventions/pagination/), so we must continue requesting pages until we have loaded every matching mention.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get):
    PAGE_SIZE = 100
    source_path = f"/projects/{PROJECT_SLUG}/mentions/search"
    source_params = {
        "entity_type": "person",
        "nature": "source",
        "has_canonical": True,
        "limit": PAGE_SIZE,
    }

    # Load the first page so we know the total number of matching mentions.
    first_page = get(source_path, **source_params)
    source_mentions = first_page["items"]
    total_mentions = first_page["pagination"]["total"]

    # Continue at offsets 100, 200, and so on until every page is loaded.
    for _offset in range(PAGE_SIZE, total_mentions, PAGE_SIZE):
        _page = get(source_path, **source_params, offset=_offset)
        source_mentions.extend(_page["items"])

    print(f"Loaded {len(source_mentions)} source mentions")
    return (source_mentions,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Count mentions by person

    Each result includes a `canonical` person with a stable id and display label. We use that id to combine references to the same person, then count:

    - **mentions** — the number of source mention rows; and
    - **stories** — the number of distinct articles containing those mentions.

    These can differ when a person has more than one saved source mention in a story.
    """)
    return


@app.cell
def _(mo, source_mentions):
    from collections import Counter, defaultdict

    # Count mentions and collect a distinct set of article ids for each person.
    mention_counts = Counter()
    story_ids = defaultdict(set)
    people_by_id = {}

    for _mention in source_mentions:
        _person = _mention["canonical"]
        _person_id = _person["id"]

        mention_counts[_person_id] += 1
        story_ids[_person_id].add(_mention["article"]["id"])
        people_by_id[_person_id] = _person

    # Counter.most_common() returns people in descending mention-count order.
    ranked_sources = [
        {
            "id": _person_id,
            "label": people_by_id[_person_id]["label"],
            "mentions": _count,
            "stories": len(story_ids[_person_id]),
        }
        for _person_id, _count in mention_counts.most_common()
    ]

    # Build a compact Markdown table for the ten most frequent sources.
    _rows = [
        "| Rank | Source | Mentions | Stories |",
        "|---:|---|---:|---:|",
    ]
    for _rank, _source in enumerate(ranked_sources[:10], start=1):
        _rows.append(
            f"| {_rank} | {_source['label']} | "
            f"{_source['mentions']} | {_source['stories']} |"
        )

    mo.md("\n".join(_rows))
    return (ranked_sources,)


@app.cell(hide_code=True)
def _(mo, ranked_sources):
    mo.md(f"""
    ## Step 3: Inspect every mention of {ranked_sources[0]['label']}

    The top-ranked source is **{ranked_sources[0]['label']}**, with **{ranked_sources[0]['mentions']} source mentions**.

    The [person mentions endpoint](https://docs.backfield.news/api/people/mentions/) returns the articles and evidence associated with one canonical person. We will keep the `nature=source` filter so the timeline matches the ranking above.

    Backfield also provides an [aggregated mention timeline](https://docs.backfield.news/api/other/mention-timeline/get-timeline/) that groups counts by date. We are using the mention list instead because we want to show every individual story and its evidence.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get, ranked_sources):
    top_source = ranked_sources[0]
    top_source_response = get(
        f"/projects/{PROJECT_SLUG}/people/{top_source['id']}/mentions",
        nature="source",
        limit=100,
    )

    # Sort by publication date so the newest source mention appears first.
    top_source_mentions = sorted(
        top_source_response["items"],
        key=lambda _mention: _mention["article"]["pub_date"] or "",
        reverse=True,
    )
    return top_source, top_source_mentions


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Draw a commit-style mention timeline

    GitHub displays commits as a vertical history: a line connects events, and each event includes a date, title, and details. We can use the same visual pattern for source mentions.

    Each event below represents one saved source mention. The headline links to the original article, and the evidence text shows the passage Backfield associated with that mention.
    """)
    return


@app.cell
def _(mo, top_source, top_source_mentions):
    import html

    _events = []
    for _mention in top_source_mentions:
        _article = _mention["article"]
        _evidence = _mention["evidence"]
        _mention_text = (
            _evidence["mention_text"]
            if _evidence and _evidence["mention_text"]
            else "No evidence text is available for this mention."
        )

        # Escape API text before inserting it into HTML.
        _date = html.escape(_article["pub_date"] or "Date unavailable")
        _headline = html.escape(_article["headline"])
        _url = html.escape(_article["url"] or "#", quote=True)
        _text = html.escape(_mention_text)

        _events.append(
            f"""
            <div style="position: relative; padding: 0 0 24px 30px;
                        border-left: 2px solid #d0d7de;">
              <span style="position: absolute; left: -7px; top: 4px;
                           width: 12px; height: 12px; border-radius: 50%;
                           background: #1f883d; border: 2px solid white;"></span>
              <div style="color: #656d76; font-size: 0.85rem;">{_date}</div>
              <div style="font-weight: 600; margin: 3px 0;">
                <a href="{_url}" target="_blank">{_headline}</a>
              </div>
              <div style="color: #1f2328; background: #f6f8fa;
                          border: 1px solid #d0d7de; border-radius: 6px;
                          padding: 10px 12px; margin-top: 8px;">
                {_text}
              </div>
            </div>
            """
        )

    source_timeline = mo.Html(
        f"""
        <div style="font-family: system-ui, sans-serif; max-width: 850px;">
          <h3 style="margin-bottom: 20px;">
            Source mentions for {html.escape(top_source['label'])}
          </h3>
          {''.join(_events)}
        </div>
        """
    )

    source_timeline
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Understand the limits of this audit

    This ranking is useful, but it is not a complete measure of sourcing quality or diversity.

    - It counts mentions labeled `source`; it does not judge the quality or importance of a quotation.
    - It includes only mentions linked to canonical people, because stable ids are needed to group the same person.
    - It reflects this demo's deliberately Minnesota-focused article sample, not all Guardian coverage.
    - A person can play different roles in different stories. This tutorial counts only their `source` mentions.

    Treat the audit as a starting point for editorial questions, not as a final verdict.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    You now know how to filter project-wide mentions, follow API pagination, rank canonical people, and retrieve every source mention for one person.

    You could adapt this audit by filtering for quoted mentions, limiting it to a publication-date range, or comparing source patterns across article topics. See the full [mention search parameters](https://docs.backfield.news/api/mentions/search/) for the available filters.
    """)
    return


if __name__ == "__main__":
    app.run()
