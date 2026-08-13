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
    # Tutorial 203: Build a local news feed

    In this tutorial we will create a local news feed specifically for the city of Minneapolis, using our sample of articles from the Guardian.

    The same principles can be applied to create similar feeds at the neighborhood or even block level, based not only on the primary subject of stories, but also on the assorted mentions of people, places and institutions that appear within them as sources and anecdotes.

    For our Minneapolis news feed, we will query our articles using three approaches:

    1. Search article text for **Minneapolis**.
    2. Search for small geographic features inside a Minneapolis bounding box.
    3. Find articles connected to known Minneapolis people, places, and organizations.

    Each approach catches stories the others can miss. We will combine their results, remove duplicate articles, and keep track of why each story matched.
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

        The helper keeps the URL, Bearer header, and JSON conversion visible.
        """
        response = httpx.get(
            f"{BASE_URL}/public/v1{path}",
            params=params,
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_all(path, **params):
        """Load every page from a Backfield list endpoint.

        Args:
            path: The part of the URL after ``/public/v1``.
            **params: Query-string filters for the endpoint.

        Returns:
            One list containing the ``items`` from every response page.

        Backfield list endpoints return at most 100 items per request. This
        helper follows the shared pagination envelope so none of our three
        discovery methods is given an artificial advantage.
        """
        page_size = 100
        first_page = get(path, **params, limit=page_size)
        items = first_page["items"]
        total = first_page["pagination"]["total"]

        for offset in range(page_size, total, page_size):
            page = get(path, **params, limit=page_size, offset=offset)
            items.extend(page["items"])

        return items

    return PROJECT_SLUG, get_all


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Set up our parameters

    Before running any queries, we need to decide what “news related to Minneapolis” means for this feed. Those choices affect both **recall**—how many useful stories we find—and **precision**—how many of the results are actually relevant.

    We will set four groups of parameters:

    - **Keyword:** `Minneapolis` is our broadest signal. It can find the city in headlines, article text, and URLs, even when no structured location was saved. It can also match a passing reference.
    - **Bounding box:** `-93.33,44.89,-93.19,45.06` roughly covers Minneapolis. A larger box would find more nearby stories but would also admit more references to surrounding communities.
    - **Location types:** we include places, addresses, intersections, streets, spans, and neighborhoods. We exclude city and regional polygons because broad geometries can overlap our box without being meaningfully about Minneapolis. Direct references to the city are covered by the canonical Minneapolis entity instead.
    - **Article metadata:** `!topic:pro_sports` excludes articles tagged with the `pro_sports` topic. In this case we're choosing to exclude stories about sports, but, you'll see, stories featuring teams and organizations in other contexts will still be included.

    Finally, we choose a short list of **canonical entities** with strong Minneapolis connections. This expands the feed beyond literal geography, but it also introduces editorial judgment. We'll start with just a few.

    Backfield documents the available [article metadata](https://docs.backfield.news/api/taxonomy/article-meta/), [location types](https://docs.backfield.news/api/taxonomy/entity-meta/locations/), and [canonical entity endpoints](https://docs.backfield.news/api/entities/).
    """)
    return


