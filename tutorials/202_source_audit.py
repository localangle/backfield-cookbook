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
    # Tutorial 202: Explore who appears in coverage

    Newsrooms often want to understand which people appear in their coverage. We will build that understanding in three stages:

    1. List the people mentioned across the project.
    2. Use mention **natures** to distinguish featured people from background context.
    3. Draw a GitHub-style contribution timeline for one frequently featured person.

    Starting with the complete list makes the effect of filtering easier to see.
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
    ## Step 1: List people

    The project-wide [`/mentions/search`](https://docs.backfield.news/api/mentions/search/) endpoint can return every person mention in the project.

    We will request:

    - `entity_type=person` because we want people rather than locations or organizations;
    - `has_canonical=true` so repeated mentions can be grouped under one canonical person; and
    - `limit=100`, the largest available page size.

    We are deliberately not filtering by role yet. The response is [paginated](https://docs.backfield.news/api/conventions/pagination/), so we continue requesting pages until every person mention is loaded.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get):
    PAGE_SIZE = 100
    people_path = f"/projects/{PROJECT_SLUG}/mentions/search"
    people_params = {
        "entity_type": "person",
        "has_canonical": True,
        "limit": PAGE_SIZE,
    }

    # Load the first page so we know the total number of matching mentions.
    first_page = get(people_path, **people_params)
    people_mentions = first_page["items"]
    total_mentions = first_page["pagination"]["total"]

    # Continue at offsets 100, 200, and so on until every page is loaded.
    for _offset in range(PAGE_SIZE, total_mentions, PAGE_SIZE):
        _page = get(people_path, **people_params, offset=_offset)
        people_mentions.extend(_page["items"])

    print(f"Loaded {len(people_mentions)} person mentions")
    return PAGE_SIZE, people_mentions


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Count every mention

    Each result includes a `canonical` person with a stable id and display label. We use that id to combine references to the same person, then count:

    - **mentions** — the number of mention rows; and
    - **stories** — the number of distinct articles containing those mentions.

    At this stage, every role counts. Someone who is only background context will appear alongside sources, subjects, experts, and other featured people.
    """)
    return


@app.cell
def _(mo, people_mentions):
    from collections import Counter, defaultdict

    def rank_people(mentions):
        """Rank canonical people by their number of mentions.

        Args:
            mentions: Mention records returned by the project-wide search endpoint.

        Returns:
            A list of people in descending mention-count order. Each item includes
            the canonical id, display label, mention count, and distinct story count.
        """
        mention_counts = Counter()
        story_ids = defaultdict(set)
        people_by_id = {}

        for mention in mentions:
            person = mention["canonical"]
            person_id = person["id"]
            mention_counts[person_id] += 1
            story_ids[person_id].add(mention["article"]["id"])
            people_by_id[person_id] = person

        return [
            {
                "id": person_id,
                "label": people_by_id[person_id]["label"],
                "mentions": count,
                "stories": len(story_ids[person_id]),
            }
            for person_id, count in mention_counts.most_common()
        ]

    ranked_people = rank_people(people_mentions)

    # Start with a compact list of the ten most frequently mentioned people.
    _rows = [
        "| Rank | Person | Mentions | Stories |",
        "|---:|---|---:|---:|",
    ]
    for _rank, _person in enumerate(ranked_people[:10], start=1):
        _rows.append(
            f"| {_rank} | {_person['label']} | "
            f"{_person['mentions']} | {_person['stories']} |"
        )

    mo.md("\n".join(_rows))
    return (rank_people,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Use natures to focus the list

    A mention's [`nature`](https://docs.backfield.news/api/taxonomy/mention-meta/people/) describes the person's role in that story. For example, a person might be a `source`, `subject`, `expert`, `official`, or `context`.

    The `context` nature is useful when reading an individual article, but it can add noise to an audit of who the coverage features. We will remove only `context` mentions and keep every other nature.

    The search endpoint can include selected natures, but it does not provide a "not context" query. Filtering the complete results in Python makes that rule explicit.
    """)
    return


@app.cell
def _(mo, people_mentions, rank_people):
    featured_mentions = [
        _mention
        for _mention in people_mentions
        if _mention["nature"] != "context"
    ]
    featured_people = rank_people(featured_mentions)

    _rows = [
        "| Rank | Featured person | Mentions | Stories |",
        "|---:|---|---:|---:|",
    ]
    for _rank, _person in enumerate(featured_people[:10], start=1):
        _rows.append(
            f"| {_rank} | {_person['label']} | "
            f"{_person['mentions']} | {_person['stories']} |"
        )

    mo.md("\n".join(_rows))
    return (featured_people,)


@app.cell(hide_code=True)
def _(featured_people, mo):
    mo.md(f"""
    ## Step 4: Follow {featured_people[0]['label']} over time

    After removing `context` mentions, **{featured_people[0]['label']}** is the most frequently featured person, with **{featured_people[0]['mentions']} mentions** across **{featured_people[0]['stories']} stories**.

    The [person mentions endpoint](https://docs.backfield.news/api/people/mentions/) returns every article associated with one canonical person. We will load that complete history and apply the same `nature != "context"` rule.
    """)
    return


@app.cell
def _(PAGE_SIZE, PROJECT_SLUG, featured_people, get):
    top_person = featured_people[0]
    top_person_path = (
        f"/projects/{PROJECT_SLUG}/people/{top_person['id']}/mentions"
    )
    top_person_params = {"limit": PAGE_SIZE}

    # This endpoint is paginated too, so load the person's complete history.
    _first_page = get(top_person_path, **top_person_params)
    top_person_mentions = _first_page["items"]
    _total_mentions = _first_page["pagination"]["total"]
    for _offset in range(PAGE_SIZE, _total_mentions, PAGE_SIZE):
        _page = get(top_person_path, **top_person_params, offset=_offset)
        top_person_mentions.extend(_page["items"])

    # Apply the same nature rule used to create the featured-people ranking.
    top_person_mentions = [
        _mention
        for _mention in top_person_mentions
        if _mention["nature"] != "context"
    ]
    return top_person, top_person_mentions


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Draw a GitHub-style mention timeline

    GitHub's contribution calendar uses one square per day. Darker greens indicate more activity. We can use the same pattern for mentions:

    - each square represents one publication date;
    - darker squares represent more mentions; and
    - hovering over a square shows the exact date and count.

    We draw one calendar per year so every dated mention remains visible.
    """)
    return


@app.cell
def _(mo, top_person, top_person_mentions):
    import collections
    import datetime
    import html

    # Count mentions by publication date. More than one mention can land on a day.
    _mention_dates = [
        datetime.date.fromisoformat(_mention["article"]["pub_date"][:10])
        for _mention in top_person_mentions
        if _mention["article"]["pub_date"]
    ]
    _date_counts = collections.Counter(_mention_dates)
    _largest_count = max(_date_counts.values(), default=1)
    _colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
    _calendars = []

    # A separate calendar for each year keeps the layout compact while still
    # showing every dated mention in the person's history.
    for _year in sorted({_date.year for _date in _mention_dates}):
        _year_start = datetime.date(_year, 1, 1)
        _year_end = datetime.date(_year, 12, 31)

        # GitHub calendars start each week on Sunday. Extend the grid to full
        # weeks so every date lands in a predictable row and column.
        _grid_start = _year_start - datetime.timedelta(
            days=(_year_start.weekday() + 1) % 7
        )
        _grid_end = _year_end + datetime.timedelta(
            days=(5 - _year_end.weekday()) % 7
        )
        _week_count = ((_grid_end - _grid_start).days + 1) // 7

        _month_labels = []
        for _month in range(1, 13):
            _month_date = datetime.date(_year, _month, 1)
            _column = ((_month_date - _grid_start).days // 7) + 2
            _month_labels.append(
                f'<span style="grid-column: {_column}; grid-row: 1;">'
                f'{_month_date.strftime("%b")}</span>'
            )

        _day_cells = []
        _date = _year_start
        while _date <= _year_end:
            _count = _date_counts[_date]
            # Scale each non-zero count to one of GitHub's four green shades.
            _level = (
                0
                if _count == 0
                else max(1, (_count * 4 + _largest_count - 1) // _largest_count)
            )
            _column = ((_date - _grid_start).days // 7) + 2
            _row = ((_date.weekday() + 1) % 7) + 2
            _label = "mention" if _count == 1 else "mentions"
            _day_cells.append(
                f'<span title="{_date.isoformat()}: {_count} {_label}" '
                f'style="grid-column: {_column}; grid-row: {_row}; '
                f'width: 11px; height: 11px; border-radius: 2px; '
                f'background: {_colors[_level]};"></span>'
            )
            _date += datetime.timedelta(days=1)

        _calendars.append(
            f"""
            <section style="margin: 0 0 28px;">
              <h4 style="margin: 0 0 10px;">{_year}</h4>
              <div style="display: grid;
                          grid-template-columns: 30px repeat({_week_count}, 11px);
                          grid-template-rows: 18px repeat(7, 11px);
                          gap: 3px; color: #656d76; font-size: 11px;">
                {''.join(_month_labels)}
                <span style="grid-column: 1; grid-row: 3;">Mon</span>
                <span style="grid-column: 1; grid-row: 5;">Wed</span>
                <span style="grid-column: 1; grid-row: 7;">Fri</span>
                {''.join(_day_cells)}
              </div>
            </section>
            """
        )

    people_timeline = mo.Html(
        f"""
        <div style="font-family: system-ui, sans-serif; max-width: 900px;
                    overflow-x: auto; border: 1px solid #d0d7de;
                    border-radius: 6px; padding: 20px;">
          <h3 style="margin: 0 0 20px;">
            Mentions of {html.escape(top_person['label'])}
          </h3>
          {''.join(_calendars) or '<p>No dated mentions are available.</p>'}
          <div style="display: flex; align-items: center; justify-content: end;
                      gap: 4px; color: #656d76; font-size: 12px;">
            <span>Less</span>
            {''.join(
                f'<span style="width: 11px; height: 11px; border-radius: 2px; '
                f'background: {_color};"></span>'
                for _color in _colors
            )}
            <span>More</span>
          </div>
        </div>
        """
    )

    people_timeline
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6: Understand the limits of this audit

    This ranking is useful, but it is not a complete measure of prominence, sourcing quality, or diversity.

    - The first ranking counts every person mention; the focused ranking excludes only `context`.
    - It includes only mentions linked to canonical people, because stable ids are needed to group the same person.
    - It reflects this demo's deliberately Minnesota-focused article sample, not all Guardian coverage.
    - The calendar counts mentions by article publication date. Mentions without a publication date cannot appear on it.

    Treat the audit as a starting point for editorial questions, not as a final verdict.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    You now know how to list project-wide person mentions, use natures to focus an audit, follow API pagination, rank canonical people, and chart one person's mentions over time.

    You could adapt this audit by choosing different natures, filtering for quoted mentions, limiting it to a publication-date range, or comparing patterns across article topics. See the full [mention search parameters](https://docs.backfield.news/api/mentions/search/) for the available filters.
    """)
    return


if __name__ == "__main__":
    app.run()
