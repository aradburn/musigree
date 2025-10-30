/** @jsxImportSource react */
import React from "react";
import { Details } from "./Details";
import { Advert } from "./Advert";
import { useEntity } from "../../contexts/useEntity";

/**
 * SidebarRight component provides a display for entity details.
 */
export const SidebarRight: React.FC = () => {
    const { state } = useEntity();
    return (
        <div
            className="sidebar sidebar-right col-auto flex-fill ms-auto d-flex p-2 h-100
                        gap-2
                        flex-sm-column flex-xl-column
                        justify-content-evenly
                        justify-content-sm-start justify-content-xl-start
                        align-items-start
                        align-items-sm-start align-items-xl-start
                        bg-secondary-subtle text-light"
        >
            {/* Details panel */}
            <Details entity={state.entity} />
            <Advert adClient="ca-pub-5857652035840115" adSlot="3061976325" />
        </div>
    );
};

export default SidebarRight;
