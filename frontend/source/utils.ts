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

export const createURLBadgeClass = (_str: string): string => {
    return "badge rounded-pill px-2 py-1 me-2 text-black bg-success-subtle bg-opacity-40 bg-gradient";
};

export const createExternalLinkBadgeClass = (str: string): string => {
    if (/discogs.com/.test(str)) {
        return createURLBadgeClass("Discogs") + str;
    } else if (/facebook.com/.test(str)) {
        return createURLBadgeClass("Facebook") + str;
    } else if (/bandcamp.com/.test(str)) {
        return createURLBadgeClass("Bandcamp") + str;
    } else if (/soundcloud.com/.test(str)) {
        return createURLBadgeClass("Soundcloud") + str;
    } else if (/youtube.com/.test(str)) {
        return createURLBadgeClass("YouTube") + str;
    } else if (/musicbrainz.org/.test(str)) {
        return createURLBadgeClass("MusicBrainz") + str;
    } else if (/spotify.com/.test(str)) {
        return createURLBadgeClass("Spotify") + str;
    } else if (/instagram.com/.test(str)) {
        return createURLBadgeClass("Instagram");
    } else if (/linkedin.com/.test(str)) {
        return createURLBadgeClass("LinkedIn");
    } else if (/wikipedia.org/.test(str)) {
        return createURLBadgeClass("Wikipedia");
    } else if (/twitter.com/.test(str)) {
        return createURLBadgeClass("Twitter");
    } else if (/myspace.com/.test(str)) {
        return createURLBadgeClass("MySpace");
    } else if (/last.fm/.test(str)) {
        return createURLBadgeClass("LastFM");
    } else if (/web.archive.org/.test(str)) {
        return createURLBadgeClass("Web Archive");
    } else {
        return "";
    }
};

export const createExternalLinkBadgeText = (str: string): string => {
    if (/discogs.com/.test(str)) {
        return "Discogs";
    } else if (/facebook.com/.test(str)) {
        return "Facebook";
    } else if (/bandcamp.com/.test(str)) {
        return "Bandcamp";
    } else if (/soundcloud.com/.test(str)) {
        return "Soundcloud";
    } else if (/youtube.com/.test(str)) {
        return "YouTube";
    } else if (/musicbrainz.org/.test(str)) {
        return "MusicBrainz";
    } else if (/spotify.com/.test(str)) {
        return "Spotify";
    } else if (/instagram.com/.test(str)) {
        return "Instagram";
    } else if (/linkedin.com/.test(str)) {
        return "LinkedIn";
    } else if (/wikipedia.org/.test(str)) {
        return "Wikipedia";
    } else if (/twitter.com/.test(str)) {
        return "Twitter";
    } else if (/myspace.com/.test(str)) {
        return "MySpace";
    } else if (/last.fm/.test(str)) {
        return "LastFM";
    } else if (/web.archive.org/.test(str)) {
        return "Web Archive";
    } else {
        return "";
    }
};

export const removeURLProtocol = (str: string): string => {
    // Remove the protocol from a URL
    return str.replace(/^https?:\/\//, "");
};

export const expandCommas = (str: string): string => {
    // Replace commas that are not already followed by a space
    // Match comma followed by non-whitespace character
    return str.replace(/,(\S)/g, ", $1");
};

export const expandBold = (str: string): string => {
    const pattern = /\[[bB]](.*?)\[\/[bB]]/g;
    return str.replace(pattern, "<b>$1</b>");
};

export const expandStrong = (str: string): string => {
    const pattern = /\[strong](.*?)\[\/strong]/gi;
    return str.replace(pattern, "<strong>$1</strong>");
};

export const expandItalic = (str: string): string => {
    const pattern = /\[[iI]](.*?)\[\/[iI]]/g;
    return str.replace(pattern, "<i>$1</i>");
};

export const expandEm = (str: string): string => {
    const pattern = /\[em](.*?)\[\/em]/gi;
    return str.replace(pattern, "<em>$1</em>");
};

export const expandMark = (str: string): string => {
    const pattern = /\[mark](.*?)\[\/mark]/gi;
    return str.replace(pattern, "<mark>$1</mark>");
};

export const expandSmall = (str: string): string => {
    const pattern = /\[small](.*?)\[\/small]/gi;
    return str.replace(pattern, "<small>$1</small>");
};

export const expandDel = (str: string): string => {
    const pattern = /\[del](.*?)\[\/del]/gi;
    return str.replace(pattern, "<del>$1</del>");
};

export const expandIns = (str: string): string => {
    const pattern = /\[ins](.*?)\[\/ins]/gi;
    return str.replace(pattern, "<ins>$1</ins>");
};

export const expandSub = (str: string): string => {
    const pattern = /\[sub](.*?)\[\/sub]/gi;
    return str.replace(pattern, "<sub>$1</sub>");
};

export const expandSup = (str: string): string => {
    const pattern = /\[sup](.*?)\[\/sup]/gi;
    return str.replace(pattern, "<sup>$1</sup>");
};

export const expandUnderline = (str: string): string => {
    const pattern = /\[[uU]](.*?)\[\/[uU]]/g;
    return str.replace(pattern, "<u>$1</u>");
};

export const expandLineBreaks = (str: string): string => {
    const pattern = /\r\n/g;
    return str.replace(pattern, "<br/>");
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
    str = expandCommas(str);
    str = expandProfileURLs(str);
    str = expandArtistLinkReferences(str);
    str = expandLabelLinkReferences(str);
    str = expandArtistTextReferences(str);
    str = expandLabelTextReferences(str);
    str = expandBold(str);
    str = expandStrong(str);
    str = expandItalic(str);
    str = expandEm(str);
    str = expandMark(str);
    str = expandSmall(str);
    str = expandDel(str);
    str = expandIns(str);
    str = expandSub(str);
    str = expandSup(str);
    str = expandUnderline(str);
    str = expandLineBreaks(str);
    return str;
};

export const sanitizedData = (s: string): { __html: string } => ({
    __html: DOMPurify.sanitize(s),
});

export const convertRemToPixels = (rem: number): number => {
    return (
        rem * parseFloat(getComputedStyle(document.documentElement).fontSize)
    );
};