@app.cell
def _():
    SEARCH_TERM = "Minneapolis"

    # This approximate bounding box covers the city of Minneapolis.
    # The API expects: minimum longitude, minimum latitude,
    # maximum longitude, maximum latitude.
    MINNEAPOLIS_BBOX = "-93.33,44.89,-93.19,45.06"

    # Keep the geographic query focused on features smaller than a city.
    # The canonical Minneapolis entity handles city-wide references without
    # admitting every city or regional polygon that overlaps our box.
    LOCAL_LOCATION_TYPES = (
        "place",
        "address",
        "intersection_road",
        "intersection_highway",
        "street_road",
        "span",
        "neighborhood",
    )

    # Apply this article metadata filter to all three query families.
    NON_SPORTS_META_FILTER = "!topic:pro_sports"

    # These canonical Stylebook ids give us a small editorially selected set
    # of entities with strong Minneapolis connections.
    MINNEAPOLIS_ENTITIES = (
        {
            "label": "Minneapolis",
            "entity_type": "locations",
            "id": "ea3b6819-1a50-46e0-bd5a-17ef46ffb74b",
        },
        {
            "label": "The Blake School",
            "entity_type": "locations",
            "id": "b92ac682-f83c-46c8-a993-04059608d679",
        },
        {
            "label": "Guthrie Theater",
            "entity_type": "locations",
            "id": "3ce9d088-9f55-4df1-9e04-242bf75331ab",
        },
        {
            "label": "Betsy Hodges",
            "entity_type": "people",
            "id": "1ad0779a-7daf-4323-9475-5feb9eaedeb5",
        },
        {
            "label": "Janee Harteau",
            "entity_type": "people",
            "id": "e18699e8-6aea-478a-a4e0-bf06eeae91d9",
        },
        {
            "label": "Minnesota Orchestra",
            "entity_type": "organizations",
            "id": "34b2c894-d659-4fad-b7e0-5e944abdd21e",
        },
        {
            "label": "Target Corp.",
            "entity_type": "organizations",
            "id": "91948522-5913-4e4c-81c1-391918b02cd9",
        },
    )
    return (
        LOCAL_LOCATION_TYPES,
        MINNEAPOLIS_BBOX,
        MINNEAPOLIS_ENTITIES,
        NON_SPORTS_META_FILTER,
        SEARCH_TERM,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Search for the word “Minneapolis”

    We will start with the [`q` parameter on article search](https://docs.backfield.news/api/articles/search/#keyword-search-q). It searches headlines, article text, and URLs.

    This is the most direct approach. But it can also match passing references (or even unrelated articles), so it should be one input rather than our entire personalization strategy.

    We will also use the [Article Meta filter](https://docs.backfield.news/api/taxonomy/article-meta/) `!topic:pro_sports` to exclude professional sports coverage from this feed.
    """)
    return


@app.cell
def _(NON_SPORTS_META_FILTER, PROJECT_SLUG, SEARCH_TERM, get_all, mo):
    keyword_articles = get_all(
        f"/projects/{PROJECT_SLUG}/articles/search",
        q=SEARCH_TERM,
        meta=NON_SPORTS_META_FILTER,
    )

    _rows = [
        "| Published | Keyword result |",
        "|---|---|",
    ]
    for _article in keyword_articles[:5]:
        _headline = _article["headline"].replace("|", r"\|")
        _url = _article["url"]
        _title = f"[{_headline}]({_url})" if _url else _headline
        _rows.append(f"| {_article['pub_date'] or 'Date unavailable'} | {_title} |")

    mo.md(
        f"**{len(keyword_articles)} articles matched the keyword query.**\n\n"
        + "\n".join(_rows)
    )
    return (keyword_articles,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Search inside a Minneapolis bounding box

    The [geographic search endpoint](https://docs.backfield.news/api/articles/geo-search/) finds articles with location mentions inside a point radius or bounding box.

    The box alone is not enough in this case. Larger geographies like states, counties and regions can overlap Minneapolis, which introduces articles that might not be specifically local. We therefore filter based on the `location_type` parameter, choosing fine-grained geographies from Backfield's [location type vocabulary](https://docs.backfield.news/api/taxonomy/entity-meta/locations/).

    Our list includes addresses, intersections, streets, neighborhoods, and places. It deliberately excludes city and regional polygons after testing showed that broad geometries such as “southern Minnesota” and neighboring St. Paul could overlap the box.

    Editorial judgment comes heavily into play here. Depending on your needs, you may choose to include those broader geographies as well.
    """)
    return


@app.cell
def _(
    LOCAL_LOCATION_TYPES,
    MINNEAPOLIS_BBOX,
    NON_SPORTS_META_FILTER,
    PROJECT_SLUG,
    get_all,
    mo,
):
    geographic_articles = get_all(
        f"/projects/{PROJECT_SLUG}/articles/geo-search",
        bbox=MINNEAPOLIS_BBOX,
        # httpx turns this tuple into one location_type parameter per value.
        location_type=LOCAL_LOCATION_TYPES,
        meta=NON_SPORTS_META_FILTER,
    )

    _rows = [
        "| Published | Geographic result | Matching locations |",
        "|---|---|---|",
    ]
    for _article in geographic_articles[:5]:
        _headline = _article["headline"].replace("|", r"\|")
        _url = _article["url"]
        _title = f"[{_headline}]({_url})" if _url else _headline
        _locations = ", ".join(
            _location["label"] for _location in _article["matching_locations"]
        )
        _rows.append(
            f"| {_article['pub_date'] or 'Date unavailable'} "
            f"| {_title} | {_locations} |"
        )

    mo.md(
        f"**{len(geographic_articles)} articles matched the geographic query.**\n\n"
        + "\n".join(_rows)
    )
    return (geographic_articles,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Follow known Minneapolis entities

    Keywords and coordinates still miss some useful associations. An article about the Blake School might be relevant to a Minneapolis reader without using the word “Minneapolis” or mentioning a location inside our box.

    Canonical entities give us an editorial way to make those connections. We will begin with seven Stylebook records:

    - three locations: Minneapolis, The Blake School, and the Guthrie Theater;
    - two people: Betsy Hodges and Janee Harteau; and
    - two organizations: the Minnesota Orchestra and Target Corp.

    Backfield provides entity-first feeds for canonical [locations](https://docs.backfield.news/api/locations/), [people](https://docs.backfield.news/api/people/), and [organizations](https://docs.backfield.news/api/organizations/). We will use their mention feeds so we get both the matching article and the evidence text. A production feed would likely use a much longer, regularly reviewed entity list.
    """)
    return


@app.cell
def _(MINNEAPOLIS_ENTITIES, NON_SPORTS_META_FILTER, PROJECT_SLUG, get_all, mo):
    entity_results = {}
    entity_evidence = {}

    for _entity in MINNEAPOLIS_ENTITIES:
        _path = (
            f"/projects/{PROJECT_SLUG}/{_entity['entity_type']}/"
            f"{_entity['id']}/mentions"
        )
        _mentions = get_all(_path, meta=NON_SPORTS_META_FILTER)

        # One entity can have several mentions in the same article. Keep one
        # article in the feed while saving all available evidence text.
        _articles_by_id = {}
        for _mention in _mentions:
            _article = _mention["article"]
            _articles_by_id[_article["id"]] = _article

            _evidence = _mention["evidence"]
            if _evidence and _evidence["mention_text"]:
                entity_evidence.setdefault(_article["id"], []).append(
                    _evidence["mention_text"]
                )

        entity_results[_entity["label"]] = list(_articles_by_id.values())

    _rows = [
        "| Entity | Matching articles |",
        "|---|---:|",
    ]
    for _label, _articles in entity_results.items():
        _rows.append(f"| {_label} | {len(_articles)} |")

    mo.md("\n".join(_rows))
    return entity_evidence, entity_results


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Combine and deduplicate the results

    The same article can match several queries. A story might contain the word “Minneapolis,” mention a local address, and reference Target Corp.

    We will use the article's stable `id` as the deduplication key. Instead of throwing away the overlap, we will save every match reason beside the article. That provenance can be useful later for ranking, explanations, or debugging an overly broad feed.
    """)
    return


@app.cell
def _(SEARCH_TERM, entity_results, geographic_articles, keyword_articles, mo):
    _result_sets = [
        (f"Keyword: {SEARCH_TERM}", keyword_articles),
        ("Geography: Minneapolis bounding box", geographic_articles),
    ]
    _result_sets.extend(
        (f"Entity: {_label}", _articles)
        for _label, _articles in entity_results.items()
    )

    # Store one article per stable id and collect every query that found it.
    _articles_by_id = {}
    for _reason, _articles in _result_sets:
        for _article in _articles:
            _match = _articles_by_id.setdefault(
                _article["id"],
                {"article": _article, "matched_by": []},
            )
            _match["matched_by"].append(_reason)

    personalized_articles = [
        {
            **_match["article"],
            "matched_by": _match["matched_by"],
        }
        for _match in _articles_by_id.values()
    ]
    personalized_articles.sort(
        key=lambda _article: (
            _article["pub_date"] or "",
            _article["id"],
        ),
        reverse=True,
    )

    _raw_match_count = sum(len(_articles) for _, _articles in _result_sets)
    _duplicates_removed = _raw_match_count - len(personalized_articles)

    mo.md(
        f"""
        **{_raw_match_count} raw matches became {len(personalized_articles)} unique articles.**

        Deduplication removed **{_duplicates_removed} repeated matches**.
        """
    )
    return (personalized_articles,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6: Display the final feed

    If we're surfacing this feed to readers, we might want to explain why different items appeared. Exposing the query that introduced the item to the feed, along with the text of any relevant mentions, is an effective way to do that.

    So for each article we'll display:

    1. its headline;
    2. whether it matched the `keyword`, `geo`, or `entity` query; and
    3. evidence text from the matching place or canonical entity.

    Geographic results already include their matching location evidence. Our entity mention queries include the same kind of evidence for people, places, and organizations. An entity-only result may not contain a Minneapolis place mention, so in that case we show the text that contains the selected entity instead.
    """)
    return


@app.cell
def _(entity_evidence, geographic_articles, mo, personalized_articles):
    import html

    # Geographic search returns the matching location mentions with each
    # article, including evidence text when it is available.
    _geo_evidence = {}
    for _article in geographic_articles:
        for _location in _article["matching_locations"]:
            _evidence = _location["evidence"]
            if _evidence and _evidence["mention_text"]:
                _geo_evidence[_article["id"]] = _evidence["mention_text"]
                break

    _entries = []
    feed_entries = []
    for _article in personalized_articles:
        _query_types = []
        for _reason in _article["matched_by"]:
            if _reason.startswith("Keyword") and "keyword" not in _query_types:
                _query_types.append("keyword")
            elif _reason.startswith("Geography") and "geo" not in _query_types:
                _query_types.append("geo")
            elif _reason.startswith("Entity") and "entity" not in _query_types:
                _query_types.append("entity")

        _matching_text = _geo_evidence.get(_article["id"])
        if not _matching_text and entity_evidence.get(_article["id"]):
            _matching_text = entity_evidence[_article["id"]][0]
        if not _matching_text:
            _matching_text = "No matching mention text is available."

        feed_entries.append(
            {
                "id": _article["id"],
                "headline": _article["headline"],
                "url": _article["url"],
                "pub_date": _article["pub_date"],
                "preview": (
                    _article["preview"] if "preview" in _article else None
                ),
                "query_types": _query_types,
                "matching_text": _matching_text,
            }
        )

        _headline = html.escape(_article["headline"])
        _url = html.escape(_article["url"] or "", quote=True)
        _headline_html = (
            f'<a href="{_url}" target="_blank">{_headline}</a>'
            if _url
            else _headline
        )
        _query_text = html.escape(", ".join(_query_types))
        _mention_text = html.escape(_matching_text)

        _entries.append(
            f"""
            <article style="padding: 4px 0 16px;">
              <div><strong>Headline:</strong> {_headline_html}</div>
              <div><strong>Query type:</strong> {_query_text}</div>
              <div><strong>Matching mention:</strong> {_mention_text}</div>
            </article>
            """
        )

    personalized_feed = mo.Html(
        """
        <div style="font-family: system-ui, sans-serif; max-width: 900px;">
        """
        + "\n<hr style=\"border: 0; border-top: 1px solid #d0d7de;\">\n".join(
            _entries
        )
        + "</div>"
    )

    personalized_feed
    return (feed_entries,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7: Decide what belongs in the final feed

    Deduplication gives us a candidate set, not a finished recommendation system.

    We can use Backfield to further filter and sort our results (say, ordering by date) or we can apply any number of reranking techniques to surface the most relevant articles and/or optimize for precision vs. recall.

    The right rules depend on the product. A breaking-news alert should probably be strict. A weekend reading list can afford to be broader.

    Here we'll use an **LLM-as-reranker** strategy to take a final pass over our results. We will ask [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) to judge each candidate from the perspective of a Minneapolis resident.

    To control cost and keep the prompt focused, we will evaluate only the **25 most recent candidates**. The model will assign a relevance score, explain its decision, remove weak matches, and reorder the remaining stories by score.

    Paste an OpenAI API key below, or set `OPENAI_API_KEY` in `.env`. The key is sent only to the [OpenAI Responses API](https://developers.openai.com/api/docs/guides/reasoning) and is never included in the article data or notebook output.
    """)
    return


@app.cell
def _(mo):
    openai_api_key = mo.ui.text(
        kind="password",
        label="Paste your OpenAI API key",
    )
    openai_api_key
    return (openai_api_key,)


@app.cell
def _(feed_entries, mo, openai_api_key):
    import json as _json
    import os as _os

    import httpx as _httpx
    from dotenv import load_dotenv as _load_dotenv

    # Support CI exports and local `.env` files without pasting a key.
    _load_dotenv()

    OPENAI_MODEL = "gpt-5.6-terra"
    RERANK_LIMIT = 25
    _openai_key = (
        openai_api_key.value
        or _os.environ.get("OPENAI_API_KEY", "")
    )

    mo.stop(
        not _openai_key,
        "Paste an OpenAI API key above, or set OPENAI_API_KEY in .env",
    )

    # The articles are already newest-first. Limiting before the API call
    # controls token use and makes recency the first coarse ranking signal.
    rerank_candidates = feed_entries[:RERANK_LIMIT]
    _candidate_data = [
        {
            "article_id": _article["id"],
            "headline": _article["headline"],
            "publication_date": _article["pub_date"],
            "query_types": _article["query_types"],
            "matching_text": _article["matching_text"],
            "preview": _article["preview"],
        }
        for _article in rerank_candidates
    ]

    _instructions = """
    You are the final editor for a geographically personalized news feed.
    Evaluate every candidate from the perspective of a Minneapolis resident.

    Keep an article only when it has a meaningful connection to Minneapolis,
    its civic life, institutions, neighborhoods, residents, or issues likely
    to affect people who live there. Reject passing references, broad Minnesota
    stories without a clear Minneapolis connection, and unrelated national or
    international coverage.

    Query types and matching text explain why retrieval found an article; they
    are evidence, not proof of relevance. Give each article a score from 0 to
    100. Set keep=true only for scores of 70 or higher. Return exactly one
    decision for every supplied article_id.
    """

    _response = _httpx.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {_openai_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "reasoning": {"effort": "low"},
            "instructions": _instructions,
            "input": _json.dumps(_candidate_data),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "minneapolis_article_reranking",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "decisions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "article_id": {"type": "integer"},
                                        "keep": {"type": "boolean"},
                                        "score": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 100,
                                        },
                                        "reason": {"type": "string"},
                                    },
                                    "required": [
                                        "article_id",
                                        "keep",
                                        "score",
                                        "reason",
                                    ],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["decisions"],
                        "additionalProperties": False,
                    },
                }
            },
            "max_output_tokens": 5000,
        },
        timeout=120,
    )
    _response.raise_for_status()
    _response_data = _response.json()

    # Raw HTTP responses place generated text inside the message output.
    _output_text = next(
        _content["text"]
        for _output in _response_data["output"]
        for _content in _output.get("content", [])
        if _content["type"] == "output_text"
    )
    _decisions = _json.loads(_output_text)["decisions"]
    _decisions_by_id = {
        _decision["article_id"]: _decision
        for _decision in _decisions
    }

    reranked_articles = [
        {
            **_article,
            "rerank": _decisions_by_id[_article["id"]],
        }
        for _article in rerank_candidates
        if (
            _article["id"] in _decisions_by_id
            and _decisions_by_id[_article["id"]]["keep"]
        )
    ]
    reranked_articles.sort(
        key=lambda _article: (
            _article["rerank"]["score"],
            _article["pub_date"] or "",
        ),
        reverse=True,
    )

    rejected_articles = [
        {
            **_article,
            "rerank": _decisions_by_id[_article["id"]],
        }
        for _article in rerank_candidates
        if (
            _article["id"] in _decisions_by_id
            and not _decisions_by_id[_article["id"]]["keep"]
        )
    ]
    return (
        OPENAI_MODEL,
        rejected_articles,
        rerank_candidates,
        reranked_articles,
    )


