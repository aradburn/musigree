import { networkManager } from "./core/singletons";

import DOMPurify from "dompurify";

// Add a hook to make all links open a new window
DOMPurify.addHook("afterSanitizeAttributes", function (node) {
    // set all elements owning target to target=_blank
    if ("target" in node) {
        node.setAttribute("target", "_blank");
    }
    // set non-HTML/MathML links to xlink:show=new
    if (
        !node.hasAttribute("target") &&
        (node.hasAttribute("xlink:href") || node.hasAttribute("href"))
    ) {
        node.setAttribute("xlink:show", "new");
    }
});

/**
 * Clamps a value between a minimum and maximum
 */
export const clamp = (value: number, min: number, max: number): number => {
    return Math.max(min, Math.min(max, value));
};

export const createBadge = (str: string): string => {
    return (
        '<span class="badge px-1 py-0 text-black bg-success-subtle bg-opacity-40 bg-gradient">' +
        str +
        "</span>"
    );
};

export const expandCommas = (str: string): string => {
    // Replace commas that are not already followed by a space
    // Match comma followed by non-whitespace character
    return str.replace(/,(\S)/g, ", $1");
};

export const expandItalics = (str: string): string => {
    const pattern = /\[[iI]](.*?)\[\/[iI]]/g;
    return str.replace(pattern, '<b><i>"$1"</i></b>');
};

export const expandProfileURLs = (str: string): string => {
    // Converts a text url in square brackets into a sanitized version
    // eg. [url=http://www.discogs.com/artist/Acid+Mothers+Temple]Acid Mothers Temple[/url]
    // <a href=$1 target="_blank" rel="noopener noreferrer">$2</a>
    // Use non-greedy matching to handle multiple URLs correctly
    const pattern = /\[url=(.*?)](.*?)\[\/url]/g;
    return str.replace(
        pattern,
        '<a href="$1" target="_blank" rel="noopener noreferrer">$2</a>',
    );
};

export const expandArtistLinkReferences = (str: string): string => {
    // Converts a text ref [a12345] into the referred to artist name
    const regexp = /\[[aA]\d+]/g;
    const matches = Array.from(str.matchAll(regexp));
    let expanded = String(str);
    for (const match of matches) {
        if (match[0]) {
            const entity_key = "artist-" + match[0].slice(2, -1);
            const value = networkManager.data.nodeMap.get(entity_key);
            const replacement = value?.name ?? match[0];
            expanded = expanded.replace(match[0], replacement);
        }
    }
    return expanded;
};

export const expandLabelLinkReferences = (str: string): string => {
    // Converts a text ref [l12345] into the referred to label name
    const regexp = /\[[lL]\d+]/g;
    const matches = Array.from(str.matchAll(regexp));
    let expanded = String(str);
    for (const match of matches) {
        if (match[0]) {
            const entity_key = "label-" + match[0].slice(2, -1);
            const value = networkManager.data.nodeMap.get(entity_key);
            const replacement = value?.name ?? match[0];
            expanded = expanded.replace(match[0], replacement);
        }
    }
    return expanded;
};

export const expandArtistTextReferences = (str: string): string => {
    // Converts an artist reference [a=Some Artist Name Here] into a badge
    const pattern = /\[[aA]=(.*?)]/g;
    return str.replace(pattern, (_match, name: string) => createBadge(name));
};

export const expandLabelTextReferences = (str: string): string => {
    // Converts a label reference [l=Some Label Name Here] into a badge
    const pattern = /\[[lL]=(.*?)]/g;
    return str.replace(pattern, (_match, name: string) => createBadge(name));
};

export const expandProfileReferences = (str: string): string => {
    // Performs multiple conversions in sequence
    const str1 = expandCommas(str);
    const str2 = expandProfileURLs(str1);
    const str3 = expandArtistLinkReferences(str2);
    const str4 = expandLabelLinkReferences(str3);
    const str5 = expandArtistTextReferences(str4);
    const str6 = expandLabelTextReferences(str5);
    const str7 = expandItalics(str6);
    return str7;
};

export const sanitizedData = (s: string): { __html: string } => ({
    __html: DOMPurify.sanitize(s),
});
