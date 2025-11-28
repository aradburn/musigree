Musigree
========

![GitHub License](https://img.shields.io/github/license/aradburn/musigree)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/aradburn/musigree/main/pyproject.toml)
![GitHub Tag](https://img.shields.io/github/v/tag/aradburn/musigree)

Interactive visualization of the **Discogs** database

What is Musigree?
-----------------

**Musigree** is an interactive visualization tool that maps the complex network of relationships between musicians,
bands,
and record labels. It provides a visual representation of the connections within the music industry, helping users
discover new music and understand how artists and labels are interconnected.

All of **Musigree**'s data is derived from the [Discogs](http://www.discogs.com) database, containing:

- 9 million artists
- 2 million labels
- 18 million releases
- Over 100 million different relationships

### Live Demo

Visit the live site at https://musigree.com.

### How to Use

1. Visit the https://musigree.com website
2. Type an artist, band, or label name into the search box
3. Explore the connections in the interactive visualization
4. Click on nodes to see more information
5. Double-click on any circle containing a plus-sign to reveal more connections
6. Zoom in and out using the mouse wheel

### Visualization Legend

- Small circles represent artists
- Large circles represent bands
- Solid lines show artist / band membership and sub-label / parent-label relationships
- Dashed lines show pseudonyms between artists ("also known as" or "AKA" for short)
- Dotted lines show all kinds of other relationships (e.g., "artist X played guitar for artist Y")

The graph shows approximately 100 items at a time for performance reasons. Double-click on nodes with plus-signs
to expand and see more connections.

### Target Audience

- Music enthusiasts and collectors
- Musicians and industry professionals
- Researchers studying musical connections and influences
- Casual users interested in discovering relationships in the music industry

### Features

- Interactive network graph visualization of music industry relationships
- Search functionality to find specific artists, bands, or labels
- Filtering options for different types of relationships
- Expandable nodes to reveal more connections
- Responsive design for desktop and mobile devices
- Detailed information about artists, bands and their relationships

### Technology Stack

#### Frontend

- [D3.js](https://d3js.org): Handles SVG, animation, and force layout of nodes in the graph
- [Bootstrap](http://getbootstrap.com/): For CSS styling
- [Vite](https://vitejs.dev/): For bundling and serving the front-end
- [React](https://reactjs.org): UI framework
- [TypeScript](https://www.typescriptlang.org/): For type safety

#### Backend

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/): FastAPI is a modern, high-performance, web framework
- [SQLAlchemy](https://www.sqlalchemy.org/): ORM for database access
- [Pydantic](https://pydantic-docs.helpmanual.io/): For data validation
- [PostgreSQL](https://www.postgresql.org/): Primary offline database
- [SQLite](https://www.sqlite.org/): For a smaller runtime database
- [Redis](https://redis.io/): For caching and rate limiting

For more details on the database structure and implementation, see the [technical documentation](docs/ABOUT.md).

Contributing
------------

If you notice any omissions or errors in the data, please consider contributing to
the [Discogs database](https://www.discogs.com/) directly, as all the underlying data is sourced from there.

For code contributions:

1. Fork this Github code repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

License
-------

This project is licensed under the terms of the [LICENSE](LICENSE) file.
