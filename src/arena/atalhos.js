// Atalhos de teclado da IDE: Ctrl+Enter = Rodar, Ctrl+Shift+Enter = abrir o Submeter (⌘ no Mac).
// O keydown é ouvido na captura, na window, para passar na frente do CodeMirror (Mod-Enter = inserir linha)
// e do xterm. O atalho só aciona o click() do botão, então faz o mesmo que o clique (main.js, ide-mobile.js,
// submissao.js). Ver design.md da change atalhos-de-teclado-na-ide.

const BOTOES = { rodar: "run-btn", submeter: "submit-btn" };
const ARIA = { rodar: "Control+Enter Meta+Enter", submeter: "Control+Shift+Enter Meta+Shift+Enter" };

// "rodar", "submeter" ou null.
export function atalhoDoEvento(ev) {
  if (!ev || ev.key !== "Enter" || ev.altKey || !(ev.ctrlKey || ev.metaKey)) return null;
  return ev.shiftKey ? "submeter" : "rodar";
}

export function podeAgir({ botao, modalAberto, repeticao }) {
  return Boolean(botao) && !botao.disabled && !modalAberto && !repeticao;
}

export function ehMac(navegador = globalThis.navigator) {
  const plataforma = navegador?.userAgentData?.platform || navegador?.platform || "";
  return /mac|iphone|ipad/i.test(plataforma);
}

export function textoAtalho(acao, mac) {
  const mod = mac ? "⌘" : "Ctrl";
  return acao === "submeter" ? `${mod}+Shift+Enter` : `${mod}+Enter`;
}

const modalAberto = (doc) => [...doc.querySelectorAll(".modal-overlay")].some((m) => !m.classList.contains("hidden"));

export function setupAtalhos({ doc = globalThis.document, janela = globalThis, navegador = globalThis.navigator } = {}) {
  const mac = ehMac(navegador);
  const rodar = doc.getElementById(BOTOES.rodar);
  const submeter = doc.getElementById(BOTOES.submeter);
  if (rodar) rodar.title = `Rodar os testes de exemplo (${textoAtalho("rodar", mac)})`;
  if (submeter) submeter.title = `Envia para o juiz (testes de exemplo + testes extras) (${textoAtalho("submeter", mac)})`;
  for (const [acao, botao] of [["rodar", rodar], ["submeter", submeter]]) botao?.setAttribute("aria-keyshortcuts", ARIA[acao]);

  janela.addEventListener("keydown", (ev) => {
    const acao = atalhoDoEvento(ev);
    if (!acao) return;
    // A combinação nunca tem outro efeito na IDE (ex.: o CodeMirror inserir linha), mesmo sem agir.
    ev.preventDefault();
    ev.stopPropagation();
    const botao = doc.getElementById(BOTOES[acao]);
    if (podeAgir({ botao, modalAberto: modalAberto(doc), repeticao: ev.repeat })) botao.click();
  }, { capture: true });
}
