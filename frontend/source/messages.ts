import { MESSAGE } from "./constants";

/**
 * Shows a message in the message container
 */
export const showMessage = (
    message: string,
    type: string = MESSAGE.TYPES.INFO,
): void => {
    const container = document.querySelector(`#${MESSAGE.CONTAINER_ID}`);
    if (!container) {
        console.error("Message container not found");
        return;
    }

    const messageElement = document.createElement("div");
    messageElement.className = `${MESSAGE.ALERT_CLASS.BASE} alert-${type} ${MESSAGE.ALERT_CLASS.DISMISSIBLE} ${MESSAGE.ALERT_CLASS.FADE} ${MESSAGE.ALERT_CLASS.SHOW}`;
    messageElement.setAttribute("role", "alert");
    messageElement.innerHTML = `
        ${message}
        <button type="button" class="${MESSAGE.BUTTON.CLOSE_CLASS}" ${MESSAGE.BUTTON.DISMISS_ATTR}="alert" aria-label="${MESSAGE.BUTTON.ARIA_LABEL}"></button>
    `;
    container.appendChild(messageElement);
};

/**
 * Clears all messages from the message container
 * @param delay - Optional delay in milliseconds before clearing messages
 */
export const clearMessages = (delay: number = 0): void => {
    const clear = (): void => {
        const container = document.querySelector(`#${MESSAGE.CONTAINER_ID}`);
        if (container) {
            container.innerHTML = "";
        }
    };

    if (delay > 0) {
        window.setTimeout(clear, delay);
    } else {
        clear();
    }
};
