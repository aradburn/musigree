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
        <Modal id="welcome-modal" show={show} onHide={handleClose} size="lg">
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
                    artist or label.
                </p>
                <p>
                    Click on the <strong>Random</strong> link in the left corner
                    to find a random artist.
                </p>
                <p>
                    The artists, bands and labels are shown as a graph of
                    connected nodes and links.
                </p>
                <p>
                    When the graph appears, click and drag the nodes around.
                    Double-click on any node with a plus-sign to re-centre the
                    graph on that node. The mouse wheel zooms the network in and
                    out. Use the <em>roles</em> selector in the right hand side
                    panel to show new types of connections.
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
