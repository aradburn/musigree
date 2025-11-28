/** @jsxImportSource react */
import React from "react";
import type { EntityData } from "../../entities";
import { capitalCase } from "text-case";
import {
    createExternalLinkBadgeClass,
    createExternalLinkBadgeText,
    expandCommas,
    expandProfileURLs,
    expandProfileReferences,
    removeURLProtocol,
} from "../../utils";
import DOMPurify from "dompurify";
import { Profile } from "./Profile";

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

    const discogs_url = hasEntity
        ? "https://discogs.com/" + entity?.type + "/" + entity?.id
        : null;

    const urls = [ discogs_url, ...(entity?.metadata?.urls || []) ];
    const urlListItems = Array.isArray(urls)
        ? urls
              .filter((url): url is string => typeof url === "string")
              .map((url, i) => (
                  <React.Fragment key={i}>
                      <dt className="col-3">
                          <span className={createExternalLinkBadgeClass(url)}>
                              {createExternalLinkBadgeText(url)}
                          </span>
                      </dt>
                      <dd className="col-9">
                          <a
                              href={DOMPurify.sanitize(url)}
                              className="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover"
                              target="_blank"
                              rel="noopener noreferrer"
                          >
                              {removeURLProtocol(url)}
                          </a>
                      </dd>
                  </React.Fragment>
              ))
        : "";

    return (
        <div
            id="entity-details-panel"
            className="details-panel
                        mx-auto pe-3
                        bg-secondary-subtle"
        >
            {/* Details panel */}
            <div className="details-title h4">
                <span>{hasEntity ? entity?.name : "Details"}</span>
            </div>
            <div className="details-content">
                <dl className="d-flex flex-wrap">
                    <dt className="col-3">Aliases</dt>
                    <dd className="col-9">{aliasesStr}</dd>

                    <dt className="col-3">Real Name</dt>
                    <dd className="col-9">{realNameStr}</dd>

                    <dt className="col-3">Alt Names</dt>
                    <dd className="col-9">{altNamesStr}</dd>

                    <dt className="col-3">Type</dt>
                    <dd className="col-9">
                        {hasEntity ? capitalCase(entity?.type) : "-"}
                    </dd>

                    <dt className="col-3">Country</dt>
                    <dd className="col-9">
                        {hasEntity && entity?.countries
                            ? expandCommas(entity.countries)
                            : "-"}
                    </dd>

                    <dt className="col-3">Genres</dt>
                    <dd className="col-9">
                        {hasEntity && entity?.genres
                            ? expandCommas(entity.genres)
                            : "-"}
                    </dd>

                    <dt className="col-3">Styles</dt>
                    <dd className="col-9">
                        {hasEntity && entity?.styles
                            ? expandCommas(entity.styles)
                            : "-"}
                    </dd>

                    <dt className="col-3">Profile</dt>
                    <dd className="col-9">
                        <Profile profileHtml={profileStr}></Profile>
                    </dd>

                    <dt className="col-11">External Links</dt>
                    <dd className="col-1"></dd>
                    {Array.isArray(urls) && urls.length > 0 ? (
                        <React.Fragment>{urlListItems}</React.Fragment>
                    ) : (
                        <React.Fragment>
                            <dt className="col-3"></dt>
                            <dd className="col-9">-</dd>
                        </React.Fragment>
                    )}
                </dl>
            </div>
        </div>
    );
};

export default Details;
