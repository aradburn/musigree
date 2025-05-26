/** @jsxImportSource react */
import React from "react";
import { Modal, Button } from "react-bootstrap";

interface WhoModalProps {
    show?: boolean;
    onHide?: () => void;
}

/**
 * "Who made this" modal component that displays information about the creators.
 * This is based on modal-who.html from the original jQuery implementation.
 */
export const WhoModal: React.FC<WhoModalProps> = ({
    show = false,
    onHide = (): void => {
        return;
    },
}): React.ReactElement => {
    const handleClose = (): void => {
        onHide();
    };

    return (
        <Modal show={show} onHide={handleClose}>
            <Modal.Header closeButton>
                <Modal.Title>Who made this?</Modal.Title>
            </Modal.Header>
            <Modal.Body>
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
                    You can fork <strong>Musigree</strong> on{" "}
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

export default WhoModal;
