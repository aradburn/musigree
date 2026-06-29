/* @jsxImportSource react */

import React from "react";
import {Container, Navbar, OverlayTrigger, Tooltip} from "react-bootstrap";
import SearchInput from "../Search/SearchInput";
import {FSM} from "@/constants.ts";
import {version} from "@/version.ts";
import {useWindow} from "@/contexts/useWindow.ts";

interface HeaderProps {
    onShowHelp?: () => void;
}

/**
 * Header UI component.
 */
export const Header: React.FC<HeaderProps> = ({onShowHelp}) => {
    const {state: windowState} = useWindow();

    const handleRandom = (e: React.MouseEvent<HTMLDivElement>): void => {
        e.preventDefault();
        // Dispatch the REQUEST_RANDOM event to trigger the FSM transition
        const event = new CustomEvent(FSM.EVENTS.REQUEST_RANDOM, {
            bubbles: true,
        });
        document.dispatchEvent(event);
    };
    const containerClassName = windowState.isMobile ? "px-1" : "";

    return (
        <Navbar
            id="nav-top"
            bg="body-tertiary"
            expand="lg"
            className="text-body p-0"
        >
            <Container fluid className={containerClassName}>
                {/* Brand section */}
                <div
                    className="px-0 px-md-2 py-0 col-lg-2 col-md-2 col-sm-2 col-2 order-1 order-md-1">
                    <div
                        className="d-flex flex-row navbar-brand align-items-center px-0 py-0">
                        <span className="text-body px-sm-2 px-1 py-0">
                            <i className="navbar-brand-icon bi bi-snow3"></i>
                        </span>

                        <h3 className="text-body flex-grow-0 d-lg-block d-none px-0 px-lg-2 py-0 mb-0">
                            MUSIGREE
                        </h3>

                        <h6 className="text-body mb-0 d-xl-block d-none">
                            &nbsp;v{version}
                        </h6>
                    </div>
                </div>

                {/* Navbar title section */}
                <div
                    className="navbar-title flex-grow-1 d-flex justify-content-center px-sm-2 px-0 py-0 h-100 d-inline-block col-lg-5 col-md-5 col-sm-9 col-9 order-2 order-md-2">
                    <span id="navbar-title"></span>
                </div>

                {/* Search section */}
                <div
                    className="justify-content-center px-2 py-2 flex-grow-1 col-lg-3 col-md-3 col-sm-11 col-11 order-4 order-md-3">
                    <SearchInput
                        placeholder="Search for artists, labels, etc."
                        className="w-100"
                    />
                </div>

                {/* Random button section */}
                <div
                    className="navbar-text navbar-right px-2 py-0 fs-5 d-flex justify-content-center col-lg-1 col-md-1 col-sm-1 col-1 order-3 order-md-4">
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
                            data-tour="random"
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
                            data-tour="help"
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
