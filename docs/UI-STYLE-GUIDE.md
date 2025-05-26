# Musigree UI Style Guide

## 1. Introduction

This document provides guidelines for maintaining visual consistency across the Musigree application. The application
uses Bootstrap 5 as its core UI framework, with custom theming to maintain a consistent and branded look and feel.

## 2. Brand Colors

### Primary Palette

| Color        | Hex Code  | Usage                                                     |
|--------------|-----------|-----------------------------------------------------------|
| Primary      | `#c0d111` | Primary brand color, used for buttons, links, and accents |
| Secondary    | `#4d8c6f` | Secondary color for UI elements                           |
| Background   | `#1c5a51` | Main background color for sidebar and panels              |
| Text (Dark)  | `#000`    | Text on light backgrounds                                 |
| Text (Light) | `#fff`    | Text on dark backgrounds                                  |

### Additional Colors

| Color                   | Hex Code  | Usage                                          |
|-------------------------|-----------|------------------------------------------------|
| SVG Background          | `#eee`    | Background color for the network visualization |
| Node Tooltip Background | `#ffffcc` | Background for node tooltips                   |
| Link Tooltip Background | `#ffeda0` | Background for link tooltips                   |

## 3. Typography

### Font Families

- Primary Font: "Open Sans", sans-serif
- Icon Font: Bootstrap Icons

### Font Sizes

- Headings:
    - H1: 2.5rem
    - H2: 2rem
    - H3: 1.75rem
    - H4: 1.5rem
    - H5: 1.25rem
    - H6: 1rem
- Body: 1rem
- Small: 0.875rem

### Text Styles

- Links: Primary color (`#c0d111`), no underline by default, underline on hover
- Navbar Title: 18px, centered

## 4. UI Components

### Navbar

- Background: Gradient from `#4d8c6f55` to `#46735ebb`
- Height: 50px
- Layout: Responsive with logo on left, search in center, action buttons on right
- Components: Logo, Title, Search, Random, Help

```html

<Navbar bg="body-tertiary" expand="lg" className="text-body p-0">
    <Container fluid>
        <!-- Brand section -->
        <!-- Navbar title section -->
        <!-- Search section -->
        <!-- Random button section -->
        <!-- Help button section -->
    </Container>
</Navbar>
```

### Sidebar

- Background: `#1c5a51`
- Width: `col-lg-2 col-md-2 col-sm-1 col-1` (responsive)
- Content: Role filters and entity details

### Side Menu Content

- Background: `rgba(#1c5a51, 0.95)` with blur effect
- Width: `min(300px, 25vw)` (responsive)
- Position: Fixed, left edge
- Shadow: `3px 0 10px rgba(0, 0, 0, 0.2)`
- Border: `1px solid lighten($dg-background-color, 10%)`
- Transition: Smooth slide-in effect

### Modals

- Three types: Help, Welcome, Who (About)
- Standard Bootstrap Modal component
- Close button in header

```html

<Modal show="{show}" onHide="{onHide}" centered>
    <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
    </Modal.Header>
    <Modal.Body> {content}</Modal.Body>
    <Modal.Footer>
        <button variant="secondary" onClick="{onHide}">Close</button>
    </Modal.Footer>
</Modal>
```

### Buttons

- Primary: Bootstrap primary with custom color
- Secondary: Bootstrap secondary with custom color
- Icon Buttons: Bootstrap Icons with tooltips

### Form Controls

#### Search Input

- Full width in container
- Placeholder text: "Search for artists, labels, etc."
- Auto-complete dropdown with results

#### Range Slider

- Custom styled thumb and track
- Width: 90%
- Thumb color: `#1c5a51`

```css
input[type="range"]::-webkit-slider-thumb {
    background-color: #4d8c6f;
    height: 1.6rem;
    width: 0.8rem;
}
```

### Tooltips

- Background: `#ffffcc` for regular tooltips
- Text color: `#111`
- Node tooltip border: `#800026`
- Link tooltip background: `#ffeda0`

```html

<OverlayTrigger
    placement="bottom"
    overlay={<Tooltip id="tooltip-id">Tooltip content</Tooltip>}
    >
    <element>Trigger Element</element>
</OverlayTrigger>
```

## 5. Network Visualization

### Network Canvas

- Background: `#eee`
- Full width and height of container
- Interactive with zoom and pan support

### Nodes

- Artist: Circle shape with specific color coding
- Label: Square shape with specific color coding
- Hover effect: Highlight with increased opacity
- Selection effect: Bold outline

### Links

- Default opacity: 0.7
- Types:
    - Solid line: Artist/band membership, parent/sublabel
    - Dashed line: Aliases
    - Dotted line: Other relationships

## 6. Layouts

### Page Layout

- Fixed header with navbar
- Full-height content area
- Sidebar on left (collapsible on small screens)
- Main visualization area

```html

<Container fluid className="vh-100 d-flex flex-column">
    <Header/>
    <Row className="flex-grow-1 overflow-hidden">
        <Sidebar/>
        <Col className="p-0 h-100">
        <NetworkView/>
        </Col>
    </Row>
</Container>
```

### Responsive Behavior

- Desktop: Full sidebar and controls visible
- Tablet: Condensed sidebar with icons only
- Mobile: Collapsible sidebar, stacked controls

## 7. Icons

- Use Bootstrap Icons for consistent look and feel
- Standard icons:
    - Help: `bi-question-circle`
    - Random: `bi-shuffle`
    - Logo: `bi-snow3`
    - Close: `bi-x`
    - Menu: `bi-list`

## 8. Animation and Transitions

- Sidebar transitions: 0.3s ease-in-out
- Hover transitions: 0.2s ease-in-out
- Network transitions: Smooth force-directed graph animations

## 9. Accessibility

- Maintain sufficient color contrast (WCAG AA compliance)
- Provide text alternatives for visual elements
- Support keyboard navigation
- All interactive elements must be focusable

## 10. Implementation Notes

### Bootstrap Integration

- Import Bootstrap CSS: `import "bootstrap/dist/css/bootstrap.min.css";`
- Import React Bootstrap components individually:
  ```js
  import { Container, Row, Col } from "react-bootstrap";
  ```

### SCSS Variables

Maintain custom variables in `musigree.scss`:

```scss
$dg-primary-color: #c0d111;
$dg-secondary-color: #4d8c6f;
$dg-background-color: #1c5a51;
$dg-text-inner-color: #000;
$dg-text-outer-color: #fff;
```

### Component Props

Keep component props consistent:

```tsx
interface ComponentProps {
    className?: string; // For custom styling
    show?: boolean; // For visibility toggling
    onHide?: () => void; // For close handlers
}
```
