/** @jsxImportSource react */
import React from "react";
import type { EntityData } from "../../entities";
import { capitalCase } from "text-case";
import {
    expandCommas,
    expandProfileURLs,
    expandProfileReferences,
    sanitizedData,
} from "../../utils";
import DOMPurify from "dompurify";

/**
 * Details component provides a panel display for details.
 */
export const Details: React.FC<{ entity?: EntityData | null }> = ({
    entity,
}) => {
    const hasEntity = Boolean(entity);
    const hasAliases = entity?.entities?.aliases;
    const aliases = hasAliases ? Object.keys(entity?.entities?.aliases) : ["-"];
    const aliasesStr = aliases.join(", ");
    const nameVariations = entity?.metadata?.name_variations;
    const altNames = Array.isArray(nameVariations) ? nameVariations : ["-"];
    const altNamesStr = altNames.join(", ");
    const realName = entity?.metadata?.real_name;
    const realNameStr = typeof realName === "string" ? realName : "-";
    const profile = entity?.metadata?.profile;
    const profileStr =
        typeof profile === "string"
            ? expandProfileURLs(expandProfileReferences(profile))
            : "";
    const urls = entity?.metadata?.urls;
    const urlListItems = Array.isArray(urls)
        ? urls
              .filter((url): url is string => typeof url === "string")
              .map((url, i) => (
                  <li key={i}>
                      <a
                          href={DOMPurify.sanitize(url)}
                          class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover"
                          target="_blank"
                          rel="noopener noreferrer"
                      >
                          {url}
                      </a>
                  </li>
              ))
        : "";

    return (
        <div
            className="details-panel
                        flex-grow-1 overflow-scroll
                        mx-auto pe-3
                        bg-secondary-subtle"
        >
            {/* Details panel */}
            <div className="details-title h4">
                <span>{hasEntity ? entity?.name : "Details"}</span>
            </div>
            <div className="details-content">
                <dl className="row">
                    <dt className="col-sm-3">Aliases</dt>
                    <dd className="col-sm-9">{aliasesStr}</dd>

                    <dt className="col-sm-3">Real Name</dt>
                    <dd className="col-sm-9">{realNameStr}</dd>

                    <dt className="col-sm-3">Alt Names</dt>
                    <dd className="col-sm-9">{altNamesStr}</dd>

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
                        {hasEntity && entity?.genres
                            ? expandCommas(entity.genres)
                            : "-"}
                    </dd>

                    <dt className="col-sm-3">Styles</dt>
                    <dd className="col-sm-9">
                        {hasEntity && entity?.styles
                            ? expandCommas(entity.styles)
                            : "-"}
                    </dd>

                    <dt className="col-sm-3">Profile</dt>
                    <dd
                        className="col-sm-9"
                        dangerouslySetInnerHTML={sanitizedData(profileStr)}
                    ></dd>

                    <dt className="col-sm-3">External Links</dt>
                    <dd className="col-sm-9">
                        {Array.isArray(urls) && urls.length > 0 ? (
                            <ul className="ps-0">{urlListItems}</ul>
                        ) : (
                            "-"
                        )}
                    </dd>
                </dl>
            </div>
        </div>
    );
};

export default Details;
