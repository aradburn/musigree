/// <reference lib="dom" />
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchAPINetwork, fetchAPIRandom, fetchAPIRadial } from "../api";
import { getSelectedRoles } from "../roles";
import type { Mock } from "vitest";

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
            const mockResponse = {
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
        });

        it("should fetch network data with roles when roles are selected", async () => {
            // Arrange
            const mockResponse = {
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
    });

    describe("fetchAPIRandom", () => {
        it("should fetch random entity with correct URL when no roles selected", async () => {
            // Arrange
            const mockResponse = { key: "artist-1", name: "Random Artist" };
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
        });

        it("should fetch random entity with roles when roles are selected", async () => {
            // Arrange
            const mockResponse = { key: "artist-1", name: "Random Artist" };
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
    });

    describe("fetchAPIRadial", () => {
        it("should fetch radial data with correct URL", async () => {
            // Arrange
            const mockResponse = {
                /* mock RelationsData structure */
            };
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            });

            // Act
            const result = await fetchAPIRadial("artist-1");

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
            await expect(fetchAPIRadial("artist-1")).rejects.toThrow(
                "Bad Request",
            );
        });
    });
});
