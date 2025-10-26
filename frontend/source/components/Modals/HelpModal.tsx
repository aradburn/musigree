/** @jsxImportSource react */
import React from "react";
import { Modal, Button } from "react-bootstrap";

interface HelpModalProps {
    show?: boolean;
    onHide?: () => void;
}

/**
 * Help modal component that displays application usage instructions.
 * This is based on modal-help.html from the original jQuery implementation.
 */
export const HelpModal: React.FC<HelpModalProps> = ({
    show = false,
    onHide = (): void => {
        return;
    },
}): React.ReactElement => {
    const handleClose = (): void => {
        onHide();
    };

    return (
        <Modal id="help-modal" show={show} onHide={handleClose} size="lg">
            <Modal.Header closeButton>
                <Modal.Title>Musigree</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <p>
                    <strong>Musigree</strong> is an interactive visualization of
                    the relationships between musicians, bands and labels.
                </p>

                <p>
                    All of <strong>Musigree</strong>'s data is derived from the{" "}
                    <a
                        href="http://discogs.com"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Discogs.com
                    </a>{" "}
                    database: nearly 9 million artists, 2 million labels, and 17
                    million releases creating a network of nearly 100 million
                    different relationships.
                </p>

                <p>What do all of these symbols mean?</p>

                <ul>
                    <li>Small circles represent artists.</li>
                    <li>Large circles represent bands.</li>
                    <li>Squares represent labels and other companies.</li>
                    <li>Solid lines show band membership.</li>
                    <li>Dashed lines show pseudonyms.</li>
                    <li>Dotted lines show other kinds of relations.</li>
                </ul>

                <p>
                    The graph only shows approximately 100 entities at a time.
                    Double-clicking on any circle containing a plus-sign will
                    follow the graph further to show more connections.
                </p>

                <p>
                    <strong>Musigree</strong> would also be impossible without
                    the generous public data dump that{" "}
                    <a
                        href="http://discogs.com"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Discogs.com
                    </a>{" "}
                    provides monthly.
                </p>

                <p>
                    If something is not working, please file a bug report on{" "}
                    <a
                        href="https://github.com/aradburn/musigree/issues"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Github
                    </a>
                    .
                </p>

                <p>
                    If any artist or label information is missing or incorrect,
                    it can be updated on{" "}
                    <a
                        href="http://discogs.com"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Discogs.com
                    </a>
                    . It may take time, even months, for the updates to be
                    processed in Discogs, then updated here in Musigree
                </p>

                <p>
                    If you are interested in developing{" "}
                    <strong>Musigree</strong>, you can access the code
                    repository on Github at{" "}
                    <a
                        href="https://github.com/aradburn/musigree"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        GitHub.
                    </a>
                </p>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose}>
                    Close
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default HelpModal;
