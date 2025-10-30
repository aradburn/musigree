import DOMPurify from "dompurify";

// Add a hook to make all links open a new window
DOMPurify.addHook('afterSanitizeAttributes', function (node) {
  // set all elements owning target to target=_blank
  if ('target' in node) {
    node.setAttribute('target', '_blank');
  }
  // set non-HTML/MathML links to xlink:show=new
  if (
    !node.hasAttribute('target') &&
    (node.hasAttribute('xlink:href') || node.hasAttribute('href'))
  ) {
    node.setAttribute('xlink:show', 'new');
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

export const expandCommas = (s: string): string => {
    const pattern = /(\S),(\S)/g;
    return s.replace(pattern, "$1, $2");
};

export const expandProfileURLs = (s: string): string => {
    // Converts a text url in square brackets into a sanitized version
    // eg. [url=http://www.discogs.com/artist/Acid+Mothers+Temple]Acid Mothers Temple[/url]
    // <a href=$1 target="_blank" rel="noopener noreferrer">$2</a>
    const pattern = /\[url=(.*)](.*)\[\/url]/g;
    return s.replace(pattern, "<a href=\"$1\" target=\"_blank\" rel=\"noopener noreferrer\">$2</a>");
};

export const sanitizedData = (s) => ({
    __html: DOMPurify.sanitize(s)
});
