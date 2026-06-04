/** @jsxImportSource react */
import React from "react";
import { RequestNetworkEvent } from "@/network/events";

interface EntityLinkProps {
    entityKey: string;
    entityName: string;
    url: string;
}

/**
 * EntityLink component provides a badge with a clickable link.
 */
export const EntityLink: React.FC<EntityLinkProps> = ({
    entityKey,
    entityName,
    url,
}) => {
    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>): void => {
        e.preventDefault();
        if (entityKey && entityKey != "null") {
            // Dispatch the REQUEST_NETWORK event to trigger the FSM transition
            const event = new RequestNetworkEvent(entityKey, true);
            document.dispatchEvent(event);
        }
    };

    return (
        <a
            href={url}
            className="entity-link badge text-black background-highlight bg-gradient"
            onClick={handleClick}
        >
            {entityName}
        </a>
    );
};

export default EntityLink;
