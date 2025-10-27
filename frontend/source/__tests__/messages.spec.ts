import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { showMessage, clearMessages } from "../messages";

describe("Messages Module", () => {
    // Setup and teardown
    let messagesContainer: HTMLDivElement;

    beforeEach(() => {
        // Create a fresh messages container before each test
        messagesContainer = document.createElement("div");
        messagesContainer.id = "message-container";
        document.body.appendChild(messagesContainer);
    });

    afterEach(() => {
        // Clean up after each test
        document.body.innerHTML = "";
        vi.restoreAllMocks();
    });

    describe("showMessage", () => {
        it('should add a message with default type "info"', () => {
            // Act
            showMessage("Test message");

            // Assert
            const alert = messagesContainer.querySelector(".alert");
            expect(alert).toBeTruthy();
            expect(alert?.classList.contains("alert-info")).toBe(true);
            expect(alert?.textContent).toContain("Test message");
        });

        it("should add a message with specified type", () => {
            // Act
            showMessage("Error message", "danger");

            // Assert
            const alert = messagesContainer.querySelector(".alert");
            expect(alert).toBeTruthy();
            expect(alert?.classList.contains("alert-danger")).toBe(true);
            expect(alert?.textContent).toContain("Error message");
        });

        it("should include a close button", () => {
            // Act
            showMessage("Test message");

            // Assert
            const closeButton = messagesContainer.querySelector(".btn-close");
            expect(closeButton).toBeTruthy();
            expect(closeButton?.getAttribute("data-bs-dismiss")).toBe("alert");
        });

        it("should do nothing if messages container does not exist", () => {
            // Arrange
            document.body.innerHTML = ""; // Remove the messages container

            // Act
            showMessage("Test message");

            // Assert
            expect(document.body.innerHTML).toBe("");
        });

        it("should allow multiple messages to be shown", () => {
            // Act
            showMessage("First message");
            showMessage("Second message", "warning");

            // Assert
            const alerts = messagesContainer.querySelectorAll(".alert");
            expect(alerts.length).toBe(2);
            expect(alerts[0]?.textContent).toContain("First message");
            expect(alerts[1]?.textContent).toContain("Second message");
            expect(alerts[1]?.classList.contains("alert-warning")).toBe(true);
        });
    });

    describe("clearMessages", () => {
        it("should clear all messages immediately when no delay is specified", () => {
            // Arrange
            showMessage("Test message 1");
            showMessage("Test message 2");

            // Act
            clearMessages();

            // Assert
            expect(messagesContainer.innerHTML).toBe("");
        });

        it("should clear all messages after specified delay", async () => {
            // Arrange
            showMessage("Test message");
            vi.useFakeTimers();

            // Act
            clearMessages(1000);

            // Assert - messages should still be there before timeout
            expect(messagesContainer.querySelectorAll(".alert").length).toBe(1);

            // Advance timer and check if messages are cleared
            await vi.advanceTimersByTimeAsync(1000);
            expect(messagesContainer.innerHTML).toBe("");

            vi.useRealTimers();
        });

        it("should do nothing if messages container does not exist", () => {
            // Arrange
            document.body.innerHTML = ""; // Remove the messages container

            // Act & Assert - should not throw
            expect(() => clearMessages()).not.toThrow();
        });
    });
});
