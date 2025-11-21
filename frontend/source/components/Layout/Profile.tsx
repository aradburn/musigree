/** @jsxImportSource react */
import type { ReactNode } from "react";
import React from "react";
import * as htmlparser2 from "htmlparser2";
import { EntityLink } from "./EntityLink";

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
        let isProcessingTag: boolean = false;
        let currentTagName: string = "";
        let currentTagAttributes: { [s: string]: string } = null;
        let currentTagText: string = "";
        const reactElements: ReactNode[] = [];
        let key: number = 0;

        const parser = new htmlparser2.Parser(
            {
                onopentag(
                    tagName: string,
                    tagAttributes: { [s: string]: string },
                ): void {
                    /*
                     * This fires when a new tag is opened.
                     *
                     * If you don't need an aggregated `attributes` object,
                     * have a look at the `onopentagname` and `onattribute` events.
                     */
                    isProcessingTag = true;
                    currentTagName = tagName;
                    currentTagAttributes = tagAttributes;
                },
                ontext(text: string): void {
                    /*
                     * Fires whenever a section of text was processed.
                     *
                     * Note that this can fire at any point within text and you might
                     * have to stitch together multiple pieces.
                     */
                    if (isProcessingTag) {
                        currentTagText = text;
                    } else {
                        const textNode = (
                            <React.Fragment key={key}>{text}</React.Fragment>
                        );
                        reactElements.push(textNode);
                        key++;
                    }
                },
                onclosetag(tagName: string): void {
                    /*
                     * Fires when a tag is closed.
                     *
                     * You can rely on this event only firing when you have received an
                     * equivalent opening tag before. Closing tags without corresponding
                     * opening tags will be ignored.
                     */
                    isProcessingTag = false;
                    if (tagName === "EntityLink") {
                        const element = (
                            <EntityLink
                                key={key}
                                entityKey={currentTagAttributes?.entityKey}
                                entityName={currentTagAttributes?.entityName}
                            />
                        );
                        reactElements.push(element);
                        key++;
                    } else if (allowedTags.includes(tagName)) {
                        const element = React.createElement(
                            currentTagName,
                            {
                                key: key,
                            },
                            currentTagText,
                        );
                        reactElements.push(element);
                        key++;
                    } else if (tagName === "br") {
                        const element = React.createElement(currentTagName, {
                            key: key,
                        });
                        reactElements.push(element);
                        key++;
                    }
                    currentTagName = "";
                    currentTagAttributes = null;
                    currentTagText = "";
                },
            },
            {
                lowerCaseTags: false,
                lowerCaseAttributeNames: false,
            },
        );

        parser.write(profileHtml);
        parser.end();

        return reactElements.length === 1 ? reactElements[0] : reactElements;
    };

    return <React.Fragment>{parseProfile(profileHtml)}</React.Fragment>;
};

export default Profile;
