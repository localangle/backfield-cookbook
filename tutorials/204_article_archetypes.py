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
    # Tutorial 204: Create editorial archetypes

    Standard news taxonomies tend to be coarse, which makes it hard to derive useful insights from them when they are used for analytics. Labeling articles with categories such as **Sports**, **Local**, **Arts** might be useful for organizing them on a website, but they do not adequately describe the nuance required to create meaningful insights about how those stories resonate with readers.

    Backfield's ability to apply metadata at the article level allows us to tag stories with more editorially meaningful information: things like story format, geographic scope and temporal orientation (is it backward-looking like a recap or forward-looking like a preview?)

    We can futher combine those attributes into **archetypes**: editorially meaningful definitions such as a game recap, an arts review, or a profile of a community member.

    Archetypes can help a newsroom answer questions that sections alone cannot:

    - What performs better: Game previews or game recaps? And what format works best for each?
    - When is the best time in the arc of coverage to introduce an explainer?
    - What kinds of profile subjects are most interesting to our readers?

    In this tutorial, we will define five archetypes and list a sample of the articles that match each one.
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

    load_dotenv()

    BASE_URL = "https://api.demo.backfield.news"
    PROJECT_SLUG = "workbooks"
    key = api_key.value or os.environ.get("BACKFIELD_PROJECT_API_KEY", "")

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
    ## Step 1: Define the archetypes

    Archetypes can be pretty much anything. Rather than trying to classify them directly, we've found that combining multiple LLM-derived attributes of an article into useful categories can be an effective way to define them.

    Our Guardian articles are being categorized across five dimensions: topic, temporal orientation, story format, subject (as in, the primary subject featured in a story like a sports contest or court case) and geographic scope.

    Backfield stores article metadata as a `meta_type` and `category` pair. For example, `subject:sports_contest` means the concrete subject of an article is a sporting event.

    The [Article Meta filter](https://docs.backfield.news/api/taxonomy/article-meta/#querying-with-meta) combines repeated `meta` parameters with **AND**. Our game recap rule therefore requires all four of these tags:

    - `subject:sports_contest`
    - `topic:pro_sports`
    - `temporal_orientation:past`
    - `format:news_story`

    The requested **timeframe** is represented by the API's [`temporal_orientation`](https://docs.backfield.news/api/taxonomy/article-meta/) metadata type. Using the contract's exact field name keeps the query portable.

    Archetypes do not need to use the same metadata types. A person profile can be useful across several topics, while a game recap benefits from a topic, subject, and time constraint.
    """)
    return


@app.cell
def _():
    SAMPLE_SIZE = 5

    ARCHETYPES = (
        {
            "name": "Game recap",
            "description": "Coverage looking back at a completed professional sporting event.",
            "filters": (
                "subject:sports_contest",
                "topic:pro_sports",
                "temporal_orientation:past",
                "format:news_story",
            ),
        },
        {
            "name": "Game preview",
            "description": "Forward-looking coverage of an upcoming professional contest.",
            "filters": (
                "subject:sports_contest",
                "topic:pro_sports",
                "temporal_orientation:future",
            ),
        },
        {
            "name": "Arts review",
            "description": "Criticism or review centered on a cultural work.",
            "filters": (
                "subject:cultural_work",
                "topic:arts_culture",
                "format:review_criticism",
            ),
        },
        {
            "name": "Current crime report",
            "description": "A current news story centered on a specific crime incident.",
            "filters": (
                "subject:crime_incident",
                "topic:public_safety_crime",
                "format:news_story",
                "temporal_orientation:present",
            ),
        },
        {
            "name": "Person profile",
            "description": "A profile whose central subject is a person, regardless of topic.",
            "filters": (
                "subject:person_profile",
                "format:profile",
            ),
        },
    )
    return ARCHETYPES, SAMPLE_SIZE


@app.cell
def _(ARCHETYPES, mo):
    _rows = [
        "| Archetype | Editorial definition | Required metadata |",
        "|---|---|---|",
    ]
    for _archetype in ARCHETYPES:
        _filters = "<br>".join(
            f"`{_filter}`" for _filter in _archetype["filters"]
        )
        _rows.append(
            f"| **{_archetype['name']}** "
            f"| {_archetype['description']} "
            f"| {_filters} |"
        )

    mo.md("\n".join(_rows))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Find matching articles

    The [`/articles/search`](https://docs.backfield.news/api/articles/search/) endpoint accepts the repeatable `meta` filter. `httpx` turns each tuple below into repeated query parameters, so every clause must match.

    We will request the five newest examples for each archetype. The response's pagination total also tells us how many articles match the full definition, even though we display only a sample.
    """)
    return


