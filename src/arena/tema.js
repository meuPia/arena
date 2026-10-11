// Tema da Arena (escuro/claro): aplica no <html data-theme>, lembra a escolha no localStorage e avisa a
// página (evento "arena:tema") para o editor e o terminal trocarem de cores. O script inline do <head> de cada
// página faz a primeira aplicação, antes do CSS pintar (sem flash); este módulo cuida do resto.

export const CHAVE_TEMA = "arena_tema";
export const TEMAS = ["dark", "light"];
export const TEMA_PADRAO = "dark";

const valido = (t) => (TEMAS.includes(t) ? t : null);

function storagePadrao() {
  try { return globalThis.localStorage ?? null; } catch { return null; }
}

export function lerTemaSalvo(storage = storagePadrao()) {
  try { return valido(storage?.getItem(CHAVE_TEMA)) ?? TEMA_PADRAO; } catch { return TEMA_PADRAO; }
}

export function gravarTema(tema, storage = storagePadrao()) {
  try { storage?.setItem(CHAVE_TEMA, tema); return true; } catch { return false; }
}

export function temaAtual(doc = globalThis.document) {
  return valido(doc?.documentElement?.dataset?.theme) ?? lerTemaSalvo();
}

export function definirTema(tema, { doc = globalThis.document, storage = storagePadrao(), salvar = true } = {}) {
  const t = valido(tema) ?? TEMA_PADRAO;
  if (doc?.documentElement) doc.documentElement.dataset.theme = t;
  if (salvar) gravarTema(t, storage);
  atualizarBotoes(doc, t);
  globalThis.dispatchEvent?.(new CustomEvent("arena:tema", { detail: { tema: t } }));
  return t;
}

export function alternarTema(opcoes = {}) {
  const doc = opcoes.doc ?? globalThis.document;
  return definirTema(temaAtual(doc) === "dark" ? "light" : "dark", opcoes);
}

// Botões com [data-alternar-tema]: ícone de lua no escuro (vai para o claro) e de sol no claro.
function atualizarBotoes(doc, tema) {
  if (!doc?.querySelectorAll) return;
  const rotulo = tema === "dark" ? "Mudar para o tema claro" : "Mudar para o tema escuro";
  doc.querySelectorAll("[data-alternar-tema]").forEach((b) => {
    b.setAttribute("aria-label", rotulo);
    b.title = rotulo;
    b.innerHTML = `<i data-lucide="${tema === "dark" ? "sun" : "moon"}"></i>`;
  });
  globalThis.lucide?.createIcons?.();
}

export function iniciarTema(doc = globalThis.document) {
  if (!doc) return;
  atualizarBotoes(doc, temaAtual(doc));
  doc.addEventListener("click", (ev) => {
    if (ev.target.closest?.("[data-alternar-tema]")) alternarTema({ doc });
  });
  // Outra aba mudou o tema (ex.: o painel aberto atrás da IDE).
  globalThis.addEventListener?.("storage", (ev) => {
    if (ev.key === CHAVE_TEMA && valido(ev.newValue)) definirTema(ev.newValue, { doc, salvar: false });
  });
}

if (typeof document !== "undefined") iniciarTema(document);
