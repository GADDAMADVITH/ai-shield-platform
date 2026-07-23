import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, type PluginOption } from "vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import { nitro } from "nitro/vite";
import viteReact from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ command }) => {
  const plugins: PluginOption[] = [
    tailwindcss(),
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({
      // Use src/server.ts (SSR error wrapper) instead of the default server entry.
      server: { entry: "server" },
    }),
    viteReact(),
  ];

  // Nitro is only needed for production builds (matches previous local behavior).
  if (command === "build") {
    plugins.push(
      nitro({
        defaultPreset: "cloudflare-module",
      }),
    );
  }

  return {
    server: {
      host: "::",
      port: 8080,
    },
    css: {
      transformer: "lightningcss",
    },
    resolve: {
      alias: {
        "@": path.resolve(rootDir, "./src"),
      },
      dedupe: [
        "react",
        "react-dom",
        "react/jsx-runtime",
        "react/jsx-dev-runtime",
        "@tanstack/react-query",
        "@tanstack/query-core",
      ],
    },
    optimizeDeps: {
      include: [
        "react",
        "react-dom",
        "react-dom/client",
        "react/jsx-runtime",
        "react/jsx-dev-runtime",
      ],
    },
    plugins,
  };
});
