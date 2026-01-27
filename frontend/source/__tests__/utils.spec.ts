import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { SimNode } from "../network/data";

// Mock networkManager before importing utils
// Note: vi.mock is hoisted, so we need to create the map inside the factory
vi.mock("../core/singletons", () => {
    const mockNodeMap = new Map<string, SimNode>();
    return {
        networkManager: {
            data: {
                nodeMap: mockNodeMap,
            },
        },
    };
});

import {
    clamp,
    createEntityLink,
    createURLBadgeClass,
    createExternalLinkBadgeClass,
    createExternalLinkBadgeText,
    removeURLProtocol,
    expandCommas,
    expandBold,
    expandStrong,
    expandItalic,
    expandEm,
    expandMark,
    expandSmall,
    expandDel,
    expandIns,
    expandSub,
    expandSup,
    expandUnderline,
    expandLineBreaks,
    expandProfileURLs,
    expandLinkReferences,
    expandProfileReferences,
    sanitizedData,
} from "../utils";
import { networkManager } from "../core/singletons";
import debounce from "debounce";

// Get reference to the mocked nodeMap for use in tests
const getMockNodeMap = () =>
    networkManager.data.nodeMap as Map<string, SimNode>;

describe("Utility Functions", () => {
    describe("clamp", () => {
        it("should return the value when it is within range", () => {
            expect(clamp(5, 0, 10)).toBe(5);
        });

        it("should return the minimum value when value is below range", () => {
            expect(clamp(-5, 0, 10)).toBe(0);
        });

        it("should return the maximum value when value is above range", () => {
            expect(clamp(15, 0, 10)).toBe(10);
        });

        it("should handle equal min and max values", () => {
            expect(clamp(5, 10, 10)).toBe(10);
        });

        it("should handle decimal numbers", () => {
            expect(clamp(1.5, 1, 2)).toBe(1.5);
            expect(clamp(0.5, 1, 2)).toBe(1);
            expect(clamp(2.5, 1, 2)).toBe(2);
        });
    });

    describe("debounce", () => {
        beforeEach(() => {
            vi.useFakeTimers();
        });

        afterEach(() => {
            vi.restoreAllMocks();
        });

        it("should call the function after the specified wait time", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            expect(mockFn).not.toHaveBeenCalled();

            vi.advanceTimersByTime(100);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        it("should only call the function once when called multiple times within wait period", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            debouncedFn();
            debouncedFn();

            vi.advanceTimersByTime(50);
            expect(mockFn).not.toHaveBeenCalled();

            vi.advanceTimersByTime(50);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        it("should call the function with the latest arguments", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn("first");
            debouncedFn("second");
            debouncedFn("third");

            vi.advanceTimersByTime(100);
            expect(mockFn).toHaveBeenCalledWith("third");
        });

        it("should reset the timer when called again", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            vi.advanceTimersByTime(50);

            debouncedFn();
            vi.advanceTimersByTime(50);
            expect(mockFn).not.toHaveBeenCalled();

            vi.advanceTimersByTime(50);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });
    });

    describe("createEntityLink", () => {
        it("should create a EntityLink component string with entityKey and entityName", () => {
            const result = createEntityLink("artist-123", "Test Artist");
            expect(result).toContain("Test Artist");
            expect(result).toContain('entityKey="artist-123"');
            expect(result).toContain('entityName="Test Artist"');
            expect(result).toContain("<EntityLink");
            expect(result).toContain("</EntityLink>");
        });

        it("should handle empty strings", () => {
            const result = createEntityLink("", "");
            expect(result).toContain('entityKey=""');
            expect(result).toContain('entityName=""');
            expect(result).toContain("<EntityLink");
            expect(result).toContain("</EntityLink>");
        });

        it("should handle special characters", () => {
            const result = createEntityLink("artist-123", "Test & Badge");
            expect(result).toContain("Test & Badge");
            expect(result).toContain('entityName="Test & Badge"');
        });

        it("should handle null entityKey", () => {
            const result = createEntityLink(null, "Test Artist");
            expect(result).toContain('entityKey="null"');
            expect(result).toContain('entityName="Test Artist"');
        });
    });

    describe("createURLBadgeClass", () => {
        it("should return a badge class string", () => {
            const result = createURLBadgeClass("test");
            expect(result).toContain("badge");
            expect(result).toContain("rounded-pill");
        });
    });

    describe("createExternalLinkBadgeClass", () => {
        it("should return Discogs badge class for discogs.com URLs", () => {
            const url = "https://www.discogs.com/artist/123";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return Facebook badge class for facebook.com URLs", () => {
            const url = "https://www.facebook.com/page";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return Bandcamp badge class for bandcamp.com URLs", () => {
            const url = "https://artist.bandcamp.com";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return Soundcloud badge class for soundcloud.com URLs", () => {
            const url = "https://soundcloud.com/user";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return YouTube badge class for youtube.com URLs", () => {
            const url = "https://www.youtube.com/channel";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return MusicBrainz badge class for musicbrainz.org URLs", () => {
            const url = "https://musicbrainz.org/artist";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return Spotify badge class for spotify.com URLs", () => {
            const url = "https://open.spotify.com/artist";
            const result = createExternalLinkBadgeClass(url);
            expect(result).toContain("badge");
            expect(result).toContain(url);
        });

        it("should return Instagram badge class for instagram.com URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://www.instagram.com/user",
            );
            expect(result).toContain("badge");
            // Instagram returns only the badge class string, not the text "Instagram" or the URL
            expect(result).not.toContain("instagram.com");
        });

        it("should return LinkedIn badge class for linkedin.com URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://www.linkedin.com/in/user",
            );
            expect(result).toContain("badge");
            // LinkedIn returns only the badge class string, not the text "LinkedIn" or the URL
            expect(result).not.toContain("linkedin.com");
        });

        it("should return Wikipedia badge class for wikipedia.org URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://en.wikipedia.org/wiki/Page",
            );
            expect(result).toContain("badge");
            // Wikipedia returns only the badge class, not the URL
            expect(result).not.toContain("wikipedia.org");
        });

        it("should return Twitter badge class for twitter.com URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://twitter.com/user",
            );
            expect(result).toContain("badge");
            // Twitter returns only the badge class, not the URL
            expect(result).not.toContain("twitter.com");
        });

        it("should return MySpace badge class for myspace.com URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://myspace.com/user",
            );
            expect(result).toContain("badge");
            // MySpace returns only the badge class, not the URL
            expect(result).not.toContain("myspace.com");
        });

        it("should return LastFM badge class for last.fm URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://www.last.fm/user",
            );
            expect(result).toContain("badge");
            // LastFM returns only the badge class, not the URL
            expect(result).not.toContain("last.fm");
        });

        it("should return Web Archive badge class for web.archive.org URLs", () => {
            const result = createExternalLinkBadgeClass(
                "https://web.archive.org/web/url",
            );
            expect(result).toContain("badge");
            // Web Archive returns only the badge class string, not the text "Web Archive"
            expect(result).not.toContain("web.archive.org");
        });

        it("should return empty string for unknown URLs", () => {
            const result = createExternalLinkBadgeClass("https://example.com");
            expect(result).toBe("");
        });
    });

    describe("createExternalLinkBadgeText", () => {
        it("should return 'Discogs' for discogs.com URLs", () => {
            expect(
                createExternalLinkBadgeText(
                    "https://www.discogs.com/artist/123",
                ),
            ).toBe("Discogs");
        });

        it("should return 'Facebook' for facebook.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://www.facebook.com/page"),
            ).toBe("Facebook");
        });

        it("should return 'Bandcamp' for bandcamp.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://artist.bandcamp.com"),
            ).toBe("Bandcamp");
        });

        it("should return 'Soundcloud' for soundcloud.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://soundcloud.com/user"),
            ).toBe("Soundcloud");
        });

        it("should return 'YouTube' for youtube.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://www.youtube.com/channel"),
            ).toBe("YouTube");
        });

        it("should return 'MusicBrainz' for musicbrainz.org URLs", () => {
            expect(
                createExternalLinkBadgeText("https://musicbrainz.org/artist"),
            ).toBe("MusicBrainz");
        });

        it("should return 'Spotify' for spotify.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://open.spotify.com/artist"),
            ).toBe("Spotify");
        });

        it("should return 'Instagram' for instagram.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://www.instagram.com/user"),
            ).toBe("Instagram");
        });

        it("should return 'LinkedIn' for linkedin.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://www.linkedin.com/in/user"),
            ).toBe("LinkedIn");
        });

        it("should return 'Wikipedia' for wikipedia.org URLs", () => {
            expect(
                createExternalLinkBadgeText(
                    "https://en.wikipedia.org/wiki/Page",
                ),
            ).toBe("Wikipedia");
        });

        it("should return 'Twitter' for twitter.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://twitter.com/user"),
            ).toBe("Twitter");
        });

        it("should return 'MySpace' for myspace.com URLs", () => {
            expect(
                createExternalLinkBadgeText("https://myspace.com/user"),
            ).toBe("MySpace");
        });

        it("should return 'LastFM' for last.fm URLs", () => {
            expect(
                createExternalLinkBadgeText("https://www.last.fm/user"),
            ).toBe("LastFM");
        });

        it("should return 'Web Archive' for web.archive.org URLs", () => {
            expect(
                createExternalLinkBadgeText("https://web.archive.org/web/url"),
            ).toBe("Web Archive");
        });

        it("should return empty string for unknown URLs", () => {
            expect(createExternalLinkBadgeText("https://example.com")).toBe("");
        });
    });

    describe("removeURLProtocol", () => {
        it("should remove http:// protocol", () => {
            expect(removeURLProtocol("http://example.com")).toBe("example.com");
        });

        it("should remove https:// protocol", () => {
            expect(removeURLProtocol("https://example.com")).toBe(
                "example.com",
            );
        });

        it("should not modify URLs without protocol", () => {
            expect(removeURLProtocol("example.com")).toBe("example.com");
        });

        it("should handle URLs with paths", () => {
            expect(removeURLProtocol("https://example.com/path/to/page")).toBe(
                "example.com/path/to/page",
            );
        });

        it("should handle empty string", () => {
            expect(removeURLProtocol("")).toBe("");
        });
    });

    describe("expandCommas", () => {
        it("should add spaces after commas between non-whitespace characters", () => {
            expect(expandCommas("word1,word2")).toBe("word1, word2");
            expect(expandCommas("a,b,c")).toBe("a, b, c");
        });

        it("should not modify strings that already have spaces after commas", () => {
            expect(expandCommas("word1, word2")).toBe("word1, word2");
        });

        it("should not modify strings without commas", () => {
            expect(expandCommas("word1 word2")).toBe("word1 word2");
        });

        it("should handle multiple commas", () => {
            expect(expandCommas("a,b,c,d")).toBe("a, b, c, d");
        });

        it("should handle empty string", () => {
            expect(expandCommas("")).toBe("");
        });

        it("should handle comma at start of string", () => {
            expect(expandCommas(",word")).toBe(", word");
        });

        it("should handle comma at end of string", () => {
            expect(expandCommas("word,")).toBe("word,");
        });

        it("should handle commas with numbers", () => {
            expect(expandCommas("1,2,3")).toBe("1, 2, 3");
        });
    });

    describe("expandBold", () => {
        it("should convert [b]...[/b] tags to bold HTML", () => {
            expect(expandBold("[b]test[/b]")).toBe("<b>test</b>");
        });

        it("should convert [B]...[/B] tags to bold HTML", () => {
            expect(expandBold("[B]test[/B]")).toBe("<b>test</b>");
        });

        it("should handle multiple bold blocks", () => {
            expect(expandBold("[b]first[/b] and [b]second[/b]")).toBe(
                "<b>first</b> and <b>second</b>",
            );
        });

        it("should not modify strings without bold tags", () => {
            expect(expandBold("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandBold("")).toBe("");
        });

        it("should handle adjacent tags", () => {
            expect(expandBold("[b]first[/b][b]second[/b]")).toBe(
                "<b>first</b><b>second</b>",
            );
        });

        it("should handle tags with special characters", () => {
            expect(expandBold("[b]text & more[/b]")).toBe("<b>text & more</b>");
        });
    });

    describe("expandStrong", () => {
        it("should convert [strong]...[/strong] tags to strong HTML", () => {
            expect(expandStrong("[strong]test[/strong]")).toBe(
                "<strong>test</strong>",
            );
        });

        it("should handle case-insensitive tags", () => {
            expect(expandStrong("[STRONG]test[/STRONG]")).toBe(
                "<strong>test</strong>",
            );
        });

        it("should handle multiple strong blocks", () => {
            expect(
                expandStrong(
                    "[strong]first[/strong] and [strong]second[/strong]",
                ),
            ).toBe("<strong>first</strong> and <strong>second</strong>");
        });

        it("should not modify strings without strong tags", () => {
            expect(expandStrong("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandStrong("")).toBe("");
        });
    });

    describe("expandItalic", () => {
        it("should convert [i]...[/i] tags to italic HTML", () => {
            const result = expandItalic("[i]test[/i]");
            expect(result).toBe("<i>test</i>");
        });

        it("should handle multiple italic blocks", () => {
            const result = expandItalic("[i]first[/i] and [i]second[/i]");
            expect(result).toBe("<i>first</i> and <i>second</i>");
        });

        it("should handle nested or complex text", () => {
            const result = expandItalic("Text [i]with italic[/i] more text");
            expect(result).toBe("Text <i>with italic</i> more text");
        });

        it("should not modify strings without italic tags", () => {
            expect(expandItalic("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandItalic("")).toBe("");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandItalic("[I]test[/I]")).toBe("<i>test</i>");
        });

        it("should handle mixed case tags", () => {
            expect(expandItalic("[i]test[/I]")).toBe("<i>test</i>");
        });
    });

    describe("expandEm", () => {
        it("should convert [em]...[/em] tags to emphasis HTML", () => {
            expect(expandEm("[em]test[/em]")).toBe("<em>test</em>");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandEm("[EM]test[/EM]")).toBe("<em>test</em>");
        });

        it("should handle multiple emphasis blocks", () => {
            expect(expandEm("[em]first[/em] and [em]second[/em]")).toBe(
                "<em>first</em> and <em>second</em>",
            );
        });

        it("should not modify strings without emphasis tags", () => {
            expect(expandEm("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandEm("")).toBe("");
        });
    });

    describe("expandMark", () => {
        it("should convert [mark]...[/mark] tags to mark HTML", () => {
            expect(expandMark("[mark]test[/mark]")).toBe("<mark>test</mark>");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandMark("[MARK]test[/MARK]")).toBe("<mark>test</mark>");
        });

        it("should handle multiple mark blocks", () => {
            expect(
                expandMark("[mark]first[/mark] and [mark]second[/mark]"),
            ).toBe("<mark>first</mark> and <mark>second</mark>");
        });

        it("should not modify strings without mark tags", () => {
            expect(expandMark("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandMark("")).toBe("");
        });
    });

    describe("expandSmall", () => {
        it("should convert [small]...[/small] tags to small HTML", () => {
            expect(expandSmall("[small]test[/small]")).toBe(
                "<small>test</small>",
            );
        });

        it("should handle case-insensitive tags", () => {
            expect(expandSmall("[SMALL]test[/SMALL]")).toBe(
                "<small>test</small>",
            );
        });

        it("should handle multiple small blocks", () => {
            expect(
                expandSmall("[small]first[/small] and [small]second[/small]"),
            ).toBe("<small>first</small> and <small>second</small>");
        });

        it("should not modify strings without small tags", () => {
            expect(expandSmall("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandSmall("")).toBe("");
        });
    });

    describe("expandDel", () => {
        it("should convert [del]...[/del] tags to del HTML", () => {
            expect(expandDel("[del]test[/del]")).toBe("<del>test</del>");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandDel("[DEL]test[/DEL]")).toBe("<del>test</del>");
        });

        it("should handle multiple del blocks", () => {
            expect(expandDel("[del]first[/del] and [del]second[/del]")).toBe(
                "<del>first</del> and <del>second</del>",
            );
        });

        it("should not modify strings without del tags", () => {
            expect(expandDel("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandDel("")).toBe("");
        });
    });

    describe("expandIns", () => {
        it("should convert [ins]...[/ins] tags to ins HTML", () => {
            expect(expandIns("[ins]test[/ins]")).toBe("<ins>test</ins>");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandIns("[INS]test[/INS]")).toBe("<ins>test</ins>");
        });

        it("should handle multiple ins blocks", () => {
            expect(expandIns("[ins]first[/ins] and [ins]second[/ins]")).toBe(
                "<ins>first</ins> and <ins>second</ins>",
            );
        });

        it("should not modify strings without ins tags", () => {
            expect(expandIns("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandIns("")).toBe("");
        });
    });

    describe("expandSub", () => {
        it("should convert [sub]...[/sub] tags to sub HTML", () => {
            expect(expandSub("[sub]test[/sub]")).toBe("<sub>test</sub>");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandSub("[SUB]test[/SUB]")).toBe("<sub>test</sub>");
        });

        it("should handle multiple sub blocks", () => {
            expect(expandSub("[sub]first[/sub] and [sub]second[/sub]")).toBe(
                "<sub>first</sub> and <sub>second</sub>",
            );
        });

        it("should not modify strings without sub tags", () => {
            expect(expandSub("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandSub("")).toBe("");
        });
    });

    describe("expandSup", () => {
        it("should convert [sup]...[/sup] tags to sup HTML", () => {
            expect(expandSup("[sup]test[/sup]")).toBe("<sup>test</sup>");
        });

        it("should handle case-insensitive tags", () => {
            expect(expandSup("[SUP]test[/SUP]")).toBe("<sup>test</sup>");
        });

        it("should handle multiple sup blocks", () => {
            expect(expandSup("[sup]first[/sup] and [sup]second[/sup]")).toBe(
                "<sup>first</sup> and <sup>second</sup>",
            );
        });

        it("should not modify strings without sup tags", () => {
            expect(expandSup("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandSup("")).toBe("");
        });
    });

    describe("expandUnderline", () => {
        it("should convert [u]...[/u] tags to underline HTML", () => {
            expect(expandUnderline("[u]test[/u]")).toBe("<u>test</u>");
        });

        it("should convert [U]...[/U] tags to underline HTML", () => {
            expect(expandUnderline("[U]test[/U]")).toBe("<u>test</u>");
        });

        it("should handle multiple underline blocks", () => {
            expect(expandUnderline("[u]first[/u] and [u]second[/u]")).toBe(
                "<u>first</u> and <u>second</u>",
            );
        });

        it("should not modify strings without underline tags", () => {
            expect(expandUnderline("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandUnderline("")).toBe("");
        });
    });

    describe("expandLineBreaks", () => {
        it("should convert \\r\\n to <br/>", () => {
            expect(expandLineBreaks("line1\r\nline2")).toBe("line1<br/>line2");
        });

        it("should handle multiple line breaks", () => {
            expect(expandLineBreaks("line1\r\nline2\r\nline3")).toBe(
                "line1<br/>line2<br/>line3",
            );
        });

        it("should not modify strings without \\r\\n", () => {
            expect(expandLineBreaks("line1\nline2")).toBe("line1\nline2");
        });

        it("should handle empty string", () => {
            expect(expandLineBreaks("")).toBe("");
        });
    });

    describe("expandProfileURLs", () => {
        it("should convert [url=...]...[/url] to anchor tag", () => {
            const result = expandProfileURLs(
                "[url=http://example.com]Link Text[/url]",
            );
            expect(result).toContain('href="http://example.com"');
            expect(result).toContain("Link Text");
            expect(result).toContain('target="_blank"');
            expect(result).toContain('rel="noopener noreferrer"');
        });

        it("should handle multiple URL tags", () => {
            const result = expandProfileURLs(
                "[url=http://example.com]First[/url] and [url=http://test.com]Second[/url]",
            );
            expect(result).toContain('href="http://example.com"');
            expect(result).toContain('href="http://test.com"');
            expect(result).toContain("First");
            expect(result).toContain("Second");
        });

        it("should not modify strings without URL tags", () => {
            expect(expandProfileURLs("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandProfileURLs("")).toBe("");
        });

        it("should handle URL with query parameters", () => {
            const result = expandProfileURLs(
                "[url=http://example.com?param=value]Link[/url]",
            );
            expect(result).toContain('href="http://example.com?param=value"');
            expect(result).toContain("Link");
        });

        it("should handle URL with fragment", () => {
            const result = expandProfileURLs(
                "[url=http://example.com#section]Link[/url]",
            );
            expect(result).toContain('href="http://example.com#section"');
        });

        it("should handle URL with empty text", () => {
            const result = expandProfileURLs("[url=http://example.com][/url]");
            expect(result).toContain('href="http://example.com"');
        });
    });

    describe("expandLinkReferences", () => {
        beforeEach(() => {
            getMockNodeMap().clear();
        });

        it("should replace [a123=Artist Name] with EntityLink component using name from nodeMap if available", () => {
            const mockNode: Partial<SimNode> = {
                name: "Artist Name From Map",
                key: "artist-123",
            };
            getMockNodeMap().set("artist-123", mockNode as SimNode);

            const result = expandLinkReferences("Check out [a123=Provided Name]");
            expect(result).toContain("Artist Name From Map");
            expect(result).toContain('entityKey="artist-123"');
            expect(result).toContain("<EntityLink");
            expect(result).not.toContain("Provided Name");
        });

        it("should replace [a123=Artist Name] with EntityLink component using provided name if not in nodeMap", () => {
            const result = expandLinkReferences("Check out [a999=Unknown Artist]");
            expect(result).toContain("Unknown Artist");
            expect(result).toContain('entityKey="artist-999"');
            expect(result).toContain('entityName="Unknown Artist"');
            expect(result).toContain("<EntityLink");
        });

        it("should handle multiple artist references", () => {
            const mockNode1: Partial<SimNode> = { name: "Artist One", key: "artist-123" };
            const mockNode2: Partial<SimNode> = { name: "Artist Two", key: "artist-456" };
            getMockNodeMap().set("artist-123", mockNode1 as SimNode);
            getMockNodeMap().set("artist-456", mockNode2 as SimNode);

            const result = expandLinkReferences("[a123=First] and [a456=Second]");
            expect(result).toContain("Artist One");
            expect(result).toContain("Artist Two");
            expect(result).toContain('entityKey="artist-123"');
            expect(result).toContain('entityKey="artist-456"');
            expect((result.match(/<EntityLink/g) || []).length).toBe(2);
        });

        it("should handle label references [l123=Label Name]", () => {
            const mockNode: Partial<SimNode> = {
                name: "Label Name From Map",
                key: "label-123",
            };
            getMockNodeMap().set("label-123", mockNode as SimNode);

            const result = expandLinkReferences("Check out [l123=Provided Label]");
            expect(result).toContain("Label Name From Map");
            expect(result).toContain('entityKey="label-123"');
            expect(result).toContain("<EntityLink");
        });

        it("should handle multiple label references", () => {
            const mockNode1: Partial<SimNode> = { name: "Label One", key: "label-123" };
            const mockNode2: Partial<SimNode> = { name: "Label Two", key: "label-456" };
            getMockNodeMap().set("label-123", mockNode1 as SimNode);
            getMockNodeMap().set("label-456", mockNode2 as SimNode);

            const result = expandLinkReferences("[l123=First] and [l456=Second]");
            expect(result).toContain("Label One");
            expect(result).toContain("Label Two");
            expect(result).toContain('entityKey="label-123"');
            expect(result).toContain('entityKey="label-456"');
            expect((result.match(/<EntityLink/g) || []).length).toBe(2);
        });

        it("should handle case-insensitive references", () => {
            const mockNode: Partial<SimNode> = {
                name: "Artist Name",
                key: "artist-123",
            };
            getMockNodeMap().set("artist-123", mockNode as SimNode);

            const result = expandLinkReferences("Check out [A123=Test]");
            expect(result).toContain("Artist Name");
            expect(result).toContain('entityKey="artist-123"');
        });

        it("should handle references with multiple digits", () => {
            const mockNode: Partial<SimNode> = {
                name: "Artist",
                key: "artist-12345",
            };
            getMockNodeMap().set("artist-12345", mockNode as SimNode);

            const result = expandLinkReferences("Check out [a12345=Test]");
            expect(result).toContain("Artist");
            expect(result).toContain('entityKey="artist-12345"');
        });

        it("should handle empty string", () => {
            expect(expandLinkReferences("")).toBe("");
        });

        it("should handle string without link references", () => {
            expect(expandLinkReferences("plain text")).toBe("plain text");
        });

        it("should handle references with special characters in name", () => {
            const result = expandLinkReferences("[a123=Artist & Name]");
            expect(result).toContain("Artist & Name");
            expect(result).toContain('entityName="Artist & Name"');
        });

        it("should handle mixed artist and label references", () => {
            const mockArtist: Partial<SimNode> = { name: "Artist", key: "artist-1" };
            const mockLabel: Partial<SimNode> = { name: "Label", key: "label-2" };
            getMockNodeMap().set("artist-1", mockArtist as SimNode);
            getMockNodeMap().set("label-2", mockLabel as SimNode);

            const result = expandLinkReferences("[a1=Test] and [l2=Test]");
            expect(result).toContain("Artist");
            expect(result).toContain("Label");
            expect(result).toContain('entityKey="artist-1"');
            expect(result).toContain('entityKey="label-2"');
        });
    });

    describe("expandProfileReferences", () => {
        beforeEach(() => {
            getMockNodeMap().clear();
        });

        it("should perform all expansions in sequence", () => {
            const mockNode: Partial<SimNode> = { name: "Test Artist", key: "artist-123" };
            getMockNodeMap().set("artist-123", mockNode as SimNode);

            const input =
                "[a123=Text Artist] [i]italic[/i] word1,word2 [url=http://test.com]Link[/url]";
            const result = expandProfileReferences(input);

            // Check artist link reference was expanded to EntityLink
            expect(result).toContain("Test Artist");
            expect(result).toContain('entityKey="artist-123"');
            expect(result).toContain("<EntityLink");
            // Check italics were expanded
            expect(result).toContain("<i>italic</i>");
            // Check commas were expanded
            expect(result).toContain("word1, word2");
            // Check URL was expanded
            expect(result).toContain('href="http://test.com"');
        });

        it("should handle complex nested patterns", () => {
            const mockNode: Partial<SimNode> = { name: "Artist", key: "artist-1" };
            getMockNodeMap().set("artist-1", mockNode as SimNode);

            const input =
                "[a1=Test] [b]bold[/b] [i]italic[/i] [url=http://test.com]Link[/url]";
            const result = expandProfileReferences(input);

            expect(result).toContain("Artist");
            expect(result).toContain("<b>bold</b>");
            expect(result).toContain("<i>italic</i>");
            expect(result).toContain('href="http://test.com"');
        });

        it("should handle empty string", () => {
            expect(expandProfileReferences("")).toBe("");
        });

        it("should handle string with no special patterns", () => {
            expect(expandProfileReferences("plain text")).toBe("plain text");
        });
    });

    describe("sanitizedData", () => {
        it("should return an object with __html property containing sanitized HTML", () => {
            const input = "<div>Safe HTML</div>";
            const result = sanitizedData(input);
            expect(result).toHaveProperty("__html");
            expect(typeof result.__html).toBe("string");
            expect(result.__html).toContain("Safe HTML");
        });

        it("should sanitize potentially dangerous HTML", () => {
            const input = '<script>alert("xss")</script><div>Safe</div>';
            const result = sanitizedData(input);
            expect(result.__html).not.toContain("<script>");
            expect(result.__html).toContain("Safe");
        });

        it("should handle empty string", () => {
            const result = sanitizedData("");
            expect(result).toHaveProperty("__html");
            expect(result.__html).toBe("");
        });

        it("should preserve safe HTML attributes", () => {
            const input = '<a href="http://example.com">Link</a>';
            const result = sanitizedData(input);
            expect(result.__html).toContain("href");
            expect(result.__html).toContain("Link");
        });

        it("should handle HTML with multiple elements", () => {
            const input = "<div>First</div><p>Second</p>";
            const result = sanitizedData(input);
            expect(result.__html).toContain("First");
            expect(result.__html).toContain("Second");
        });

        it("should sanitize event handlers", () => {
            const input = "<div onclick=\"alert('xss')\">Safe</div>";
            const result = sanitizedData(input);
            expect(result.__html).not.toContain("onclick");
            expect(result.__html).toContain("Safe");
        });
    });
});
