// Temas do CodeMirror e do Xterm da IDE, escuro e claro. Fundo neutro, sem efeitos: o estilo "gamer" fica na
// moldura da página. As tags vêm do tokenizer de src/editor/meupia-lang.js (keyword, typeName, atom...).
import { EditorView } from "@codemirror/view";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";
import { CORES_EDITOR, CORES_TERMINAL } from "./editor-cores.js";

function temaEditor(nome) {
  const c = CORES_EDITOR[nome];
  const visual = EditorView.theme({
    "&": { color: c.texto, backgroundColor: c.fundo, height: "100%" },
    ".cm-content": { caretColor: c.cursor, fontFamily: "var(--a-font-mono)", lineHeight: "1.65" },
    ".cm-scroller": { fontFamily: "var(--a-font-mono)" },
    ".cm-cursor, .cm-dropCursor": { borderLeftColor: c.cursor, borderLeftWidth: "2px" },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, ::selection":
      { backgroundColor: c.selecao },
    ".cm-activeLine": { backgroundColor: c.linhaAtiva },
    ".cm-gutters": { backgroundColor: c.gutter, color: c.numeros, borderRight: `1px solid ${c.borda}` },
    ".cm-activeLineGutter": { backgroundColor: c.linhaAtiva, color: c.texto },
    ".cm-lineNumbers .cm-gutterElement": { padding: "0 12px 0 16px" },
    ".cm-matchingBracket, &.cm-focused .cm-matchingBracket": { backgroundColor: c.selecao, outline: "none" },
    ".cm-tooltip": { backgroundColor: c.gutter, border: `1px solid ${c.borda}`, color: c.texto },
    ".cm-tooltip-autocomplete > ul > li[aria-selected]": { backgroundColor: c.selecao, color: c.texto },
    ".cm-panels": { backgroundColor: c.gutter, color: c.texto },
    ".cm-linha-erro": { backgroundColor: c.erro },
  }, { dark: nome === "dark" });

  const realce = HighlightStyle.define([
    { tag: t.keyword, color: c.keyword },
    { tag: [t.typeName], color: c.typeName },
    { tag: [t.string], color: c.string },
    { tag: [t.number], color: c.number },
    { tag: [t.operator], color: c.operator },
    { tag: [t.atom], color: c.atom },
    { tag: [t.comment], color: c.comment, fontStyle: "italic" },
    { tag: [t.variableName], color: c.variableName },
    { tag: [t.punctuation], color: c.punctuation },
  ]);

  return [visual, syntaxHighlighting(realce)];
}

const EXTENSOES = { dark: temaEditor("dark"), light: temaEditor("light") };

export const extensoesEditor = (tema) => EXTENSOES[tema] ?? EXTENSOES.dark;
export const temaTerminal = (tema) => ({ ...(CORES_TERMINAL[tema] ?? CORES_TERMINAL.dark) });
