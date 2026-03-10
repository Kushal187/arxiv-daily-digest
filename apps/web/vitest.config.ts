import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
      "@shared": path.resolve(__dirname, "../../packages/shared/src")
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"]
  }
});
