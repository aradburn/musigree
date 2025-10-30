/** @jsxImportSource react */
import React from "react";
import type { EntityData } from "../../entities";
import { capitalCase } from "text-case";
import { expandCommas } from "../../utils";

/**
 * Details component provides a panel display for details.
 */
export const Details: React.FC<{ entity?: EntityData | null }> = ({
    entity,
}) => {
    const relationCounts = entity?.relation_counts ?? {};
    const hasEntity = Boolean(entity);
    const hasAliases = entity?.entities?.aliases;
    const aliases = hasAliases ? Object.keys(entity?.entities?.aliases) : [""];
    const aliasesStr = aliases.join(", ");
    const hasAltNames = entity?.metadata?.name_variations;
    const altNames = hasAltNames ? entity?.metadata?.name_variations : [""];
    const altNamesStr = altNames.join(", ");
    const hasRealName = entity?.metadata?.real_name;
    const realNameStr = hasRealName ? entity?.metadata?.real_name : "";
    const hasProfile = entity?.metadata?.profile;
    const profileStr = hasProfile ? entity?.metadata?.profile : "";
    const hasURLs = entity?.metadata?.urls;
    const urlListItems = hasURLs ? entity?.metadata?.urls.map((url, i) => <li key={i}>{url}</li>) : "";

    return (
        <div className="flex-grow-1 overflow-scroll details-panel mx-auto pe-3 bg-secondary-subtle">
            {/* Details panel */}
            <div className="details-title h4">
                <span>{hasEntity ? entity?.name : "Details"}</span>
            </div>
            <div className="details-content">
                <dl className="row">
                    <dt className="col-sm-3">Aliases</dt>
                    <dd className="col-sm-9">
                        {hasEntity ? aliasesStr : "-"}
                    </dd>

                    <dt className="col-sm-3">Real Name</dt>
                    <dd className="col-sm-9">
                        {hasEntity ? realNameStr : "-"}
                    </dd>

                    <dt className="col-sm-3">Alternative Names</dt>
                    <dd className="col-sm-9">
                        {hasEntity ? altNamesStr : "-"}
                    </dd>

                    <dt className="col-sm-3">Type</dt>
                    <dd className="col-sm-9">
                        {hasEntity ? capitalCase(entity?.type) : "-"}
                    </dd>

                    <dt className="col-sm-3">Country</dt>
                    <dd className="col-sm-9">
                        {hasEntity && entity?.countries
                            ? expandCommas(entity.countries)
                            : "-"}
                    </dd>

                    <dt className="col-sm-3">Genres</dt>
                    <dd className="col-sm-9">
                        {hasEntity && entity?.genres ? expandCommas(entity.genres) : "-"}
                    </dd>

                    <dt className="col-sm-3">Styles</dt>
                    <dd className="col-sm-9">
                        {hasEntity && entity?.styles ? expandCommas(entity.styles) : "-"}
                    </dd>

                    <dt className="col-sm-3">Profile</dt>
                    <dd className="col-sm-9">
                        {hasEntity ? profileStr : "-"}
                    </dd>

                    <dt className="col-sm-3">URLs</dt>
                    <dd className="col-sm-9">
                        {hasURLs ? <ul className="ps-0">{urlListItems}</ul> : "-"}
                    </dd>
                </dl>
            </div>
        </div>
    );
};

export default Details;
