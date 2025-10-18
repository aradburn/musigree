# Musigree: Product Requirements Document

## 1. Introduction

### 1.1 Purpose

Musigree is an interactive visualization tool for the Discogs music database, enabling users to explore the complex
network of relationships between artists, bands, and labels. It provides a visual representation of the connections
within the music industry, helping users discover new music and understand how artists and labels are interconnected.

### 1.2 Project Scope

The application visualizes data derived from the Discogs database, covering:

- 10 million artists
- 2 million labels
- 17 million releases
- Over 100 million different relationships

### 1.3 Target Audience

- Music enthusiasts and collectors
- Musicians and industry professionals
- Researchers studying musical connections and influences
- Casual users interested in discovering relationships in the music industry

## 2. Product Overview

### 2.1 Product Vision

To create the most comprehensive and user-friendly visualization of the music industry's interconnected relationships,
making it easy for users to discover and explore connections between artists, bands, and labels.

### 2.2 Key Features

- Interactive network graph visualization of music industry relationships
- Search functionality to find specific artists, bands, or labels
- Filtering options for different types of relationships
- Expandable nodes to reveal more connections
- Responsive design for desktop and mobile devices
- Detailed information about entities and their relationships

### 2.3 User Stories

1. As a music enthusiast, I want to search for my favorite artist and see all their connections so I can discover
   related artists and projects.
2. As a researcher, I want to filter connections by relationship types so I can focus on specific aspects of music
   industry networks.
3. As a casual user, I want an intuitive interface that makes it easy to explore music connections without requiring
   special knowledge.
4. As a collector, I want to see detailed information about artists and labels to enhance my understanding of the music
   industry.
5. As a mobile user, I want the visualization to work well on my device so I can explore music connections on the go.

## 3. Functional Requirements

### 3.1 Core Functionality

#### 3.1.1 Network Visualization

- Display entities (artists, bands, labels) as nodes in a force-directed graph
- Represent different types of relationships with distinct line styles:
    - Solid lines: artist/band membership and sublabel/parent-label relationships
    - Dashed lines: pseudonyms between artists (AKA)
    - Dotted lines: other relationships (e.g., artist played guitar for another artist)
- Support interactive zooming and panning
- Limit visualization to a reasonable number of entities at a time for performance (depends on screen size)
- Support expanding nodes (via double-click) to reveal additional connections (relationships)

#### 3.1.2 Search

- Enable users to search for artists, bands, and labels by name
- Display search results with entity types and ordered by relevance
- Support partial name matching and fuzzy search
- Provide a random entity option for discovery

#### 3.1.3 Filtering

- Allow filtering by relationship types (e.g., Member Of, Alias)
- Support multiple filter selections
- Update visualization immediately when filters change
- Provide a clear indication of active filters
- Allow users to reset filters easily
- Provide a "Show All" option to reset all filters
- Allow users to hide/show specific relationship types
- Provide a "Show Only" option to focus on specific relationship types
- Allow users to hide entities by right-clicking on them and selecting "Hide"

#### 3.1.4 Entity Information

- Display detailed information about selected entities
- Show name, type, and all relationships
- Provide links to Discogs for additional information

### 3.2 User Interface Requirements

#### 3.2.1 Layout

- Header with application name, search bar, random and help options
- Sidebar for filter controls, entity information and network force settings
- Main visualization area of nodes and links
- Responsive design that adapts to different screen sizes

#### 3.2.2 Modals

- Welcome modal with instructions for first-time visitors
- Help modal explaining visualization symbols and controls
- Information modal about the application and its creators

#### 3.2.3 Controls

- Zoom via mouse wheel, and pan via mouse drag for the visualization
- Search input with autocomplete
- Filter checkboxes or dropdown menus
- Node selection (expansion) via double-click, node becomes new center of the graph

## 4. Non-Functional Requirements

### 4.1 Performance

- Load visualization within 5 seconds for typical queries
- Support smooth interaction with up to 100 nodes
- Optimize API responses to minimize load times
- Implement caching for frequently accessed data

### 4.2 Scalability

- Handle concurrent users effectively
- Scale to support growth in the Discogs database
- Optimize database queries for large datasets

### 4.3 Security

