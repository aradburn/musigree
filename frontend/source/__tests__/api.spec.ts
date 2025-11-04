/// <reference lib="dom" />
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
    fetchAPINetwork,
    fetchAPIRandom,
    fetchAPIRelations,
    fetchAPIEntity,
} from "../api";
import { getSelectedRoles } from "../roles";
import type { Mock } from "vitest";
import type { APINetworkDataResponse } from "../api";
import type { NetworkCenter } from "../network/data";
import type { RelationsData } from "../relations";
import type { EntityData } from "../entities";

// Mock the roles module
vi.mock("../roles", () => ({
    getSelectedRoles: vi.fn(),
}));

// Mock global fetch
const mockFetch: Mock = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("API Functions", () => {
    beforeEach(() => {
        vi.resetAllMocks();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe("fetchAPINetwork", () => {
        it("should fetch network data with correct URL when no roles selected", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-1", name: "Test Artist" },
                nodes: [],
                links: [],
            };
            const emptyRoles: string[] = [];
            vi.mocked(getSelectedRoles).mockReturnValue(emptyRoles);
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPINetwork("artist-1", emptyRoles);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/artist/network/1");
            expect(result).toEqual(mockResponse);
            expect(result).toHaveProperty("center");
            expect(result).toHaveProperty("nodes");
            expect(result).toHaveProperty("links");
        });

        it("should fetch network data with roles when roles are selected", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-1", name: "Test Artist" },
                nodes: [],
                links: [],
            };
            const selectedRoles = ["producer", "writer"];
            vi.mocked(getSelectedRoles).mockReturnValue(selectedRoles);
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPINetwork("artist-1", selectedRoles);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith(
                "/api/artist/network/1?roles=producer%2Cwriter",
            );
            expect(result).toEqual(mockResponse);
        });

        it("should throw error when fetch fails", async () => {
            // Arrange
            const emptyRoles: string[] = [];
            vi.mocked(getSelectedRoles).mockReturnValue(emptyRoles);
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Not Found",
            });

            // Act & Assert
            await expect(
                fetchAPINetwork("artist-1", emptyRoles),
            ).rejects.toThrow("Not Found");
        });

        it("should handle different entity types correctly", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "label-123", name: "Test Label" },
                nodes: [],
                links: [],
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPINetwork("label-123", []);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/label/network/123");
        });

        it("should handle multiple roles correctly", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-1", name: "Test Artist" },
                nodes: [],
                links: [],
            };
            const multipleRoles = ["producer", "writer", "mixer", "engineer"];
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPINetwork("artist-1", multipleRoles);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith(
                "/api/artist/network/1?roles=producer%2Cwriter%2Cmixer%2Cengineer",
            );
        });
    });

    describe("fetchAPIRandom", () => {
        it("should fetch random entity with correct URL when no roles selected", async () => {
            // Arrange
            const mockResponse: NetworkCenter = {
                center: "artist-1",
            };
            const emptyRoles: string[] = [];
            vi.mocked(getSelectedRoles).mockReturnValue(emptyRoles);
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIRandom(emptyRoles);

            // Assert
            expect(mockFetch.mock.calls[0][0]).toMatch(
                /^\/api\/random\?r=\d+$/,
            );
            expect(result).toEqual(mockResponse);
            expect(result).toHaveProperty("center");
            expect(typeof result.center).toBe("string");
        });

        it("should fetch random entity with roles when roles are selected", async () => {
            // Arrange
            const mockResponse: NetworkCenter = {
                center: "artist-1",
            };
            const selectedRoles = ["producer"];
            vi.mocked(getSelectedRoles).mockReturnValue(selectedRoles);
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIRandom(selectedRoles);

            // Assert
            expect(mockFetch.mock.calls[0][0]).toMatch(
                /^\/api\/random\?r=\d+&roles=producer$/,
            );
            expect(result).toEqual(mockResponse);
        });

        it("should throw error when fetch fails", async () => {
            // Arrange
            const emptyRoles: string[] = [];
            vi.mocked(getSelectedRoles).mockReturnValue(emptyRoles);
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Server Error",
            });

            // Act & Assert
            await expect(fetchAPIRandom(emptyRoles)).rejects.toThrow(
                "Server Error",
            );
        });

        it("should generate different random numbers on multiple calls", async () => {
            // Arrange
            const mockResponse: NetworkCenter = {
                center: "artist-1",
            };
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPIRandom([]);
            await fetchAPIRandom([]);

            // Assert
            const calls = mockFetch.mock.calls;
            expect(calls).toHaveLength(2);

            // Extract random numbers from URLs
            const random1 = calls[0][0].match(/r=(\d+)/)?.[1];
            const random2 = calls[1][0].match(/r=(\d+)/)?.[1];

            expect(random1).toBeDefined();
            expect(random2).toBeDefined();
            expect(random1).not.toBe(random2);
        });

        it("should handle multiple roles correctly", async () => {
            // Arrange
            const mockResponse: NetworkCenter = {
                center: "artist-1",
            };
            const multipleRoles = ["producer", "writer", "mixer"];
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPIRandom(multipleRoles);

            // Assert
            expect(mockFetch.mock.calls[0][0]).toMatch(
                /^\/api\/random\?r=\d+&roles=producer%2Cwriter%2Cmixer$/,
            );
        });
    });

    describe("fetchAPIRelations", () => {
        it("should fetch relations data with correct URL", async () => {
            // Arrange
            const mockResponse: RelationsData = {
                /* mock RelationsData structure */
            } as RelationsData;
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIRelations("artist-1");

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/artist/relations/1");
            expect(result).toEqual(mockResponse);
        });

        it("should throw error when fetch fails", async () => {
            // Arrange
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Bad Request",
            });

            // Act & Assert
            await expect(fetchAPIRelations("artist-1")).rejects.toThrow(
                "Bad Request",
            );
        });

        it("should handle different entity types correctly", async () => {
            // Arrange
            const mockResponse: RelationsData = {} as RelationsData;
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPIRelations("label-123");

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/label/relations/123");
        });
    });

    describe("fetchAPIEntity", () => {
        it("should fetch entity details with correct URL", async () => {
            // Arrange
            const mockResponse: EntityData = {
                id: 1,
                type: "artist",
                name: "Test Artist",
                metadata: {},
                entities: {},
                relation_counts: {},
                countries: "US",
                genres: "Rock",
                styles: "Alternative",
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIEntity("artist-1");

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/artist/details/1");
            expect(result).toEqual(mockResponse);
        });

        it("should handle different entity types correctly", async () => {
            // Arrange
            const mockResponse: EntityData = {
                id: 2,
                type: "label",
                name: "Test Label",
                metadata: {},
                entities: {},
                relation_counts: {},
                countries: "UK",
                genres: null,
                styles: null,
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIEntity("label-456");

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/label/details/456");
            expect(result).toEqual(mockResponse);
        });

        it("should throw error when fetch fails", async () => {
            // Arrange
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Not Found",
            });

            // Act & Assert
            await expect(fetchAPIEntity("artist-999")).rejects.toThrow(
                "Not Found",
            );
        });

        it("should handle network errors", async () => {
            // Arrange
            mockFetch.mockRejectedValueOnce(new Error("Network error"));

            // Act & Assert
            await expect(fetchAPIEntity("artist-1")).rejects.toThrow(
                "Network error",
            );
        });
    });

    describe("URL Construction Edge Cases", () => {
        it("should handle entity keys with special characters", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-test_123", name: "Test Artist" },
                nodes: [],
                links: [],
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPINetwork("artist-test_123", []);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith(
                "/api/artist/network/test_123",
            );
        });

        it("should handle empty roles array", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-1", name: "Test Artist" },
                nodes: [],
                links: [],
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPINetwork("artist-1", []);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith("/api/artist/network/1");
        });

        it("should handle roles with special characters", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-1", name: "Test Artist" },
                nodes: [],
                links: [],
            };
            const rolesWithSpecialChars = ["producer,writer", "mixer/engineer"];
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            await fetchAPINetwork("artist-1", rolesWithSpecialChars);

            // Assert
            expect(mockFetch).toHaveBeenCalledWith(
                "/api/artist/network/1?roles=producer%2Cwriter%2Cmixer%2Fengineer",
            );
        });
    });

    describe("Error Handling Edge Cases", () => {
        it("should handle different HTTP error status codes", async () => {
            // Test 500 error
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Internal Server Error",
                status: 500,
            });

            await expect(fetchAPINetwork("artist-1", [])).rejects.toThrow(
                "Internal Server Error",
            );

            // Test 404 error
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Not Found",
                status: 404,
            });

            await expect(fetchAPIRandom([])).rejects.toThrow("Not Found");

            // Test 403 error
            mockFetch.mockResolvedValueOnce({
                ok: false,
                statusText: "Forbidden",
                status: 403,
            });

            await expect(fetchAPIRelations("artist-1")).rejects.toThrow(
                "Forbidden",
            );
        });

        it("should handle JSON parsing errors", async () => {
            // Arrange
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.reject(new Error("Invalid JSON")),
            });

            // Act & Assert
            await expect(fetchAPINetwork("artist-1", [])).rejects.toThrow(
                "Invalid JSON",
            );
        });

        it("should handle timeout errors", async () => {
            // Arrange
            mockFetch.mockRejectedValueOnce(new Error("Request timeout"));

            // Act & Assert
            await expect(fetchAPIRandom([])).rejects.toThrow("Request timeout");
        });
    });

    describe("Type Safety and Return Value Validation", () => {
        it("should return properly typed APINetworkDataResponse", async () => {
            // Arrange
            const mockResponse: APINetworkDataResponse = {
                center: { key: "artist-1", name: "Test Artist" },
                nodes: [
                    {
                        id: "1",
                        key: "artist-1",
                        name: "Test Artist",
                        size: 10,
                        type: "artist",
                    },
                ],
                links: [
                    {
                        key: "link-1",
                        role: "producer",
                        source: "artist-1",
                        target: "artist-2",
                    },
                ],
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPINetwork("artist-1", []);

            // Assert
            expect(result).toHaveProperty("center");
            expect(result).toHaveProperty("nodes");
            expect(result).toHaveProperty("links");
            expect(result.center).toHaveProperty("key");
            expect(result.center).toHaveProperty("name");
            expect(Array.isArray(result.nodes)).toBe(true);
            expect(Array.isArray(result.links)).toBe(true);
        });

        it("should return properly typed NetworkCenter", async () => {
            // Arrange
            const mockResponse: NetworkCenter = {
                center: "artist-1",
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIRandom([]);

            // Assert
            expect(result).toHaveProperty("center");
            expect(typeof result.center).toBe("string");
        });
    });
});
