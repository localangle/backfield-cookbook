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
    # Tutorial 302: Build an entity knowledge graph

    Backfield links article mentions to canonical people in Stylebook. Stylebook can also maintain explicit relationships between those people and other canonical entities: one official supports another, works for an organization, represents a place, and so on.

    In this tutorial we will turn those relationships into a small exploratory knowledge graph:

    1. Find people classified as elected officials, government officials or political staff.
    2. Load their explicit Stylebook connections, including connected organizations and locations.
    3. Collapse repeated relationships between the same pair into one graph edge.
    4. Explore the graph visually.

    The graph will contain those people, the organizations and locations directly tied to them, and their explicit Stylebook relationships. Articles will **not** become nodes or edges.
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
    import networkx as nx
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

    return PROJECT_SLUG, get_all, nx


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Choose a political cohort

    The canonical [people endpoint](https://docs.backfield.news/api/people/search/) can filter records by `person_type`. We will combine three types:

    - `elected_official` — elected officeholders;
    - `government_official` — appointed or career government officials; and
    - `political_staff` — staff to elected or political officials.

    Setting `min_mentions=1` leaves out Stylebook records that have not appeared in this project. The response includes project-level mention and story counts, which we will use to size nodes later.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get_all):
    PERSON_TYPES = (
        "elected_official",
        "government_official",
        "political_staff",
    )
    selected_entities = {}
    for _person_type in PERSON_TYPES:
        _people = get_all(
            f"/projects/{PROJECT_SLUG}/people/",
            person_type=_person_type,
            min_mentions=1,
        )
        for _person in _people:
            _node_key = ("person", _person["id"])
            selected_entities[_node_key] = {
                "entity_type": "person",
                "person_type": _person["person_type"],
                "canonical_id": _person["id"],
                "slug": _person["slug"],
                "label": _person["label"],
                "title": _person["title"],
                "affiliation": _person["affiliation"],
                "mention_count": _person["counts"]["mentions"],
                "article_count": _person["counts"]["stories"],
            }

    print(f"Selected {len(selected_entities):,} canonical people.")
    for _person_type in PERSON_TYPES:
        _count = sum(
            stats["person_type"] == _person_type
            for stats in selected_entities.values()
        )
        print(f"- {_person_type.replace('_', ' ').title()}: {_count}")

    return PERSON_TYPES, selected_entities


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Load explicit Stylebook connections

    Canonical [people](https://docs.backfield.news/api/people/connections/) have a `/connections` endpoint. A connection has:

    - two canonical entity endpoints;
    - a directional **nature**, such as `works_for`, `member_of` or `supports`; and
    - an optional human-readable **description**.

    There is no project-wide connection export, so we request connections for each selected person. The same connection can be returned from both endpoints. We first deduplicate by connection ID, then keep:

    - connections between two people in our political cohort; and
    - connections from a cohort member to any organization or location.

    That gives organizations and locations useful context without expanding into unrelated parts of Stylebook. People outside the three selected types are not added.

    One important limitation: Stylebook retains evidence for inferred connections internally, but the public connection response does not expose that evidence. Descriptions are useful context, but they are not source evidence and we will not label them that way.
    """)
    return


@app.cell
def _(PROJECT_SLUG, get_all, selected_entities):
    connections_by_id = {}
    for (_, _canonical_id) in selected_entities:
        _path = f"/projects/{PROJECT_SLUG}/people/{_canonical_id}/connections"
        for _connection in get_all(_path):
            connections_by_id[_connection["id"]] = _connection

    selected_keys = set(selected_entities)
    context_types = {"organization", "location"}
    induced_connections = []
    graph_entities = dict(selected_entities)

    for _connection in connections_by_id.values():
        _from_key = (
            _connection["from_entity_type"],
            _connection["from_entity_id"],
        )
        _to_key = (
            _connection["to_entity_type"],
            _connection["to_entity_id"],
        )
        _selected_pair = _from_key in selected_keys and _to_key in selected_keys
        _selected_to_context = (
            _from_key in selected_keys and _to_key[0] in context_types
        ) or (
            _to_key in selected_keys and _from_key[0] in context_types
        )
        if not (_selected_pair or _selected_to_context):
            continue

        induced_connections.append(_connection)
        for _side, _node_key in (("from", _from_key), ("to", _to_key)):
            if _node_key[0] not in context_types:
                continue
            graph_entities.setdefault(
                _node_key,
                {
                    "entity_type": _node_key[0],
                    "person_type": None,
                    "canonical_id": _node_key[1],
                    "slug": None,
                    "label": _connection[f"{_side}_label"],
                    "title": None,
                    "affiliation": None,
                    "mention_count": None,
                    "article_count": None,
                },
            )

    print(
        f"Loaded {len(connections_by_id):,} unique connections touching the "
        f"selected people; {len(induced_connections):,} connect cohort members "
        "to one another or to an organization or location."
    )
    for _entity_type in ("person", "organization", "location"):
        _count = sum(
            data["entity_type"] == _entity_type
            for data in graph_entities.values()
        )
        print(f"- {_entity_type.title()} nodes: {_count}")

    return graph_entities, induced_connections


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Collapse relationships into graph edges

    Stylebook can contain more than one connection between a pair. Two people might both cooperate and oppose one another in different contexts, or separate connection records might explain different aspects of a person's affiliation with an organization.

    Drawing each record as a separate line produces a noisy multigraph. We instead create one undirected visual edge for each unordered pair and preserve the detail as edge attributes:

    - `relationship_count` — connection records represented by the edge;
    - `natures` — unique relationship types;
    - `descriptions` — unique explanatory descriptions; and
    - `relationships` — the original direction, nature, description and connection ID.

    The graph is undirected for neighborhood and path exploration. Direction is not discarded; it remains available inside `relationships`.
    """)
    return


