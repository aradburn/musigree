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

/**
 * Debounces a function call
 */
export const debounce = <T extends (...args: Parameters<T>) => void>(
    func: T,
    wait: number,
): ((...args: Parameters<T>) => void) => {
    let timeout: number | null = null;
    return (...args: Parameters<T>) => {
        if (timeout) window.clearTimeout(timeout);
        timeout = window.setTimeout(() => func(...args), wait);
    };
};

export const createBadge = (str: string): string => {
    return "<span class=\"badge px-1 py-0 text-black bg-success-subtle bg-opacity-40 bg-gradient\">" + str + "</span>";
};

export const expandCommas = (str: string): string => {
    const pattern = /(\S),(\S)/g;
    return str.replace(pattern, "$1, $2");
};

export const expandItalics = (str: string): string => {
    const pattern = /\[i](.*?)\[\/i]/g;
    return str.replace(pattern, "<b><i>\"$1\"</i></b>");
};

export const expandProfileURLs = (str: string): string => {
    // Converts a text url in square brackets into a sanitized version
    // eg. [url=http://www.discogs.com/artist/Acid+Mothers+Temple]Acid Mothers Temple[/url]
    // <a href=$1 target="_blank" rel="noopener noreferrer">$2</a>
    const pattern = /\[url=(.*)](.*)\[\/url]/g;
    return str.replace(
        pattern,
        '<a href="$1" target="_blank" rel="noopener noreferrer">$2</a>',
    );
};

export const expandArtistLinkReferences = (str: string): string => {
    // Converts a text ref [a12345] into the referred to artist name
    const regexp = /\[a\d+]/g;
    let match;
    let expanded = String(str);
    while ((match = regexp.exec(str)) !== null) {
        console.log("Found Artist: ", match[0]);
        const entity_key = "artist-" + match[0].slice(2, -1);
        console.log("entity_key: ", entity_key);
        const value = networkManager.data.nodeMap.get(entity_key);
        console.log("value: ", value);
        console.log("name: ", value?.name);
        expanded = expanded.replace(match[0], value?.name);
    }
    return expanded;
};

export const expandLabelLinkReferences = (str: string): string => {
    // Converts a text ref [l12345] into the referred to label name
    const regexp = /\[l\d+]/g;
    let match;
    let expanded = String(str);
    while ((match = regexp.exec(str)) !== null) {
        console.log("Found Label: ", match[0]);
        const entity_key = "label-" + match[0].slice(2, -1);
        console.log("entity_key: ", entity_key);
        const value = networkManager.data.nodeMap.get(entity_key);
        console.log("value: ", value);
        console.log("name: ", value?.name);
        expanded = expanded.replace(match[0], value?.name);
    }
    return expanded;
};

export const expandArtistTextReferences = (str: string): string => {
    // Converts an artist reference [a=Some Artist Name Here] into a plain name
    const pattern = /\[a=(.*?)]/g;
    const replacement = createBadge("$1")
    return str.replace(pattern, replacement);
};

export const expandLabelTextReferences = (str: string): string => {
    // Converts an label reference [l=Some Label Name Here] into a plain name
    const pattern = /\[l=(.*?)]/g;
    const replacement = createBadge("$1")
    return str.replace(pattern, replacement);
};

export const expandProfileReferences = (str: string): string => {
    // Performs multiple comversions
    const str2 = expandArtistLinkReferences(str);
    const str3 = expandLabelLinkReferences(str2);
    const str4 = expandArtistTextReferences(str3);
    const str5 = expandLabelTextReferences(str4);
    const str6 = expandItalics(str5);
    return str6;
};

export const sanitizedData = (s) => ({
    __html: DOMPurify.sanitize(s),
});
