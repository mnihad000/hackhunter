import assert from "node:assert/strict";
import { resolveApiBaseUrl } from "../src/api.ts";

assert.equal(resolveApiBaseUrl({ DEV: true }), "/api");
assert.equal(
  resolveApiBaseUrl({ DEV: false, VITE_API_BASE_URL: "https://piggybank-backend.up.railway.app" }),
  "https://piggybank-backend.up.railway.app",
);
assert.throws(
  () => resolveApiBaseUrl({ DEV: false }),
  /VITE_API_BASE_URL is required for production builds\./,
);

console.log("apiConfig assertions passed");