- Secure API endpoints with rate limiting to prevent abuse
- Implement input validation to prevent injection attacks
- Secure cross-origin requests

### 4.4 Accessibility

- Ensure visualization is accessible to users with disabilities
- Support keyboard navigation
- Provide text alternatives for visual elements
- Follow WCAG 2.1 guidelines

### 4.5 Compatibility

- Support modern browsers (Chrome, Firefox, Safari, Edge)
- Responsive design for mobile and desktop devices
- Graceful degradation for older browsers

## 5. Technical Architecture

### 5.1 Frontend

- **Framework**: React with TypeScript
- **Visualization**: D3.js for network force graph
- **UI Components**: React Bootstrap
- **Build Tool**: Vite
- **Testing**: Vitest for unit tests, Playwright for E2E tests

### 5.2 Backend

- **Framework**: FastAPI (Python)
- **Database**: SQLAlchemy with PostgreSQL and SQLite
- **API**: RESTful endpoints
- **Caching**: Redis for performance optimization
- **Data Processing**: Custom ETL processes for Discogs data, offline database for intermediate processing, a smaller
  runtime database for optimized runtime use

### 5.3 Data Flow

1. Frontend sends requests to backend API endpoints
2. Backend queries database for entity and relationship data
3. Data is transformed into graph format and returned to frontend
4. Frontend renders network visualization using D3.js
5. User interactions trigger new requests or updates to the visualization

## 6. Data Requirements

### 6.1 Data Sources

- Discogs database dump (primary source)
- User preferences (stored locally)

### 6.2 Data Storage

- Relational database for entities and relationships
- Redis for caching frequently accessed data
- Local storage for user preferences

### 6.3 Data Processing

- ETL pipeline to extract, transform, and load Discogs data
- Natural language processing for search optimization
- Graph algorithms for relationship analysis

## 7. User Experience

### 7.1 User Flow

1. User arrives at the website
2. First-time visitors see welcome modal with instructions
3. User searches for an artist, band, or label
4. Results are displayed as interactive visualization
5. User can explore connections by clicking on nodes
6. User can filter relationships to focus on specific types
7. User can expand nodes to reveal more connections

### 7.2 Design Guidelines

- Clean, minimalist interface focusing on the visualization
- Intuitive controls that don't require extensive learning
- Consistent visual language for entity types and relationships
- Responsive design that works well on all devices
- Helpful tooltips and instructions for new users

## 8. Implementation Timeline

### 8.1 Phase 1: Core Functionality

- Setup project architecture and infrastructure
- Implement basic network visualization
- Develop search functionality
- Create API endpoints for entity and relationship data

### 8.2 Phase 2: Enhanced Features

- Add filtering options for relationships
- Implement node expansion functionality
- Optimize performance for large datasets
- Add detailed entity information display

### 8.3 Phase 3: Refinement

- Improve user interface and experience
- Enhance mobile responsiveness
- Optimize search algorithm
- Add additional visualization options

### 8.4 Phase 4: Release

- Final testing and bug fixing
- Performance optimization
- Documentation
- Deployment to production environment

## 9. Success Metrics

### 9.1 Performance Metrics

- Page load time < 5 seconds
- API response time < 2 second
- Visualization rendering time < 2 seconds
- Support for up to 100 concurrent users

### 9.2 User Metrics

- User engagement (time spent exploring)
- Number of searches performed
- Number of nodes displayed
- Return visitor rate

### 9.3 Technical Metrics

- Code test coverage > 80%
- Zero critical or severe security vulnerabilities
- Accessibility score > 90%
- Browser compatibility across major platforms and devices

## 10. Appendix

### 10.1 Glossary

- **Entity**: An artist, band, or label in the Discogs database
- **Node**: Visual representation of an entity in the network graph
- **Link**: An edge connection between two nodes representing a relationship
- **Relationship**: Connection between two entities (e.g., membership, collaboration)

### 10.2 References

- [Discogs API Documentation](https://www.discogs.com/developers/)
- [Python Documentation](https://docs.python.org/3/)
- [D3.js Documentation](https://d3js.org/)
- [React Documentation](https://react.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Bootstrap Documentation](https://react-bootstrap.github.io/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Redis Documentation](https://redis.io/)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
-