@app.cell
def _(
    OPENAI_MODEL,
    mo,
    rejected_articles,
    rerank_candidates,
    reranked_articles,
):
    import html as _html

    def render_decision(article):
        """Render one reranking decision as a small HTML block.

        Args:
            article: A feed entry with the model's ``rerank`` decision.

        Returns:
            Escaped HTML showing the headline, score, and explanation.
        """
        headline = _html.escape(article["headline"])
        url = _html.escape(article["url"] or "", quote=True)
        headline_html = (
            f'<a href="{url}" target="_blank">{headline}</a>'
            if url
            else headline
        )
        score = article["rerank"]["score"]
        reason = _html.escape(article["rerank"]["reason"])
        return f"""
        <article style="padding: 6px 0 14px;">
          <div><strong>{headline_html}</strong></div>
          <div>Relevance score: {score}/100</div>
          <div>{reason}</div>
        </article>
        """

    _kept_html = "\n<hr>\n".join(
        render_decision(_article)
        for _article in reranked_articles
    )
    _rejected_html = "\n<hr>\n".join(
        render_decision(_article)
        for _article in rejected_articles
    )

    reranked_feed = mo.Html(
        f"""
        <div style="font-family: system-ui, sans-serif; max-width: 900px;">
          <h3>Reranked Minneapolis feed</h3>
          <p>
            {OPENAI_MODEL} kept {len(reranked_articles)} of
            {len(rerank_candidates)} candidates.
          </p>
          {_kept_html or '<p>No articles met the relevance threshold.</p>'}
          <details style="margin-top: 24px;">
            <summary>
              Removed articles ({len(rejected_articles)})
            </summary>
            <div style="margin-top: 12px;">
              {_rejected_html or '<p>No articles were removed.</p>'}
            </div>
          </details>
        </div>
        """
    )

    reranked_feed
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    We now have the basic shape of a geographically personalized feed: broad recall from several query types, careful geographic constraints, editorially selected entities, and article-level deduplication.

    Try changing the bounding box, local location types, or canonical entities for another community. The [article search](https://docs.backfield.news/api/articles/search/), [geographic search](https://docs.backfield.news/api/articles/geo-search/), and [entity endpoints](https://docs.backfield.news/api/entities/) provide the building blocks.

    **[Tutorial 204: Create article archetypes](./204_article_archetypes.py)** combines article metadata into more specific editorial definitions.
    """)
    return


if __name__ == "__main__":
    app.run()
