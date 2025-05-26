/** @jsxImportSource react */
import React from "react";
import { Modal, Button } from "react-bootstrap";

interface WelcomeModalProps {
    show?: boolean;
    onHide?: () => void;
    isReturnVisitor?: boolean;
}

/**
 * Welcome modal component that displays on first visit.
 * This is based on modal-welcome.html from the original jQuery implementation.
 */
export const WelcomeModal: React.FC<WelcomeModalProps> = ({
    show = false,
    onHide = (): void => {
        return;
    },
    isReturnVisitor = false,
}): React.ReactElement | null => {
    // Don't render the modal for return visitors
    if (isReturnVisitor) {
        return null;
    }

    const handleClose = (): void => {
        onHide();
    };

    return (
        <Modal show={show} onHide={handleClose} size="lg">
            <Modal.Header closeButton>
                <Modal.Title>Hello music lovers!</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <p>
                    Welcome to <strong>Musigree</strong>, an interactive
                    visualization of relationships between artists, bands and
                    labels, based on data from the{" "}
                    <a
                        href="http://discogs.com"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Discogs.com
                    </a>{" "}
                    database.
                </p>

                <p>
                    Use the search box in the right corner to look for a musical
                    artist or label. Click on the <strong>Random</strong>
                    link in the left corner to find a random artist.
                </p>

                <p>
                    The artists and labels are shown as a graph of connected
                    nodes and links. When the graph appears, click and drag the
                    nodes around. Double-click on any node with a plus-sign to
                    re-centre the graph on that node. Use the
                    <em>roles</em> selector in the bottom right corner to show
                    new types of connections.
                </p>

                <p>
                    You can also click on any selected entity's name in the
                    lower left-hand corner to open their{" "}
                    <a
                        href="http://discogs.com"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Discogs.com
                    </a>{" "}
                    profile, or the little eye icon next to their name to pull
                    up a graph of their musical proclivities
                </p>

                <p>
                    Originally made in 2015 by{" "}
                    <a
                        href="https://github.com/josiah-wolf-oberholtzer/musigree"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Josiah Wolf Oberholtzer
                    </a>
                    .
                </p>
                <p>
                    Updated 2023 by{" "}
                    <a
                        href="http://andyradburn.co.uk"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Andy Radburn
                    </a>
                    .
                </p>

                <p>
                    <strong>Musigree</strong> is made with a little help from
                    these great tools and packages:
                </p>

                <ul>
                    <li>
                        <a
                            href="http://python.org"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Python 3
                        </a>
                    </li>
                    <li>
                        <a
                            href="http://peewee.readthedocs.org"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Peewee
                        </a>
                    </li>
                    <li>
                        <a
                            href="http://d3js.org/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            D3
                        </a>{" "}
                        and{" "}
                        <a
                            href="http://getbootstrap.com"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Bootstrap CSS
                        </a>
                    </li>
                    <li>
                        <a
                            href="http://machina-js.org/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Machina-JS
                        </a>
                    </li>
                    <li>
                        <a
                            href="http://flask.pocoo.org"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Flask
                        </a>
                        ,
                        <a
                            href="http://gunicorn.org/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Gunicorn
                        </a>{" "}
                        and
                        <a
                            href="http://supervisord.org/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            supervisor.d
                        </a>
                    </li>
                </ul>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="primary" onClick={handleClose}>
                    Start
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default WelcomeModal;
