/** @jsxImportSource react */
import type { ReactNode } from "react";
import React from "react";
import * as htmlparser2 from "htmlparser2";
import { EntityLink } from "./EntityLink";
import { API } from "../../constants";

interface ProfileProps {
    profileHtml: string;
}

/**
 * Profile component renders the entity's profile text with clickable links.
 */
export const Profile: React.FC<ProfileProps> = ({ profileHtml }) => {
    const allowedTags = [
        "b",
        "strong",
        "i",
        "em",
        "mark",
        "small",
        "del",
        "ins",
        "sub",
        "sup",
        "u",
    ];

    const parseProfile = (profileHtml: string): ReactNode => {
        interface TagStackItem {
            tagName: string; // lowercase for comparison
            originalTagName: string; // original case for case sensitivity checks
            attributes: { [s: string]: string } | null;
            children: ReactNode[];
            key: number;
            ignoreContent: boolean;
        }

        const tagStack: TagStackItem[] = [];
        const rootElements: ReactNode[] = [];
        let key: number = 0;

        // Tags that should be completely ignored (including their text content)
        const ignoredTags = ["script", "style"];

        const createElement = (
            tagName: string,
            attributes: { [s: string]: string } | null,
            children: ReactNode[],
            elementKey: number,
        ): ReactNode => {
            const tagNameLower = tagName.toLowerCase();
            // EntityLink is case-insensitive
            if (attributes && tagNameLower === "entitylink") {
                let url = "";
                if (attributes.entityKey) {
                    const parts = attributes.entityKey.split("-");
                    if (parts.length >= 2) {
                        const firstPart = parts[0];
                        const restParts = parts.slice(1);
                        if (
                            firstPart !== undefined &&
                            firstPart.length > 0 &&
                            restParts.length > 0
                        ) {
                            const entityType: string = firstPart;
                            const entityId: string = restParts.join("-");

                            url = API.ENDPOINTS.UI(entityType, entityId);
                        }
                    }
                }
                return (
                    <EntityLink
                        key={elementKey}
                        entityKey={attributes?.entityKey || ""}
                        entityName={attributes?.entityName || ""}
                        url={url}
                    />
                );
            }
            // For other tags, only allow exact lowercase matches (case-sensitive)
            // This ensures uppercase tags like <B> are ignored even if <b> is allowed
            if (
                tagName === tagNameLower &&
                allowedTags.includes(tagNameLower)
            ) {
                return React.createElement(
                    tagNameLower,
                    { key: elementKey },
                    ...children,
                );
            }
            if (tagName === tagNameLower && tagNameLower === "br") {
                return React.createElement(tagNameLower, { key: elementKey });
            }
            return null;
        };

        const parser = new htmlparser2.Parser(
            {
                onopentag(
                    tagName: string,
                    tagAttributes: { [s: string]: string },
                ): void {
                    /*
                     * This fires when a new tag is opened.
                     * Push the tag onto the stack to handle nesting.
                     * Store both lowercase and original for case sensitivity checks.
                     */
                    const tagNameLower = tagName.toLowerCase();
                    const ignoreContent = ignoredTags.includes(tagNameLower);
                    tagStack.push({
                        tagName: tagNameLower, // Use lowercase for consistent comparison
                        originalTagName: tagName, // Preserve original for case sensitivity
                        attributes: tagAttributes,
                        children: [],
                        key: key++,
                        ignoreContent,
                    });
                },
                ontext(text: string): void {
                    /*
                     * Fires whenever a section of text was processed.
                     * Add text to the current tag's children, or to root if no tag is open.
                     * Skip text if we're inside an ignored tag.
                     */
                    // Check if we're inside an ignored tag
                    if (tagStack.length > 0) {
                        const currentTag = tagStack[tagStack.length - 1];
                        if (currentTag.ignoreContent) {
                            // Ignore text content of script/style tags
                            return;
                        }
                    }

                    const textNode = (
                        <React.Fragment key={key++}>{text}</React.Fragment>
                    );

                    if (tagStack.length > 0) {
                        // Add text to the current tag's children
                        const currentTag = tagStack[tagStack.length - 1];
                        currentTag.children.push(textNode);
                    } else {
                        // Add text to root elements
                        rootElements.push(textNode);
                    }
                },
                onclosetag(_tagName: string): void {
                    /*
                     * Fires when a tag is closed.
                     * Pop the tag from the stack, create the React element,
                     * and add it to the parent tag or root elements.
                     */
                    if (tagStack.length === 0) {
                        return;
                    }

                    const closedTag = tagStack.pop();
                    if (!closedTag) {
                        return;
                    }

                    // Completely ignore script and style tags
                    if (closedTag.ignoreContent) {
                        return;
                    }

                    // Process the tag even if names don't match exactly
                    // (handles edge cases with self-closing or malformed tags)
                    // Use original tag name for case sensitivity checks
                    const element = createElement(
                        closedTag.originalTagName,
                        closedTag.attributes,
                        closedTag.children,
                        closedTag.key,
                    );

                    if (element === null) {
                        // For unsupported tags, preserve their text content
                        // by adding children to the parent or root
                        if (tagStack.length > 0) {
                            const parentTag = tagStack[tagStack.length - 1];
                            // Only add children if parent is not ignored
                            if (!parentTag.ignoreContent) {
                                parentTag.children.push(...closedTag.children);
                            }
                        } else {
                            rootElements.push(...closedTag.children);
                        }
                        return;
                    }

                    if (tagStack.length > 0) {
                        // Add element to parent tag's children
                        const parentTag = tagStack[tagStack.length - 1];
                        // Only add to parent if parent is not ignored
                        if (!parentTag.ignoreContent) {
                            parentTag.children.push(element);
                        }
                    } else {
                        // Add element to root elements
                        rootElements.push(element);
                    }
                },
            },
            {
                lowerCaseTags: false,
                lowerCaseAttributeNames: false,
                recognizeSelfClosing: true,
            },
        );

        parser.write(profileHtml);
        parser.end();

        return rootElements.length === 1 ? rootElements[0] : rootElements;
    };

    return <React.Fragment>{parseProfile(profileHtml)}</React.Fragment>;
};

export default Profile;
