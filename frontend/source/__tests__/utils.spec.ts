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
    createBadge,
    expandCommas,
    expandItalic,
    expandProfileURLs,
    expandArtistLinkReferences,
    expandLabelLinkReferences,
    expandArtistTextReferences,
    expandLabelTextReferences,
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

    describe("createBadge", () => {
        it("should create a badge HTML string with the given text", () => {
            const result = createBadge("Test Badge");
            expect(result).toContain("Test Badge");
            expect(result).toContain('class="badge');
            expect(result).toContain("<span");
            expect(result).toContain("</span>");
        });

        it("should handle empty string", () => {
            const result = createBadge("");
            expect(result).toContain('class="badge');
            expect(result).toContain("</span>");
        });

        it("should handle special characters", () => {
            const result = createBadge("Test & Badge");
            expect(result).toContain("Test & Badge");
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
    });

    describe("expandArtistLinkReferences", () => {
        beforeEach(() => {
            getMockNodeMap().clear();
        });

        it("should replace [a123] with artist name from nodeMap", () => {
            const mockNode: Partial<SimNode> = {
                name: "Artist Name",
                key: "artist-123",
            };
            getMockNodeMap().set("artist-123", mockNode as SimNode);

            const result = expandArtistLinkReferences("Check out [a123]");
            expect(result).toBe("Check out Artist Name");
        });

        it("should handle multiple artist references", () => {
            const mockNode1: Partial<SimNode> = { name: "Artist One" };
            const mockNode2: Partial<SimNode> = { name: "Artist Two" };
            getMockNodeMap().set("artist-123", mockNode1 as SimNode);
            getMockNodeMap().set("artist-456", mockNode2 as SimNode);

            const result = expandArtistLinkReferences("[a123] and [a456]");
            expect(result).toBe("Artist One and Artist Two");
        });

        it("should keep reference if artist not found", () => {
            const result = expandArtistLinkReferences("Check out [a999]");
            expect(result).toBe("Check out [a999]");
        });

        it("should handle empty string", () => {
            expect(expandArtistLinkReferences("")).toBe("");
        });

        it("should handle string without artist references", () => {
            expect(expandArtistLinkReferences("plain text")).toBe("plain text");
        });
    });

    describe("expandLabelLinkReferences", () => {
        beforeEach(() => {
            getMockNodeMap().clear();
        });

        it("should replace [l123] with label name from nodeMap", () => {
            const mockNode: Partial<SimNode> = {
                name: "Label Name",
                key: "label-123",
            };
            getMockNodeMap().set("label-123", mockNode as SimNode);

            const result = expandLabelLinkReferences("Check out [l123]");
            expect(result).toBe("Check out Label Name");
        });

        it("should handle multiple label references", () => {
            const mockNode1: Partial<SimNode> = { name: "Label One" };
            const mockNode2: Partial<SimNode> = { name: "Label Two" };
            getMockNodeMap().set("label-123", mockNode1 as SimNode);
            getMockNodeMap().set("label-456", mockNode2 as SimNode);

            const result = expandLabelLinkReferences("[l123] and [l456]");
            expect(result).toBe("Label One and Label Two");
        });

        it("should keep reference if label not found", () => {
            const result = expandLabelLinkReferences("Check out [l999]");
            expect(result).toBe("Check out [l999]");
        });

        it("should handle empty string", () => {
            expect(expandLabelLinkReferences("")).toBe("");
        });

        it("should handle string without label references", () => {
            expect(expandLabelLinkReferences("plain text")).toBe("plain text");
        });
    });

    describe("expandArtistTextReferences", () => {
        it("should convert [a=Artist Name] to badge", () => {
            const result = expandArtistTextReferences("[a=Artist Name]");
            expect(result).toContain("Artist Name");
            expect(result).toContain('class="badge');
        });

        it("should handle multiple artist text references", () => {
            const result = expandArtistTextReferences(
                "[a=First Artist] and [a=Second Artist]",
            );
            expect(result).toContain("First Artist");
            expect(result).toContain("Second Artist");
            expect((result.match(/class="badge/g) || []).length).toBe(2);
        });

        it("should not modify strings without artist text references", () => {
            expect(expandArtistTextReferences("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandArtistTextReferences("")).toBe("");
        });
    });

    describe("expandLabelTextReferences", () => {
        it("should convert [l=Label Name] to badge", () => {
            const result = expandLabelTextReferences("[l=Label Name]");
            expect(result).toContain("Label Name");
            expect(result).toContain('class="badge');
        });

        it("should handle multiple label text references", () => {
            const result = expandLabelTextReferences(
                "[l=First Label] and [l=Second Label]",
            );
            expect(result).toContain("First Label");
            expect(result).toContain("Second Label");
            expect((result.match(/class="badge/g) || []).length).toBe(2);
        });

        it("should not modify strings without label text references", () => {
            expect(expandLabelTextReferences("plain text")).toBe("plain text");
        });

        it("should handle empty string", () => {
            expect(expandLabelTextReferences("")).toBe("");
        });
    });

    describe("expandProfileReferences", () => {
        beforeEach(() => {
            getMockNodeMap().clear();
        });

        it("should perform all expansions in sequence", () => {
            const mockNode: Partial<SimNode> = { name: "Test Artist" };
            getMockNodeMap().set("artist-123", mockNode as SimNode);

            const input =
                "[a123] [a=Text Artist] [i]italic[/i] word1,word2 [url=http://test.com]Link[/url]";
            const result = expandProfileReferences(input);

            // Check artist link reference was expanded
            expect(result).toContain("Test Artist");
            // Check artist text reference was converted to badge
            expect(result).toContain("Text Artist");
            expect(result).toContain('class="badge');
            // Check italics were expanded
            expect(result).toContain("<i>italic</i>");
            // Check commas were expanded
            expect(result).toContain("word1, word2");
            // Check URL was expanded
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
    });
});
