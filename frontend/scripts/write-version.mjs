// Writes dist/version.json so the deploy pipeline can check which commit is live.
// RENDER_GIT_COMMIT is set by Render during the build.
import { writeFileSync } from "node:fs";

const commit = process.env.RENDER_GIT_COMMIT ?? "unknown";
writeFileSync("dist/version.json", JSON.stringify({ commit }) + "\n");
console.log(`wrote dist/version.json for commit ${commit}`);
