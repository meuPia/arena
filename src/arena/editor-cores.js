// Cores do editor e do terminal da IDE, por tema. Sem dependências: usadas por editor-tema.js e pelo teste de
// contraste (editor-cores.test.js). Ver design.md da change aplicar-novo-visual.

export const CORES_EDITOR = {
  dark: {
    fundo: "#0B0E14", texto: "#C3CCD8", gutter: "#0B0E14", numeros: "#7D8A9E", linhaAtiva: "#111827",
    selecao: "#24324A", cursor: "#C6FF3D", borda: "#141A24",
    keyword: "#6CC6FF", typeName: "#B39DFF", string: "#E9C46A", number: "#F49B6C", operator: "#8B98AB",
    atom: "#FF8FC6", comment: "#6A7891", variableName: "#C3CCD8", punctuation: "#8B98AB",
    erro: "rgba(255, 122, 138, .16)",
  },
  light: {
    fundo: "#FFFFFF", texto: "#2A323E", gutter: "#FAFBFC", numeros: "#66717F", linhaAtiva: "#F3FBE3",
    selecao: "#D6E9FF", cursor: "#11161E", borda: "#EEF1F5",
    keyword: "#0B62A8", typeName: "#6347C9", string: "#8A5A00", number: "#B0471A", operator: "#5A6576",
    atom: "#A3155C", comment: "#77818F", variableName: "#2A323E", punctuation: "#5A6576",
    erro: "rgba(194, 33, 58, .1)",
  },
};

// Classes de token que precisam de 4,5:1 sobre o fundo (comentário: 3:1).
export const TOKENS_REALCE = ["keyword", "typeName", "string", "number", "operator", "atom", "variableName"];

export const CORES_TERMINAL = {
  dark: {
    background: "#06080B", foreground: "#C3CCD8", cursor: "#C6FF3D", cursorAccent: "#06080B",
    selectionBackground: "#24324A",
    black: "#0E121A", red: "#FF7A8A", green: "#C6FF3D", yellow: "#F2C14E", blue: "#6CC6FF",
    magenta: "#FF6FB4", cyan: "#38E1FF", white: "#E6EDF5",
    brightBlack: "#5E6A7D", brightRed: "#FF9AA6", brightGreen: "#D8FF73", brightYellow: "#F7D47E",
    brightBlue: "#9AD8FF", brightMagenta: "#FF9BCB", brightCyan: "#7DEBFF", brightWhite: "#FFFFFF",
  },
  light: {
    background: "#FAFBFC", foreground: "#2A323E", cursor: "#11161E", cursorAccent: "#FAFBFC",
    selectionBackground: "#D6E9FF",
    black: "#11161E", red: "#B91C36", green: "#3F6A00", yellow: "#7A5A00", blue: "#0B62A8",
    magenta: "#A3155C", cyan: "#0A6E8F", white: "#5A6576",
    brightBlack: "#5A6576", brightRed: "#A3172D", brightGreen: "#2F5200", brightYellow: "#6B4E00",
    brightBlue: "#0A5490", brightMagenta: "#8E1250", brightCyan: "#085D79", brightWhite: "#11161E",
  },
};

function luminancia(hex) {
  const n = parseInt(hex.slice(1), 16);
  const canal = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * canal((n >> 16) & 255) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255);
}

export function contraste(a, b) {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}
