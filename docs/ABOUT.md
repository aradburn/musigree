About Musigree
================

- Interactive graphing of the relationships between bands, labels and musicians
- Single-page application, using asynchronous calls to a JSON API
- Uses the Discogs XML dump, heavily transformed

The Stack
---------

The front-end:

- [D3](https://d3js.org): handles svg, animation, and force layout of nodes in the graph
- a custom finite state machine for simplifying single-page state
- [React](https://reactjs.org/): for the UI
- [Bootstrap](http://getbootstrap.com/): for CSS and styling
- [Vite](https://vitejs.dev/): for bundling and serving the front-end

The back-end:

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) : web framework
- [SQLAlchemy](https://www.sqlalchemy.org/): to access the database
- [Pydantic](https://pydantic-docs.helpmanual.io/): for data validation
- [PostgreSQL](https://www.postgresql.org/): the primary offline database
- [SQLite](https://www.sqlite.org/): for a smaller runtime database
- [Redis](https://redis.io/): for caching and rate limiting

The DB Structure
----------------

A classic graph-search problem, with two primary tables:

- *Entities*: all artists and labels (the nodes)
- *Relations*: any connection (links) drawn between two entities (including the same one)
- *Roles*: the roles (or credit on the release) for each relation
- *Releases*: the releases (tracks / albums / CDs etc) that the relations are drawn on

The graph-search algorithm
--------------------------

1. Start with an entity
2. Get all relations involving that entity.
3. Get all other entities involved in those relations.
4. Get all relations involving those new entities.
    - `Alias`, `Member Of`, `Sublabel Of` are stored on in the `entities` table
    - All other credit roles require hitting the `relations` table.
    - Some prolific roles (`Released On`, `Compiled On`, `Written-By`) are pruned after distance 1.
5. Repeat getting entities and relations until either:
    - the maximum distance is reached,
    - we run out of entities,
    - or we surpass either the max-entities or max-relations thresholds.
6. Cross-reference all entities with all roles (pre-role-pruning).

Here's the terminal output for the graph-search, starting with Morris Day, and using the roles "Alias", "Member Of"
and "Guitar":

```
Searching around Morris Day...
    Max nodes: 75
    Max links: 225
    Roles: ('Alias', 'Member Of', 'Guitar')
    At distance 0:
        0 old nodes
        0 old links
        1 new nodes
        Retrieving entities
            1-1 of 1
        Retrieving structural relations
        Retrieving relational relations
            1-1 of 1
    At distance 1:
        1 old nodes
        8 old links
        8 new nodes
        Retrieving entities
            1-8 of 8
        Retrieving structural relations
        Retrieving relational relations
            1-8 of 8
    At distance 2:
        9 old nodes
        188 old links
        161 new nodes
        Retrieving entities
            1-161 of 161
        Max nodes: exiting next search loop.
        Retrieving structural relations
        Max links: exiting next search loop.
    At distance 3:
        170 old nodes
        833 old links
        584 new nodes
        Retrieving entities
            1-584 of 584
    Cross-referencing...
        753 & 753
        Cross-referenced: 754 nodes / 1060 links
    Built trellis: 754 nodes / 1060 links
Network query time: 0.6372168064117432
```
