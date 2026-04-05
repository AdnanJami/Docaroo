import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",   // ← required so Docker can expose the port
    port: 3000,
    proxy: {
      // Proxy /api calls to Django — avoids CORS issues in dev
      "/api": {
        target: "http://django:8000",  // use container name, not localhost
        changeOrigin: true,
      },
    },
  },
});