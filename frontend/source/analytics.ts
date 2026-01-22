/**
 * @fileoverview Analytics service wrapper for Umami and Swetrix
 * Provides a unified interface for tracking events across different analytics providers
 */

/**
 * Type definitions for analytics providers
 */
interface UmamiProvider {
    track: (event: string, data?: Record<string, unknown>) => void;
    identify?: (userId: string, userData?: Record<string, unknown>) => void;
}

interface SwetrixProvider {
    track: (options: {
        ev: string;
        unique?: boolean;
        profileId?: string;
        meta?: Record<string, unknown>;
    }) => void;
    trackViews: () => void;
    init: (projectId: string, meta?: Record<string, unknown>) => void;
}

/**
 * Analytics provider type
 */
type AnalyticsProvider = "umami" | "swetrix" | "none";

/**
 * Detects which analytics provider is available
 */
function detectProvider(): AnalyticsProvider {
    if (typeof window !== "undefined") {
        // Check for Umami
        if (window.umami && typeof window.umami.track === "function") {
            return "umami";
        }

        // Check for Swetrix
        if (window.swetrix && typeof window.swetrix.track === "function") {
            if (typeof window.swetrix.init === "function") {
                window.swetrix.init("UlCB72ACQWVr", {
                    devMode: true,
                    apiURL: "https://swetrix-api.musigree.com/log",
                });
                window.swetrix.trackViews();
                console.log("Analytics started");
            }
            return "swetrix";
        }
    }

    return "none";
}

/**
 * Analytics service class
 */
class AnalyticsService {
    private provider: AnalyticsProvider;

    constructor() {
        this.provider = detectProvider();
    }

    /**
     * Get the current analytics provider
     */
    getProvider(): AnalyticsProvider {
        return this.provider;
    }

    /**
     * Track an event with optional metadata
     * @param event - Event name
     * @param data - Optional event metadata
     */
    track(event: string, data?: Record<string, unknown>): void {
        switch (this.provider) {
            case "umami": {
                if (window.umami?.track) {
                    window.umami.track(event, data);
                }
                break;
            }
            case "swetrix": {
                if (window.swetrix?.track) {
                    window.swetrix.track({
                        ev: event,
                        meta: data,
                    });
                }
                break;
            }
            case "none":
                // No analytics provider available, silently fail
                break;
        }
    }

    /**
     * Identify a user (Umami only)
     * @param userId - User identifier
     * @param userData - Optional user data
     */
    identify(userId: string, userData?: Record<string, unknown>): void {
        if (this.provider === "umami" && window.umami?.identify) {
            window.umami.identify(userId, userData);
        }
    }
}

// Create singleton instance
export const analytics = new AnalyticsService();

// Export the track function as the main API
export const track = (event: string, data?: Record<string, unknown>): void => {
    analytics.track(event, data);
};

// Export identify function for Umami
export const identify = (
    userId: string,
    userData?: Record<string, unknown>,
): void => {
    analytics.identify(userId, userData);
};

// Extend Window interface to include analytics providers
declare global {
    interface Window {
        umami?: UmamiProvider;
        swetrix?: SwetrixProvider;
    }
}
