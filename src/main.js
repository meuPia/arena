import { EditorState, Compartment } from "@codemirror/state";
import { EditorView, basicSetup } from "codemirror";
import { history } from "@codemirror/commands";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { meuPiaLanguage, meuPiaAutocompletion, meuPiaErroCompilacao } from "./editor/meupia-lang.js";
import { initWasmEngine, runWasmCode, getPyodide } from "./engine/wasm.js";
import { carregarDesafioDaURL, desafioAtual } from "./engine/desafios.js";
import { renderDesafio, parseTestLine } from "./ui/instructions.js";
import { setupToolbar } from "./ui/toolbar.js";
import { setupAjuda } from "./arena/ajuda.js";
import cartaoDialeto from "./arena/cartao.js";
import { setupLayout } from "./ui/layout.js";
import { setupSubmissao } from "./arena/submissao.js";
import { gravarRascunho } from "./arena/api.js";
import { GridManager } from "./engine/grid/gridManager.js";
import { temaAtual } from "./arena/tema.js";
import { extensoesEditor, temaTerminal } from "./arena/editor-tema.js";

const hasDesafio = await carregarDesafioDaURL();
if (!hasDesafio) throw new Error("[arena] sem missão: redirecionando ao painel");

const term = new Terminal({ 
  theme: temaTerminal(temaAtual()), // Arena: tema do terminal segue o tema da página
  fontFamily: '"JetBrains Mono", ui-monospace, Menlo, Consolas, monospace',
  cursorBlink: true, 
  fontSize: 14 
});

const fitAddon = new FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById("terminal-pane"));

const originalWriteln = term.writeln.bind(term);
term.writeln = (text) => {
  originalWriteln(text);
  parseTestLine(text); 
};

window.addEventListener('resize', () => fitAddon.fit());

const themeConfig = new Compartment();
let docInicial = `algoritmo "MissaoWeb"\ninicio\n    escreva("meuPiá Lab pronto!")\nfim_algoritmo`;
if (hasDesafio) {
  const tabGrid = document.getElementById('tab-grid');
  if (hasDesafio && desafioAtual.mapa) {
      tabGrid.style.display = ''; 
  } else {
      tabGrid.style.display = 'none'; 
  }

  if (desafioAtual.codigoInicial) {
      docInicial = desafioAtual.codigoInicial;
  } else {
      docInicial = `algoritmo "${desafioAtual.id}"\ninicio\n    // Escreva sua solução aqui\nfim_algoritmo`;
  }
}

const view = new EditorView({
  state: EditorState.create({
    doc: docInicial,
    extensions: [ 
      basicSetup, 
      meuPiaLanguage, 
      meuPiaAutocompletion,
      meuPiaErroCompilacao,
      themeConfig.of(extensoesEditor(temaAtual())), 
      history(), 
      EditorView.updateListener.of((u) => {
        if (u.docChanged && desafioAtual) gravarRascunho(desafioAtual.codigo, u.state.doc.toString());
      }),
      EditorView.lineWrapping 
    ]
  }),
  parent: document.getElementById("editor-pane")
});

setupToolbar(view, term, themeConfig);
setupAjuda(view, cartaoDialeto);

// Arena: troca de tema (botão da IDE ou outra aba) reconfigura editor e terminal sem perder código nem histórico.
window.addEventListener("arena:tema", (ev) => {
  view.dispatch({ effects: themeConfig.reconfigure(extensoesEditor(ev.detail.tema)) });
  term.options.theme = temaTerminal(ev.detail.tema);
});
setupLayout(term, fitAddon);

if (hasDesafio) {
  renderDesafio(desafioAtual);
  setupSubmissao(view, desafioAtual);
  if (window.setInstructions) {
      window.setInstructions(document.getElementById('test-content').innerHTML);
  }
} else {
  if (window.setInstructions) {
      window.setInstructions(""); 
  }
}

const runBtn = document.getElementById("run-btn");
const gridManager = new GridManager();

window.meuPiaGridAPI = {
  iniciar: (w, h) => gridManager.iniciarGrid(w, h),
  parede: (x, y) => gridManager.definirParede(x, y),
  visitar: (x, y, step) => gridManager.visitarCelula(x, y, step),
  reset: () => gridManager.reset(),
  play: () => gridManager.autoPlay(),
  hasAnimation: () => gridManager.hasAnimation(),
  carregarMapa: (mapa) => gridManager.carregarMapaDesafio(mapa),
  sensor: (x, y) => gridManager.sensorCelula(x, y),
  chegouNoObjetivo: (alvo_x, alvo_y) => {
      const timeline = gridManager.state.timeline;
      if (timeline.length === 0) return false;
      const ultimoPasso = timeline[timeline.length - 1];
      return ultimoPasso.x === alvo_x && ultimoPasso.y === alvo_y;
  }
};

if (hasDesafio && desafioAtual.mapa) {
  window.meuPiaGridAPI.carregarMapa(desafioAtual.mapa);
}

runBtn.addEventListener("click", async () => {
    const resultsContainer = document.getElementById('test-results');
    if (resultsContainer) resultsContainer.innerHTML = '';
      if (window.meuPiaGridAPI) {
      if (hasDesafio && desafioAtual.mapa) {
          window.meuPiaGridAPI.carregarMapa(desafioAtual.mapa);
      } else {
          window.meuPiaGridAPI.reset();
      }
  }
  
    await runWasmCode(view, term);
    if (window.meuPiaGridAPI && window.meuPiaGridAPI.hasAnimation()) {
      const tabGrid = document.getElementById('tab-grid');
      if (tabGrid) {
          tabGrid.style.display = ''; 
          if (!tabGrid.classList.contains('active')) {
              tabGrid.click(); 
          }
      }
      window.meuPiaGridAPI.play();
    }
});

initWasmEngine(term, runBtn);
setTimeout(() => { if (window.lucide) window.lucide.createIcons(); }, 100);