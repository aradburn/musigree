/* @jsxImportSource react */

import React from "react";
import { Navbar, Container, OverlayTrigger, Tooltip } from "react-bootstrap";
import { SearchInput } from "../Search";
import { FSM } from "../../constants";
import { version } from "../../version";

interface HeaderProps {
    onShowHelp?: () => void;
    onShowWho?: () => void;
}

/**
 * Header UI component.
 */
export const Header: React.FC<HeaderProps> = ({ onShowHelp, onShowWho }) => {
    const handleRandom = (e: React.MouseEvent<HTMLDivElement>): void => {
        e.preventDefault();
        // Dispatch the REQUEST_RANDOM event to trigger the FSM transition
        const event = new CustomEvent(FSM.EVENTS.REQUEST_RANDOM, {
            bubbles: true,
        });
        document.dispatchEvent(event);
    };

    return (
        <Navbar
            id="nav-top"
            bg="body-tertiary"
            expand="lg"
            className="text-body p-0"
        >
            <Container fluid>
                {/* Brand section */}
                <div className="px-2 py-0 col-lg-2 col-md-2 col-sm-1 col-1 order-1 order-md-1">
                    <div
                        className="d-flex flex-row navbar-brand px-0 py-0"
                        role="button"
                        onClick={onShowWho}
                    >
                        <span className="text-body px-2 py-0">
                            <i className="navbar-brand-icon bi bi-snow3"></i>
                        </span>
                        <OverlayTrigger
                            placement="bottom"
                            overlay={
                                <Tooltip id="tooltip-musigree">
                                    Musigree
                                </Tooltip>
                            }
                        >
                            <h3 className="text-body flex-grow-0 px-1 py-0 mb-0 collapse navbar-collapse">
                                MUSIGREE
                            </h3>
                        </OverlayTrigger>
                        <h6 className="text-body mb-0 collapse navbar-collapse">
                            &nbsp;v{version}
                        </h6>
                    </div>
                </div>

                {/* Navbar title section */}
                <div className="navbar-title flex-grow-1 d-flex justify-content-center px-2 py-0 h-100 d-inline-block col-lg-5 col-md-5 col-sm-10 col-10 order-2 order-md-2">
                    <span id="navbar-title"></span>
                </div>

                {/* Search section */}
                <div className="justify-content-center px-2 py-2 flex-grow-1 col-lg-3 col-md-3 col-sm-11 col-11 order-4 order-md-3">
                    <SearchInput
                        placeholder="Search for artists, labels, etc."
                        className="w-100"
                    />
                </div>

                {/* Random button section */}
                <div className="navbar-text navbar-right px-2 py-0 fs-5 d-flex justify-content-center col-lg-1 col-md-1 col-sm-1 col-1 order-3 order-md-4">
                    <OverlayTrigger
                        placement="bottom"
                        overlay={
                            <Tooltip id="tooltip-random">
                                Choose a random artist
                            </Tooltip>
                        }
                    >
                        <div
                            className="d-flex flex-row"
                            role="button"
                            onClick={handleRandom}
                        >
                            <i className="bi bi-shuffle px-1 py-0"></i>
                            <div className="collapse navbar-collapse px-1 py-0">
                                RANDOM
                            </div>
                        </div>
                    </OverlayTrigger>
                </div>

                {/* Help button section */}
                <div
                    className="navbar-text navbar-right px-2 py-0 fs-5
                                d-flex justify-content-center
                                col-lg-1 col-md-1 col-sm-1 col-1
                                order-5 order-md-5"
                >
                    <OverlayTrigger
                        placement="bottom"
                        overlay={<Tooltip id="tooltip-help">Help</Tooltip>}
                    >
                        <div
                            className="d-flex flex-row"
                            role="button"
                            onClick={onShowHelp}
                        >
                            <i className="bi bi-question-circle px-1 py-0"></i>
                            <div className="collapse navbar-collapse px-1 py-0">
                                HELP
                            </div>
                        </div>
                    </OverlayTrigger>
                </div>
            </Container>
        </Navbar>
    );
};

export default Header;
