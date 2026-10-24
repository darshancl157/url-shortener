import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same-origin in development: the browser only talks to Vite, which forwards /api.
    // 127.0.0.1 rather than localhost: Node may resolve localhost to IPv6 (::1),
    // while uvicorn listens on IPv4 by default.
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
