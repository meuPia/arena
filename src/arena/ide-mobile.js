// IDE no celular (≤ 768 px, ou deitado: altura ≤ 500 px com tela de toque): os painéis viram abas (Código, Missão, Terminal), as ferramentas secundárias vão
// para o menu "Mais" e Rodar/Submeter ficam no rodapé. A disposição é toda do CSS (arena.css, bloco "IDE no
// celular"), guiada por <body data-aba>; o Split.js do Lab continua montado e volta a mandar fora dessa consulta.
// Nada aqui destrói o editor ou o terminal: trocar de aba não perde código, histórico nem saída.

export const ABAS = ["codigo", "missao", "terminal"];
export const ABA_PADRAO = "codigo";
export const CONSULTA_CELULAR = "(max-width: 768px), (max-height: 500px) and (pointer: coarse)";

export function normalizarAba(valor) {
  return ABAS.includes(valor) ? valor : ABA_PADRAO;
}

// Grava a aba no <body> e deixa só a aba ativa com aria-selected="true" (e no Tab do teclado).
export function aplicarAba(doc, aba) {
  const a = normalizarAba(aba);
  doc.body.dataset.aba = a;
  doc.querySelectorAll("[data-aba-alvo]").forEach((b) => {
    const ativa = b.dataset.abaAlvo === a;
    b.setAttribute("aria-selected", String(ativa));
    b.tabIndex = ativa ? 0 : -1;
    if (ativa) delete b.dataset.novo;
  });
  return a;
}

// O xterm mede 0 enquanto oculto: depois de mostrar o Terminal, um "resize" sintético faz o listener do
// main.js chamar fitAddon.fit() já com o painel visível.
export function mostrarAba(doc, aba, { agendar = globalThis.requestAnimationFrame, janela = globalThis } = {}) {
  const a = aplicarAba(doc, aba);
  if (a === "terminal") agendar?.(() => janela.dispatchEvent(new Event("resize")));
  return a;
}

export function deveIrParaTerminal(ehCelular) {
  return Boolean(ehCelular);
}

// Menu "Mais": abre/fecha pelo botão; fecha com Esc, com toque fora e depois de escolher uma opção.
export function criarMenu({ botao, painel, doc }) {
  const menu = {
    aberto: () => painel.classList.contains("aberto"),
    abrir() { painel.classList.add("aberto"); botao.setAttribute("aria-expanded", "true"); },
    fechar() { painel.classList.remove("aberto"); botao.setAttribute("aria-expanded", "false"); },
    alternar() { menu.aberto() ? menu.fechar() : menu.abrir(); },
  };
  botao.addEventListener("click", () => menu.alternar());
  painel.addEventListener("click", (ev) => { if (ev.target.closest?.("button, a")) menu.fechar(); });
  doc.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && menu.aberto()) { menu.fechar(); botao.focus?.(); }
  });
  doc.addEventListener("pointerdown", (ev) => {
    if (menu.aberto() && !painel.contains(ev.target) && !botao.contains(ev.target)) menu.fechar();
  });
  return menu;
}

export function iniciarIdeMobile(doc = globalThis.document, janela = globalThis) {
  const barra = doc.querySelector(".arena-abas-mobile");
  if (!barra) return;
  const celular = janela.matchMedia?.(CONSULTA_CELULAR);
  const ehCelular = () => Boolean(celular?.matches);

  aplicarAba(doc, ABA_PADRAO);
  barra.addEventListener("click", (ev) => {
    const b = ev.target.closest?.("[data-aba-alvo]");
    if (b) mostrarAba(doc, b.dataset.abaAlvo);
  });
  // Setas esquerda/direita entre as abas (padrão de tablist).
  barra.addEventListener("keydown", (ev) => {
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    const i = ABAS.indexOf(doc.body.dataset.aba) + (ev.key === "ArrowRight" ? 1 : -1);
    const a = mostrarAba(doc, ABAS[(i + ABAS.length) % ABAS.length]);
    barra.querySelector(`[data-aba-alvo="${a}"]`)?.focus();
  });

  const botao = doc.getElementById("mais-btn"), painel = doc.getElementById("mais-menu");
  if (botao && painel) criarMenu({ botao, painel, doc });

  // Desfazer/refazer a um toque no cabeçalho do celular: repassam aos botões do Lab (toolbar.js).
  for (const [m, original] of [["undo-btn-m", "undo-btn"], ["redo-btn-m", "redo-btn"]]) {
    doc.getElementById(m)?.addEventListener("click", () => doc.getElementById(original)?.click());
  }

  doc.getElementById("run-btn")?.addEventListener("click", () => {
    if (deveIrParaTerminal(ehCelular())) mostrarAba(doc, "terminal");
  });

  // Resultados novos dos testes de exemplo com a aba Missão fora da vista: marca a aba.
  const conteudo = doc.getElementById("test-content");
  if (conteudo && janela.MutationObserver) {
    new janela.MutationObserver((mudancas) => {
      if (doc.body.dataset.aba === "missao") return;
      const novo = mudancas.some((m) => [...m.addedNodes].some((n) => n.classList?.contains("test-item")));
      if (novo) barra.querySelector('[data-aba-alvo="missao"]').dataset.novo = "1";
    }).observe(conteudo, { childList: true, subtree: true });
  }

  // Altura visível de verdade (Safari iOS ignora interactive-widget e não encolhe o dvh com o teclado).
  const vv = janela.visualViewport;
  if (vv) {
    const ajustar = () => {
      doc.documentElement.style.setProperty("--a-vh", `${Math.round(vv.height)}px`);
      if (ehCelular() && doc.body.dataset.aba === "terminal") janela.requestAnimationFrame?.(() => janela.dispatchEvent(new Event("resize")));
    };
    ajustar();
    vv.addEventListener("resize", ajustar);
  }
}

if (typeof document !== "undefined") iniciarIdeMobile(document, window);