@app.cell
def _(graph_entities, induced_connections, nx):
    from collections import defaultdict as _defaultdict

    grouped_edges = _defaultdict(
        lambda: {
            "connection_ids": set(),
            "natures": set(),
            "descriptions": set(),
            "relationships": [],
        }
    )

    for _connection in induced_connections:
        _from_key = (
            _connection["from_entity_type"],
            _connection["from_entity_id"],
        )
        _to_key = (
            _connection["to_entity_type"],
            _connection["to_entity_id"],
        )
        _pair = tuple(sorted((_from_key, _to_key)))
        _edge = grouped_edges[_pair]
        _edge["connection_ids"].add(_connection["id"])

        if _connection["nature"]:
            _edge["natures"].add(_connection["nature"])
        if _connection["description"]:
            _edge["descriptions"].add(_connection["description"])

        _edge["relationships"].append(
            {
                "connection_id": _connection["id"],
                "from": _from_key,
                "to": _to_key,
                "nature": _connection["nature"],
                "description": _connection["description"],
            }
        )

    collapsed_edges = []
    for (_from_key, _to_key), _edge in grouped_edges.items():
        collapsed_edges.append(
            {
                "from": _from_key,
                "to": _to_key,
                "relationship_count": len(_edge["connection_ids"]),
                "connection_ids": sorted(_edge["connection_ids"]),
                "natures": sorted(_edge["natures"]),
                "descriptions": sorted(_edge["descriptions"]),
                "relationships": sorted(
                    _edge["relationships"],
                    key=lambda relationship: relationship["connection_id"],
                ),
            }
        )

    entity_graph = nx.Graph()
    for _node_key, _stats in graph_entities.items():
        entity_graph.add_node(_node_key, **_stats)

    for _edge in collapsed_edges:
        entity_graph.add_edge(
            _edge["from"],
            _edge["to"],
            relationship_count=_edge["relationship_count"],
            connection_ids=_edge["connection_ids"],
            natures=_edge["natures"],
            descriptions=_edge["descriptions"],
            relationships=_edge["relationships"],
        )

    _connected_nodes = sum(
        1 for node in entity_graph if entity_graph.degree(node) > 0
    )
    _collapsed_count = sum(
        edge["relationship_count"] - 1 for edge in collapsed_edges
    )
    print(
        f"The graph has {entity_graph.number_of_nodes()} nodes, "
        f"{entity_graph.number_of_edges()} edges and {_connected_nodes} "
        f"connected nodes."
    )
    print(f"Collapsed {_collapsed_count} additional relationships onto existing edges.")

    return collapsed_edges, entity_graph


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Explore the network

    Node size represents the number of project articles mentioning a person. Connected organizations and locations use a fixed size because the connection response does not include their article counts. Color distinguishes all five node types. Hover over a node for details or an edge for all of its collapsed natures and descriptions.

    Most records in this cohort do not have an explicit connection to another cohort member. We hide those isolates by default so the network structure is easier to see.

    The controls filter the graph already held in memory. They do not make more Backfield requests.
    """)
    return


@app.cell
def _(PERSON_TYPES, entity_graph, mo):
    person_type_filter = mo.ui.multiselect(
        options=list(PERSON_TYPES),
        value=list(PERSON_TYPES),
        label="Person types",
    )
    context_type_filter = mo.ui.multiselect(
        options=["organization", "location"],
        value=["organization", "location"],
        label="Connected context",
    )
    nature_options = sorted(
        {
            nature
            for _, _, edge in entity_graph.edges(data=True)
            for nature in edge["natures"]
        }
    )
    nature_filter = mo.ui.dropdown(
        options=["All relationships", *nature_options],
        value="All relationships",
        label="Relationship nature",
    )
    node_search = mo.ui.text(
        value="",
        label="Highlight entity",
        placeholder="e.g. Trump, Senate, Minnesota",
    )
    show_isolates = mo.ui.checkbox(
        value=False,
        label="Show people without a connection inside this cohort",
    )

    mo.vstack(
        [
            mo.hstack(
                [person_type_filter, context_type_filter, nature_filter],
                justify="start",
                gap=1.5,
            ),
            mo.hstack([node_search, show_isolates], justify="start", gap=1.5),
        ],
        gap=1,
    )
    return (
        context_type_filter,
        nature_filter,
        node_search,
        person_type_filter,
        show_isolates,
    )


@app.cell
def _(
    context_type_filter,
    entity_graph,
    mo,
    nature_filter,
    node_search,
    nx,
    person_type_filter,
    show_isolates,
):
    import html as _html
    import math as _math

    from pyvis.network import Network as _Network

    _allowed_person_types = set(person_type_filter.value)
    _allowed_context_types = set(context_type_filter.value)
    _allowed_nodes = {
        node
        for node, data in entity_graph.nodes(data=True)
        if (
            data["entity_type"] == "person"
            and data["person_type"] in _allowed_person_types
        )
        or (
            data["entity_type"] in _allowed_context_types
        )
    }
    filtered_graph = entity_graph.subgraph(_allowed_nodes).copy()

    if nature_filter.value != "All relationships":
        _remove_edges = [
            (left, right)
            for left, right, data in filtered_graph.edges(data=True)
            if nature_filter.value not in data["natures"]
        ]
        filtered_graph.remove_edges_from(_remove_edges)

    if not show_isolates.value:
        filtered_graph.remove_nodes_from(list(nx.isolates(filtered_graph)))

    _colors = {
        "elected_official": "#4f7cac",
        "government_official": "#4f9968",
        "political_staff": "#d28b34",
        "organization": "#8f5da2",
        "location": "#2a9d8f",
    }
    _query = node_search.value.strip().lower()
    _network = _Network(
        height="680px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#24292f",
        cdn_resources="in_line",
        directed=False,
    )

    for _node, _data in filtered_graph.nodes(data=True):
        _matches = bool(_query and _query in _data["label"].lower())
        _node_id = f"{_node[0]}:{_node[1]}"
        _node_type = _data["person_type"] or _data["entity_type"]
        _title_lines = [
            _data["label"],
            f"Type: {_node_type.replace('_', ' ').title()}",
        ]
        if _data["article_count"] is not None:
            _title_lines.extend(
                [
                    f"Project articles: {_data['article_count']}",
                    f"Mentions: {_data['mention_count']}",
                ]
            )
        _title_lines.append(f"Graph degree: {filtered_graph.degree(_node)}")
        _title = "\n".join(_title_lines)
        _network.add_node(
            _node_id,
            label=_data["label"],
            title=_title,
            color="#d94841" if _matches else _colors[_node_type],
            size=(
                12 + 5 * _math.log1p(_data["article_count"])
                if _data["article_count"] is not None
                else 16
            ),
            borderWidth=5 if _matches else 1,
        )

    for _left, _right, _data in filtered_graph.edges(data=True):
        _nature_text = ", ".join(_data["natures"]) or "Unspecified"
        _description_text = "\n\n".join(_data["descriptions"])
        _edge_title = (
            f"Natures: {_nature_text}\n"
            f"Connection records: {_data['relationship_count']}"
        )
        if _description_text:
            _edge_title += f"\n\nDescriptions:\n{_description_text}"

        _network.add_edge(
            f"{_left[0]}:{_left[1]}",
            f"{_right[0]}:{_right[1]}",
            title=_edge_title,
            label=_nature_text if len(_data["natures"]) == 1 else "",
            width=1 + _math.log1p(_data["relationship_count"]),
        )

    _network.set_options(
        """
        {
          "interaction": {"hover": true, "navigationButtons": true},
          "nodes": {"shape": "dot", "font": {"size": 15}},
          "edges": {
            "color": {"color": "#a8adb3", "highlight": "#57606a"},
            "font": {"size": 10, "align": "middle"},
            "smooth": {"type": "continuous"}
          },
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -4200,
              "centralGravity": 0.18,
              "springLength": 150,
              "springConstant": 0.035
            },
            "stabilization": {"iterations": 300}
          }
        }
        """
    )

    _graph_html = _network.generate_html(notebook=False)
    _iframe = (
        '<iframe title="Entity knowledge graph" '
        'style="width:100%;height:700px;border:1px solid #d0d7de;'
        'border-radius:8px;background:white" '
        f'srcdoc="{_html.escape(_graph_html, quote=True)}"></iframe>'
    )

    mo.vstack(
        [
            mo.md(
                f"Showing **{filtered_graph.number_of_nodes()} nodes** and "
                f"**{filtered_graph.number_of_edges()} edges**. "
                "Blue = elected official; green = government official; "
                "orange = political staff; purple = organization; "
                "teal = location."
            ),
            mo.Html(_iframe),
        ]
    )
    return (filtered_graph,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What this graph can—and cannot—say

    This graph supports directories, relationship explainers, discovery tools, background research and graph-assisted recommendations. It can reveal hubs, brokers, communities and paths that are hard to see in a list of records.

    Its claims remain precise:

    - primary nodes are canonical people in the three selected person types;
    - organization and location nodes are included only when directly connected to one of those people;
    - edges are maintained Stylebook connections;
    - natures and descriptions come from those connection records; and
    - project articles only determine whether a person has appeared, not whether an edge exists.

    The graph does **not** prove that a relationship was reported in a particular article. Supporting passages are not available on the public connections endpoint. An application that needs citation-level provenance should store that evidence separately or use a different, explicitly labeled co-mention graph.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    Try changing `PERSON_TYPES`, hiding one kind of context node, showing the unconnected records, or filtering to one relationship nature. A production application could cache the graph, let editors inspect directional relationship details, or combine these graph features with search and recommendation ranking.

    Useful references:

    - [Entities overview](https://docs.backfield.news/api/entities/)
    - [List and search people](https://docs.backfield.news/api/people/search/)
    - [People types](https://docs.backfield.news/api/taxonomy/entity-meta/people/)
    - [People connections](https://docs.backfield.news/api/people/connections/)
    - [Organizations](https://docs.backfield.news/api/organizations/)
    - [Locations](https://docs.backfield.news/api/locations/)
    """)
    return


if __name__ == "__main__":
    app.run()
