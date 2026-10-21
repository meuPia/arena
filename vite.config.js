import { defineConfig } from "vite";
import { resolve } from "node:path";

// Build offline (ARENA_OFFLINE=1, usado por scripts/preparar_offline.py): troca as URLs de CDN e do
// PyPI pelas cópias em /vendor, sem editar os arquivos do Lab (ide.html, src/engine/wasm.js).
// Se um trecho sumir (ex.: merge do upstream), o build falha em vez de gerar uma IDE que pede internet.
const ARQUIVO_WHEEL = (nome) => `new URL("/vendor/wheels/${nome}", location.href).href`;
const SUBSTITUICOES = {
  html: [
    ["https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js", "/vendor/pyodide/pyodide.js"],
    ["https://unpkg.com/lucide@0.469.0/dist/umd/lucide.min.js", "/vendor/lucide.min.js"],
    ["https://cdnjs.cloudflare.com/ajax/libs/split.js/1.6.5/split.min.js", "/vendor/split.min.js"],
  ],
  "src/engine/wasm.js": [
    ['"https://cdn.jsdelivr.net/pyodide/v0.25.0/full/"', 'new URL("/vendor/pyodide/", location.href).href'],
    ['"meupia-core=="+version', ARQUIVO_WHEEL('meupia_core-"+version+"-py3-none-any.whl')],
    ['"meupia-testes"', ARQUIVO_WHEEL("meupia_testes-1.0.0-py3-none-any.whl")],
    ['"https://cdn.jsdelivr.net/gh/meuPia/grid@main/dist/meupia_grid-1.0.2-py3-none-any.whl"',
      ARQUIVO_WHEEL("meupia_grid-1.0.2-py3-none-any.whl")],
  ],
};

function substituir(codigo, pares, onde, exigir) {
  for (const [de, para] of pares) {
    if (!codigo.includes(de)) {
      if (exigir) throw new Error(`build offline: "${de}" não encontrado em ${onde}`);
      continue;
    }
    codigo = codigo.replaceAll(de, para);
  }
  return codigo;
}

function arenaOffline() {
  return {
    name: "arena-offline",
    transformIndexHtml: (html, ctx) => substituir(html, SUBSTITUICOES.html, ctx.filename, false),
    transform(codigo, id) {
      if (id.split("?")[0].replaceAll("\\", "/").endsWith("/src/engine/wasm.js")) {
        return substituir(codigo, SUBSTITUICOES["src/engine/wasm.js"], id, true);
      }
    },
    generateBundle(_, bundle) {
      // nenhuma página pode sobrar apontando para a internet
      for (const arquivo of Object.values(bundle)) {
        const texto = arquivo.type === "asset" ? String(arquivo.source) : arquivo.code;
        for (const [de] of SUBSTITUICOES.html) {
          if (typeof texto === "string" && texto.includes(de)) {
            throw new Error(`build offline: ${arquivo.fileName} ainda aponta para ${de}`);
          }
        }
      }
    },
  };
}

// Quatro páginas: painel (login + missões), IDE da missão, placar do telão e painel da banca.
export default defineConfig({
  plugins: process.env.ARENA_OFFLINE === "1" ? [arenaOffline()] : [],
  build: {
    target: "es2022", // main.js usa top-level await
    rollupOptions: {
      input: {
        painel: resolve(import.meta.dirname, "index.html"),
        ide: resolve(import.meta.dirname, "ide.html"),
        placar: resolve(import.meta.dirname, "placar.html"),
        admin: resolve(import.meta.dirname, "admin.html"),
      },
    },
  },
  // `npm run dev` sozinho não roda as funções Python: use `vercel dev` (ver README).
  server: { proxy: process.env.ARENA_API ? { "/api": process.env.ARENA_API } : undefined },
});
