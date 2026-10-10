import { defineConfig } from "vite";
import { resolve } from "node:path";

// Três páginas: painel (login + missões), IDE da missão e placar do telão.
export default defineConfig({
  build: {
    target: "es2022", // main.js usa top-level await
    rollupOptions: {
      input: {
        painel: resolve(import.meta.dirname, "index.html"),
        ide: resolve(import.meta.dirname, "ide.html"),
        placar: resolve(import.meta.dirname, "placar.html"),
      },
    },
  },
  // `npm run dev` sozinho não roda as funções Python: use `vercel dev` (ver README).
  server: { proxy: process.env.ARENA_API ? { "/api": process.env.ARENA_API } : undefined },
});
