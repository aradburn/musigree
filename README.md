# Musigree

Interactive visualization of the Discogs Database

## What is Musigree?

Musigree is an interactive visualization tool that maps the complex network of relationships between musicians, bands,
and record labels. It provides a visual representation of the connections within the music industry, helping users
discover new music and understand how artists and labels are interconnected.

All of Musigree's data is derived from the [Discogs](http://www.discogs.com) musigreey database, containing:

- 9 million artists
- 2 million labels
- 18 million releases
- Over 100 million different relationships

## Live Demo

Visit the live site at https://musigree.azurewebsites.net.

## How to Use

1. Visit the website
2. Type an artist, band, or label name into the search box
3. Explore the connections in the interactive visualization
4. Click on nodes to see more information
5. Double-click on any circle containing a plus-sign to reveal more connections

### Visualization Legend

- Small circles represent artists
- Large circles represent bands
- Solid lines show artist/band membership and sublabel/parent-label relationships
- Dashed lines show pseudonyms between artists (_AKA_)
- Dotted lines show all kinds of other relationships (e.g., "artist X played guitar for artist Y")

The graph shows at most 100 entities at a time for performance reasons. Double-click on nodes with plus-signs to expand
and see more connections.

## Target Audience

- Music enthusiasts and collectors
- Musicians and industry professionals
- Researchers studying musical connections and influences
- Casual users interested in discovering relationships in the music industry

## Features

- Interactive network graph visualization of music industry relationships
- Search functionality to find specific artists, bands, or labels
- Filtering options for different types of relationships
- Expandable nodes to reveal more connections
- Responsive design for desktop and mobile devices
- Detailed information about entities and their relationships

## Technology Stack

### Frontend

- [D3.js](https://d3js.org): Handles SVG, animation, and force layout of nodes in the graph
- [Machina-JS](http://machina-js.org/): A finite state machine for simplifying single-page state
- [jQuery](https://jquery.com): For event binding
- [Twitter Typeahead](https://github.com/twitter/typeahead.js/): For entity lookups
- [Bootstrap](http://getbootstrap.com/): For CSS styling
- [Vite](https://vitejs.dev/): For bundling and serving the front-end
- [React](https://reactjs.org): UI framework (in newer versions)
- [TypeScript](https://www.typescriptlang.org/): For type safety

### Backend

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/): FastAPI is a modern, high-performance, web framework
- [SQLAlchemy](https://www.sqlalchemy.org/): ORM for database access
- [Pydantic](https://pydantic-docs.helpmanual.io/): For data validation
- [PostgreSQL](https://www.postgresql.org/): Primary offline database
- [SQLite](https://www.sqlite.org/): For a smaller runtime database
- [Redis](https://redis.io/): For caching and rate limiting

## Development

The project uses `uv` and `venv` to manage the Python environment and dependencies.

### Prerequisites

- Python 3.13+
- Node.js 22+ (for frontend development)
- PostgreSQL (for full database) and/or SQLite (for development and runtime)
- Redis (optional, for caching)

### Setting Up the Development Environment

#### Backend Setup

1. Create a virtual environment:

    ```
    python3 -m venv venv
    ```

2. Activate the virtual environment:

    ```
    # On Unix or MacOS
    source venv/bin/activate

    # On Windows
    venv\Scripts\activate
    ```

3. Install dependencies:

    ```
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

#### Frontend Setup

Navigate to the frontend directory and install dependencies:

```
cd frontend
npm install
```

### Running the Application

1. Start the backend server:

    ```
    python wsgi.py
    ```

2. Start the frontend development server:

    ```
    cd frontend
    npm run dev
    ```

3. Visit `http://localhost:5000` in your browser.

### Database Structure

Musigree uses a graph database structure with two primary tables:

- **Entities**: All artists and labels
- **Relations**: Connections between entities

For more details on the database structure and implementation, see the [technical documentation](docs/ABOUT.md).

## Contributing

If you notice any omissions or errors in the data, please consider contributing to
the [Discogs database](https://www.discogs.com/) directly, as all our data is sourced from there.

For code contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
