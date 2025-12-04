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
        <div className="p-2 d-flex h-sm-100">
            <div className="flex-fill ms-auto d-flex gap-2 flex-column text-light">
                <div className="flex-fill overflow-x-hidden overflow-y-auto">
                    {/* Details panel */}
                    <Details entity={state.entity} />
                </div>
                <div className="flex-shrink-0">
                    {/*<Advert*/}
                    {/*    adClient="ca-pub-5857652035840115"*/}
                    {/*    adSlot="3061976325"*/}
                    {/*/>*/}
                </div>
            </div>
        </div>
    );
};

export default SidebarRight;
