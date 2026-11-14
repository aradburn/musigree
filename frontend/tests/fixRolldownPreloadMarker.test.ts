import { describe, expect, it } from "vitest";

import { stripRolldownPreloadMarker } from "../fixRolldownPreloadMarker";

describe("stripRolldownPreloadMarker", () => {
    it("removes the hash Rolldown appends to an empty preload list", () => {
        const broken =
            "preload(() => import(`./analytics.js`),[]52fb0675ec3cdd6fe818fc32088cc3d3)";

        expect(stripRolldownPreloadMarker(broken)).toBe(
            "preload(() => import(`./analytics.js`),[])",
        );
    });

    it("removes the hash after a dependency preload list", () => {
        const broken =
            "import(`./HelpModal.js`).then(e => e.HelpModal),__vite__mapDeps([0,1])e2febb4c4000b15a95488df652011592)";

        expect(stripRolldownPreloadMarker(broken)).toBe(
            "import(`./HelpModal.js`).then(e => e.HelpModal),__vite__mapDeps([0,1]))",
        );
    });
});
