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
    # Tutorial 201: Create a coverage map with Backfield and H3

    In [Tutorial 101](./101_hello_backfield.py), we logged into the API and performed some basic searches. Now we will use Backfield data to build a map of coverage across the U.S.

    In addition to generating other geographic data, like points and polygons, Backfield assigns an [H3 cell](https://h3geo.org/) to each location it geocodes. H3 cells give us a consistent and visually friendly way to group nearby locations and count the articles that mention them.
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

    For this tutorial, we will use Backfield's [geo-cell coverage endpoint](https://docs.backfield.news/api/other/geo-cells/coverage/), which is a shortcut for producing counts of articles whose locations fall within H3 cells at a given resolution.

    The box takes the format:

    ```text
    minimum longitude, minimum latitude, maximum longitude, maximum latitude
    ```

    We will set ours around the contiguous United States.

    H3 supports resolutions from 0 (very large hexagons) to 15 (very small hexagons). We will request **resolution 4**, where an average hexagon covers about 1,770 square kilometers. These large regional cells make broad national patterns easier to see. See the [H3 resolution table](https://h3geo.org/docs/core-library/restable/) for other sizes.
    """)
    return


@app.cell
def _():
    # West, south, east, and north edges of the contiguous United States.
    US_BBOX = "-125,24,-66.5,49.5"

    # Lower H3 resolutions produce larger hexagons. Resolution 4 works well
    # for a map showing the entire contiguous United States.
    H3_RESOLUTION = 4
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
    return (cells,)


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
    ## Step 3: Match the resolution to the geography

    Not every location represents the same amount of physical space. Backfield's [`location_type` vocabulary](https://docs.backfield.news/api/taxonomy/entity-meta/locations/) includes:

    - precise, point-like locations such as `address`, `place`, `intersection_road`, and `intersection_highway`;
    - intermediate areas such as `neighborhood` and `political_district`; and
    - broad areas such as `city`, `county`, `state`, and `country`.

    The type helps describe a location, but Backfield uses the actual geometry's footprint to choose its **native H3 resolution**. A point can be stored at a fine resolution. A large city polygon needs a coarser resolution that better represents its size.

    The [coverage endpoint's size gate](https://docs.backfield.news/api/other/geo-cells/coverage/#resolution-rollup-and-size-gate) uses that native resolution:

    - Fine locations can roll up into larger display cells. An address can contribute to a city-sized hexagon.
    - Broad locations are excluded from displays that are more precise than their footprint. A city should not appear to belong to one tiny neighborhood or block simply because its polygon has a center point.

    Backfield does not fill every tiny hexagon covered by a city polygon. It assigns the location a representative cell at an appropriate native resolution, then includes or excludes it according to the map's display resolution.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Compare broad and precise locations

    We can demonstrate the size gate by requesting two location types at two resolutions:

    - Resolution 4 uses large regional hexagons.
    - Resolution 8 uses hexagons smaller than one square kilometer, roughly a neighborhood-scale view.

    The demo project does not contain enough addresses or intersections for a useful comparison, so we will compare `place` points with `city` polygons. The same principle applies to other precise and broad geography types.
    """)
    return


@app.cell
def _(PROJECT_SLUG, US_BBOX, get, mo):
    _populated_cells = {}

    # Use the same bounding box for every request so only the location type
    # and display resolution change.
    for _location_type in ("place", "city"):
        for _resolution in (4, 8):
            _result = get(
                f"/projects/{PROJECT_SLUG}/articles/geo-cells",
                bbox=US_BBOX,
                resolution=_resolution,
                location_type=_location_type,
            )
            _populated_cells[(_location_type, _resolution)] = len(
                _result["cells"]
            )

    # A small table makes the effect of changing resolution easier to compare.
    _rows = [
        "| Location type | Resolution 4 | Resolution 8 |",
        "|---|---:|---:|",
        (
            "| Place | "
            f"{_populated_cells[('place', 4)]} cells | "
            f"{_populated_cells[('place', 8)]} cells |"
        ),
        (
            "| City | "
            f"{_populated_cells[('city', 4)]} cells | "
            f"{_populated_cells[('city', 8)]} cells |"
        ),
    ]
    mo.md("\n".join(_rows))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Point-like `place` locations remain available at the finer resolution and spread into more distinct cells. Most city polygons disappear at resolution 8 because that display implies more precision than their geometry supports.

    This behavior helps a zoomable map stay honest. As a reader zooms in, precise addresses and venues remain visible while broad city, state, and country references drop away.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Turn counts into colors

    We will shade low-count hexagons yellow and high-count hexagons red.

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
                    int(255 - 66 * _strength),
                    int(237 - 237 * _strength),
                    int(160 - 122 * _strength),
                    190,
                ],
            }
        )
    return (map_cells,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Draw the map

    [pydeck](https://deckgl.readthedocs.io/en/latest/) can draw H3 indexes directly with its `H3HexagonLayer`. We give it the cell index, the color calculated above, and the original article count for the hover tooltip.

    Yellow hexagons have fewer articles, while darker red hexagons have more. Hover over any hexagon to see its exact count.
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
    ## Step 6: Interpreting the results

    Apart from the expected coverage density around the coasts, there is also an unusual concentration around Minnesota. This is not an accident. The subset of articles we used from the Guardian dataset is a list of 250 articles that contains the word "Minnesota".

    Still, the map shows the wide breadth of even a small amount of coverage. Each hexagon represents an area being mentioned in an article, in any capacity. It might refer to a sports team, a politician, or even a small and seemingly insignificant anecdote.

    One thing we've noticed working with metro and regional publishers is that often their coverage touches on a broader swath of their community than they might expect. If a crime victim is from a given neighborhood, we might not learn that until several paragraphs deep into the article — but to their friends and neighbors, that's still news.
    """)
    return


if __name__ == "__main__":
    app.run()
