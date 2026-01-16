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

interface DetailsProps {
    entity?: EntityData;
    isMobile: boolean;
}

/**
 * Details component provides a panel display for details.
 */
export const Details: React.FC<DetailsProps> = ({ entity, isMobile }) => {
    const hasEntity = Boolean(entity);
    const hasAliases = entity?.entities?.aliases;
    const aliases = hasAliases ? Object.keys(entity?.entities?.aliases) : [""];
    const aliasesStr = aliases.join(", ");
    const nameVariations = entity?.metadata?.name_variations;
    const altNames = Array.isArray(nameVariations) ? nameVariations : [""];
    const altNamesStr = altNames.join(", ");
    const realName = entity?.metadata?.real_name;
    const _realNameStr = typeof realName === "string" ? realName : "";
    const countriesStr = entity?.countries
        ? expandCommas(entity.countries)
        : "";
    const genresStr = entity?.genres ? expandCommas(entity.genres) : "";
    const stylesStr = entity?.styles ? expandCommas(entity.styles) : "";
    const profile = entity?.metadata?.profile;
    const profileStr =
        typeof profile === "string"
            ? expandProfileURLs(expandProfileReferences(profile))
            : "";

    const discogs_url = hasEntity
        ? "https://discogs.com/" + entity?.type + "/" + entity?.id
        : null;

    const metadataUrls = entity?.metadata?.urls;
    const metadataUrlsArray = Array.isArray(metadataUrls)
        ? metadataUrls.filter((url): url is string => typeof url === "string")
        : [];
    const urls = [discogs_url, ...metadataUrlsArray];
    const dtClassName = isMobile ? "col-12 ms-3 mt-3" : "col-3 mt-2";
    const ddClassName = isMobile ? "col-12 ms-3 mt-3" : "col-9 mt-2";
    const urlListItems = Array.isArray(urls)
        ? urls
              .filter((url): url is string => typeof url === "string")
              .map((url, i) => (
                  <React.Fragment key={i}>
                      <dt className={dtClassName}>
                          <span className={createExternalLinkBadgeClass(url)}>
                              {createExternalLinkBadgeText(url)}
                          </span>
                      </dt>
                      <dd className={ddClassName}>
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
                    {aliasesStr ? (
                        <>
                            <dt className={dtClassName}>Aliases</dt>
                            <dd className={ddClassName}>{aliasesStr}</dd>
                        </>
                    ) : null}

                    {/*
                    <dt className="col-3">Real Name</dt>
                    <dd className="col-9">{realNameStr}</dd>
                    */}

                    {altNamesStr ? (
                        <>
                            <dt className={dtClassName}>Alt Names</dt>
                            <dd className={ddClassName}>{altNamesStr}</dd>
                        </>
                    ) : null}

                    <dt className={dtClassName}>Type</dt>
                    <dd className={ddClassName}>
                        {hasEntity ? capitalCase(entity?.type) : "-"}
                    </dd>

                    {countriesStr ? (
                        <>
                            <dt className={dtClassName}>Countries</dt>
                            <dd className={ddClassName}>{countriesStr}</dd>
                        </>
                    ) : null}

                    {genresStr ? (
                        <>
                            <dt className={dtClassName}>Genres</dt>
                            <dd className={ddClassName}>{genresStr}</dd>
                        </>
                    ) : null}

                    {stylesStr ? (
                        <>
                            <dt className={dtClassName}>Styles</dt>
                            <dd className={ddClassName}>{stylesStr}</dd>
                        </>
                    ) : null}

                    {profileStr ? (
                        <>
                            <dt className={dtClassName}>Profile</dt>
                            <dd className={ddClassName}>
                                <Profile profileHtml={profileStr}></Profile>
                            </dd>
                        </>
                    ) : null}

                    <dt className={dtClassName}>External Links</dt>
                    <dd className={ddClassName}></dd>
                    {Array.isArray(urls) && urls.length > 0 ? (
                        <React.Fragment>{urlListItems}</React.Fragment>
                    ) : (
                        <React.Fragment>
                            <dt className="col-3 mt-3"></dt>
                            <dd className="col-9 mt-3">-</dd>
                        </React.Fragment>
                    )}
                </dl>
            </div>
        </div>
    );
};

export default Details;
