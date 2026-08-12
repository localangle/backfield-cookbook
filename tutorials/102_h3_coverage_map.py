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
    # Tutorial 102: Map coverage with H3 hexagons

    In [Tutorial 101](./101_hello_backfield.py), we searched articles and inspected the entities found in one story. Now we will use those location entities to build a U.S. coverage map.

    Backfield assigns an [H3 cell](https://h3geo.org/) to each geocoded location. H3 divides the world into hexagons, giving us a consistent way to group nearby locations and count the articles that mention them.

    By the end of this tutorial, we will have a national map where:

    - each hexagon represents an area of the country;
    - darker hexagons represent more articles; and
    - hovering over a hexagon shows its article count.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Connect to Backfield

    As in Tutorial 101, you can paste a [project API key](https://docs.backfield.news/api/authentication/) below or set `BACKFIELD_PROJECT_API_KEY` in `.env`.
    """)
    return


@app.cell
def _(mo):
    api_key = mo.ui.text(kind="password", label="Paste your Backfield project API key")
    api_key  # noqa: B018
    return (api_key,)


@app.cell
def _(api_key, mo):
    import math
    import os

    import httpx
    import pydeck as pdk
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

        The national aggregation can take longer than a simple article lookup,
        so this tutorial allows up to 30 seconds for the response.
        """
        response = httpx.get(
            f"{BASE_URL}/public/v1{path}",
            params=params,
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    return PROJECT_SLUG, get, math, pdk


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Choose the map area and hexagon size

    The [geo-cell coverage endpoint](https://docs.backfield.news/api/other/geo-cells/coverage/) requires a bounding box in this order:

    ```text
    minimum longitude, minimum latitude, maximum longitude, maximum latitude
    ```

    We will use a bounding box around the contiguous United States.

    H3 supports resolutions from 0 (very large hexagons) to 15 (very small hexagons). We will request **resolution 5**, where an average hexagon covers about 250 square kilometers. That is large enough to show national patterns while still separating many neighboring cities. See the [H3 resolution table](https://h3geo.org/docs/core-library/restable/) for other sizes.
    """)
    return


@app.cell
def _():
    # West, south, east, and north edges of the contiguous United States.
    US_BBOX = "-125,24,-66.5,49.5"

    # Resolution 5 produces relatively large, city-scale hexagons.
    H3_RESOLUTION = 5
    return H3_RESOLUTION, US_BBOX


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Request article counts by hexagon

    [`GET /articles/geo-cells`](https://docs.backfield.news/api/other/geo-cells/coverage/) counts the distinct articles that mention at least one qualifying location in each H3 cell.

    An article counts only once in a cell, even when it mentions several places inside that same hexagon. One article can still contribute to several cells when it mentions places in different parts of the country.
    """)
    return


@app.cell
def _(H3_RESOLUTION, PROJECT_SLUG, US_BBOX, get):
    coverage = get(
        f"/projects/{PROJECT_SLUG}/articles/geo-cells",
        bbox=US_BBOX,
        resolution=H3_RESOLUTION,
    )
    cells = coverage["cells"]

    print(f"Requested resolution: {coverage['requested_resolution']}")
    print(f"Resolution returned: {coverage['resolution']}")
    print(f"Hexagons with coverage: {len(cells)}")
    print(f"Automatically coarsened: {coverage['coarsened']}")
    return cells, coverage


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The API may return a coarser resolution when a request would produce more than 5,000 cells. Always draw the cells using the response's `resolution`. In this small demo project, the requested resolution should remain unchanged.

    The cells arrive in descending count order. Let’s inspect the busiest few before drawing the map.
    """)
    return


@app.cell
def _(cells):
    for _cell in cells[:5]:
        print(f"{_cell['h3_cell']}: {_cell['article_count']} articles")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Turn counts into colors

    We will shade low-count hexagons light blue and high-count hexagons dark blue.

    A few cells have much larger counts than the rest. A logarithmic scale reduces that gap so cells with smaller counts remain visible. The underlying `article_count` does not change; only its display color does.
    """)
    return


@app.cell
def _(cells, math):
    max_count = max(_cell["article_count"] for _cell in cells)

    map_cells = []
    for _cell in cells:
        # Scale each count from 0 to 1. log1p also works when a count is 0.
        _strength = math.log1p(_cell["article_count"]) / math.log1p(max_count)

        # Store the color beside the original H3 index and article count.
        map_cells.append(
            {
                **_cell,
                "fill_color": [
                    int(225 - 175 * _strength),
                    int(235 - 125 * _strength),
                    int(255 - 35 * _strength),
                    190,
                ],
            }
        )
    return (map_cells,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Draw the national coverage map

    [pydeck](https://deckgl.readthedocs.io/en/latest/) can draw H3 indexes directly with its `H3HexagonLayer`. We give it the cell index, the color calculated above, and the original article count for the hover tooltip.

    Darker hexagons represent more articles. Hover over any hexagon to see its exact count.
    """)
    return


@app.cell
def _(map_cells, pdk):
    coverage_layer = pdk.Layer(
        "H3HexagonLayer",
        map_cells,
        get_hexagon="h3_cell",
        get_fill_color="fill_color",
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        pickable=True,
        stroked=True,
    )

    coverage_map = pdk.Deck(
        layers=[coverage_layer],
        initial_view_state=pdk.ViewState(
            latitude=38,
            longitude=-96,
            zoom=3.2,
            pitch=0,
        ),
        map_provider="carto",
        map_style="light",
        tooltip={
            "html": "<b>{article_count} articles</b><br/>H3 cell: {h3_cell}",
        },
    )

    coverage_map
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Read the pattern carefully

    The map should show an unusually strong concentration around Minnesota. That is not evidence that the Guardian devoted this share of all its reporting to Minnesota.

    It reflects how this demo dataset was built: we selected 250 articles whose text contained the word **“Minnesota.”** The map therefore visualizes the geography inside a deliberately Minnesota-focused sample.

    Coverage elsewhere on the map is still meaningful. Those cells represent other places mentioned in the same stories—for example, opposing sports teams, national political figures, travel, or comparisons with other cities. But every conclusion must account for the rule used to select the source articles.

    This is a useful general lesson for data products: a polished map can faithfully represent its input while the input itself remains selective.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    You now know how to:

    - request H3 coverage cells for a geographic area;
    - choose a display resolution;
    - shade cells by distinct article count; and
    - interpret the result in light of how the dataset was collected.

    A future tutorial can use the [geo-cell drill-down endpoint](https://docs.backfield.news/api/other/geo-cells/list-articles/) to retrieve the articles behind any selected hexagon.
    """)
    return


if __name__ == "__main__":
    app.run()
