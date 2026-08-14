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
    # Tutorial 301: "Backfield Cooking"

    Earlier tutorials relied on Backfield's first-class data types, such as people, places and metadata. Agate's [Custom Extract node](https://docs.backfield.news/tutorials/agate/custom-extraction/) lets a project define its own arbitrary structured objects to be pulled out of text.

    Taking inspiration from the early days of [NYT Cooking](https://cooking.nytimes.com), we will build a small **Backfield Cooking** browser on top of structured data that has been extracted from narrative recipes. Each recipe article includes:

    - **ingredients** with quantities;
    - **steps** for preparing the dish;
    - **recipe details** such as the dish name and serving size; and
    - **meal** metadata, such as breakfast, lunch, or dinner.

    We will load those records from the API once, index them in the notebook, and then search locally by meal or ingredient.
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
        """
        response = httpx.get(
            f"{BASE_URL}/public/v1{path}",
            params=params,
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
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
    ## Step 1: Find the cooking articles

    The demo corpus is **Backfield Cooking** — 25 synthetic recipe articles whose URLs all share the host `backfieldcooking.example`.

    The [`q`](https://docs.backfield.news/api/articles/search/) parameter searches headline, body, and URL, so matching that host selects the full set. Requesting `include=counts` is useful here: `counts.custom_records` shows which record types exist on each article before we fetch them.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get_all, mo):
    PUBLICATION = "Backfield Cooking"
    COOKING_URL_HOST = "backfieldcooking.example"

    cooking_articles = get_all(
        f"/projects/{PROJECT_SLUG}/articles/search",
        q=COOKING_URL_HOST,
        include="counts",
        sort="pub_date",
        sort_direction="desc",
    )

    mo.stop(
        not cooking_articles,
        f"No {PUBLICATION} articles found (searched URL host {COOKING_URL_HOST!r}).",
    )

    _rows = [
        "| Article | Meal tags | Custom records |",
        "|---|---|---|",
    ]
    for _article in cooking_articles:
        _meals = ", ".join(
            _tag["category"]
            for _tag in _article["metadata"]
            if _tag["meta_type"] == "meal"
        ) or "—"
        _records = ", ".join(
            f"{_type}×{_count}"
            for _type, _count in sorted(
                _article["counts"]["custom_records"].items()
            )
        ) or "—"
        _headline = _article["headline"].replace("|", r"\|")
        _rows.append(f"| {_headline} | {_meals} | {_records} |")

    mo.md(
        f"**{len(cooking_articles)} cooking articles from {PUBLICATION}.**\n\n"
        + "\n".join(_rows)
    )
    return (cooking_articles,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Load recipe custom records

    The [custom records endpoint](https://docs.backfield.news/api/articles/hub/custom-records/) returns structured objects produced by Custom Extract for each article.

    In this project, each recipe has three record types:

    - `recipe_details` — dish name and serving size;
    - `ingredients` — each ingredient's name and quantity; and
    - `steps` — ordered preparation instructions.

    Meal type is stored separately as ordinary [article metadata](https://docs.backfield.news/api/taxonomy/article-meta/) with `meta_type=meal`.
    """)
    return


@app.cell
def _(PROJECT_SLUG, cooking_articles, get_all):
    def build_recipe(article, records):
        """Assemble one searchable recipe object from article and custom records.

        Args:
            article: An article list row from the cooking publication search.
            records: Custom-record rows returned for that article.

        Returns:
            A dictionary with the fields our local browser will search and display.
        """
        details = next(
            (
                record["fields"]
                for record in records
                if record["record_type"] == "recipe_details"
            ),
            {},
        )
        ingredients = [
            {
                "name": record["fields"]["name"],
                "quantity": record["fields"]["quantity"],
            }
            for record in records
            if record["record_type"] == "ingredients"
        ]
        steps = [
            record["fields"]["step"]
            for record in records
            if record["record_type"] == "steps"
        ]
        meals = [
            tag["category"]
            for tag in article["metadata"]
            if tag["meta_type"] == "meal"
        ]

        return {
            "article_id": article["id"],
            "headline": article["headline"],
            "url": article["url"],
            "author": article["author"],
            "pub_date": article["pub_date"],
            "name": details.get("name") or article["headline"],
            "serving_size": details.get("serving_size"),
            "meals": meals,
            "ingredients": ingredients,
            "steps": steps,
        }

    recipes = []
    for _article in cooking_articles:
        _records = get_all(
            f"/projects/{PROJECT_SLUG}/articles/{_article['id']}/custom-records"
        )
        recipes.append(build_recipe(_article, _records))

    print(f"Loaded {len(recipes)} recipes")
    for _recipe in recipes:
        print(
            f"- {_recipe['name']}: "
            f"{len(_recipe['ingredients'])} ingredients, "
            f"{len(_recipe['steps'])} steps, "
            f"meals={_recipe['meals']}"
        )
    return (recipes,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Index recipes for local search

    Generally it is not a great idea to use Backfield for consumer-facing applications, unless you provision it for public traffic in your own installation. Better to use Backfield to feed production systems that in turn are equipped to serve public traffic.

    In this case, we'll store our records in a simple Python index so we don't have to query the API repeatedly.

    Our index is intentionally small:

    - a sorted list of meal labels for a dropdown; and
    - each recipe's ingredient names, lowercased, for substring matching.
    """)
    return


@app.cell
def _(recipes):
    meal_options = sorted(
        {
            meal
            for recipe in recipes
            for meal in recipe["meals"]
        }
    )

    # Store a lowercase ingredient list beside each recipe so search stays simple.
    recipe_index = [
        {
            **recipe,
            "ingredient_names": [
                ingredient["name"].lower()
                for ingredient in recipe["ingredients"]
                if ingredient["name"]
            ],
        }
        for recipe in recipes
    ]
    return meal_options, recipe_index


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Search by meal or ingredient

    Use the controls below to filter the local index.

    - **Meal** narrows recipes to a metadata category such as Dinner.
    - **Ingredient** keeps recipes whose ingredient list contains the typed text.

    Leave either control blank to ignore that filter. Matching happens entirely in the notebook.
    """)
    return


@app.cell
def _(meal_options, mo):
    meal_filter = mo.ui.dropdown(
        options=["Any meal", *meal_options],
        value="Any meal",
        label="Meal",
    )
    ingredient_filter = mo.ui.text(
        value="",
        label="Ingredient contains",
        placeholder="e.g. gochujang, tofu, maple",
    )
    mo.hstack([meal_filter, ingredient_filter], justify="start", gap=1.5)
    return ingredient_filter, meal_filter


@app.cell
def _(ingredient_filter, meal_filter, mo, recipe_index):
    import html

    selected_meal = meal_filter.value
    ingredient_query = ingredient_filter.value.strip().lower()

    matches = []
    for _recipe in recipe_index:
        if selected_meal != "Any meal" and selected_meal not in _recipe["meals"]:
            continue
        if ingredient_query and not any(
            ingredient_query in _name for _name in _recipe["ingredient_names"]
        ):
            continue
        matches.append(_recipe)

    _cards = []
    for _recipe in matches:
        _title = html.escape(_recipe["name"])
        _url = html.escape(_recipe["url"] or "", quote=True)
        _title_html = (
            f'<a href="{_url}" target="_blank">{_title}</a>'
            if _url
            else _title
        )
        _meals = html.escape(", ".join(_recipe["meals"]) or "Unspecified meal")
        _servings = html.escape(_recipe["serving_size"] or "Unknown")
        _ingredient_items = "".join(
            "<li>"
            + html.escape(
                f"{_item['quantity']} {_item['name']}".strip()
                if _item["quantity"]
                else _item["name"]
            )
            + "</li>"
            for _item in _recipe["ingredients"]
        )
        _step_items = "".join(
            f"<li>{html.escape(_step)}</li>" for _step in _recipe["steps"]
        )
        _cards.append(
            f"""
            <article style="padding: 8px 0 20px;">
              <h3 style="margin: 0 0 6px;">{_title_html}</h3>
              <div style="color: #656d76; margin-bottom: 10px;">
                Meal: {_meals} · Serves {_servings}
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1.4fr; gap: 18px;">
                <div>
                  <strong>Ingredients</strong>
                  <ul>{_ingredient_items}</ul>
                </div>
                <div>
                  <strong>Steps</strong>
                  <ol>{_step_items}</ol>
                </div>
              </div>
            </article>
            """
        )

    cooking_browser = mo.Html(
        f"""
        <div style="font-family: system-ui, sans-serif; max-width: 960px;">
          <p><strong>{len(matches)}</strong> recipe(s) matched.</p>
          {"<hr style='border:0;border-top:1px solid #d0d7de;'>".join(_cards) or "<p>No recipes matched these filters.</p>"}
        </div>
        """
    )
    cooking_browser
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Why this pattern matters

    Custom Extract turns freeform article text into application-ready structured data. Once those objects exist, Backfield is the system of record for extraction — but your product can own search, ranking and presentation.

    A production cooking app might sync recipe records into Postgres, Elasticsearch, or a vector index, then serve readers from that local copy. The notebook version does the same thing at a smaller scale.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    Try searching for `gochujang`, `tofu`, or `maple`, or switch the meal filter across Breakfast, Lunch, Dinner, and Snack. Re-run the loading cells whenever new Backfield Cooking recipes land in the project.

    Useful references:

    - [List and search articles](https://docs.backfield.news/api/articles/search/)
    - [List custom records](https://docs.backfield.news/api/articles/hub/custom-records/)
    - [Article Meta](https://docs.backfield.news/api/taxonomy/article-meta/)

    Continue with [Tutorial 302: Build an entity knowledge graph](./302_entity_knowledge_graph.py) to explore political people and the organizations and locations directly connected to them.
    """)
    return


if __name__ == "__main__":
    app.run()