@app.cell
def _(ARCHETYPES, PROJECT_SLUG, SAMPLE_SIZE, get, mo):
    archetype_results = []

    for _archetype in ARCHETYPES:
        _response = get(
            f"/projects/{PROJECT_SLUG}/articles/search",
            meta=_archetype["filters"],
            sort="pub_date",
            sort_direction="desc",
            limit=SAMPLE_SIZE,
        )
        archetype_results.append(
            {
                **_archetype,
                "articles": _response["items"],
                "total": _response["pagination"]["total"],
            }
        )

    _summary_rows = [
        "| Archetype | Matching articles |",
        "|---|---:|",
    ]
    for _result in archetype_results:
        _summary_rows.append(
            f"| {_result['name']} | {_result['total']} |"
        )

    mo.md("\n".join(_summary_rows))
    return (archetype_results,)


@app.cell(hide_code=True)
def _(archetype_results, mo):
    _sections = []

    for _result in archetype_results:
        _filters = " · ".join(
            f"`{_filter}`" for _filter in _result["filters"]
        )
        _article_lines = []

        for _article in _result["articles"]:
            _headline = _article["headline"].replace("|", r"\|")
            _url = _article["url"]
            _title = f"[{_headline}]({_url})" if _url else _headline
            _date = _article["pub_date"] or "Date unavailable"
            _article_lines.append(f"- {_title} — {_date}")

        if not _article_lines:
            _article_lines.append("- No matching articles in this project.")

        # Build each section from unindented lines. Indentation inside a
        # multiline string can make Markdown interpret some lines as code.
        _section_lines = [
            f"### {_result['name']}",
            "",
            _result["description"],
            "",
            f"**Rule:** {_filters}",
            "",
            f"**{_result['total']} matching articles**",
            "",
            *_article_lines,
        ]
        _sections.append("\n".join(_section_lines))

    mo.md("\n\n---\n\n".join(_sections))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: How you might use archetypes

    Archetypes can be applied to articles in analytics systems like Google Analytics, Snowflake or others. This allows you to ask questions like "Show me how game previews relative to game recaps" and so forth. They can also be used to help analyze your coverage mix and how your teams are using their time.

    In practice, dialing in on the right archetypes might involve some trial and error. It's also possible the pre-set metadata categories offered in Agate aren't enough to derive the archetypes you want — which is why Agate also allows you to write your own custom prompts to create any additional metadata you require.

    Archetypes are also not exclusive. An article can be assigned more than one, depending on how you choose to apply them.

    Backfield supplies the editorial metadata and matching articles. Audience performance data would come from integrations with a newsroom's analytics system.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    Try changing one clause and observe how the sample changes. The metadata discovery routes documented under [Article Meta](https://docs.backfield.news/api/taxonomy/article-meta/#discover-values-in-your-project) show which types and categories are available in a project.

    From here, these archetypes could become saved editorial definitions, recurring coverage reports, or dimensions in an analytics dashboard.

    When you are ready for Custom Extract, continue with [Tutorial 301: Backfield Cooking](./301_backfield_cooking.py).
    """)
    return


if __name__ == "__main__":
    app.run()
