import { desafioAtual } from "./desafios.js";
import { extrairMensagemErro, mapearLinhaErro, formatarMensagemErro } from "./erros.js";
import { marcarErroCompilacao, limparErroCompilacao } from "../editor/meupia-lang.js";

let pyodide = null;
let version = "1.3.0"

const contarLinhas = (texto) => texto.split("\n").length;

export const getPyodide = () => pyodide;

export async function initWasmEngine(term, runBtn) {
    term.writeln('\x1b[1;33m> Inicializando Motor meuPiá (WebAssembly)...\x1b[0m');

    try {
        pyodide = await loadPyodide({
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/",
            stdout: (text) => term.writeln(text),
            stderr: (text) => term.writeln('\x1b[1;31m' + text + '\x1b[0m'),
            stdin: () => {
                let resposta = window.prompt("O programa está solicitando uma entrada de dados:");
                return resposta !== null ? resposta + "\n" : "\n";
            }
        });

        term.writeln('\x1b[1;34m> Baixando Compilador meuPiá v' + version + '...\x1b[0m');
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        await micropip.install("meupia-core=="+version);
        await micropip.install("meupia-testes");

        if (desafioAtual && desafioAtual.mapa) {
            term.writeln('\x1b[1;36m> Detectado Mapa 2D: Auto-instalando plugin "grid"...\x1b[0m');
            const gridUrl = "https://cdn.jsdelivr.net/gh/meuPia/grid@main/dist/meupia_grid-1.0.2-py3-none-any.whl";
            await micropip.install(gridUrl);
        }

        term.writeln('\x1b[1;32m> Ambiente 100% Pronto!\x1b[0m');
        term.writeln('====================================\n');

        runBtn.disabled = false;
        runBtn.innerHTML = '<i data-lucide="play"></i> Rodar';
        if (window.lucide) window.lucide.createIcons();

    } catch (err) {
        term.writeln('\x1b[1;31m> Falha Crítica:\x1b[0m');
        term.writeln(err.toString());
    }
}

export async function runWasmCode(view, term) {
    const pyodideInstance = getPyodide();
    if (!pyodideInstance) return;
    
    let codigoOriginal = view.state.doc.toString();
    let codigoFinal = codigoOriginal;
    // Informações da montagem do desafio, para converter a linha do erro na linha do editor.
    let infoMontagem = null;

    if (desafioAtual && desafioAtual.codigoTeste) {
        codigoFinal = codigoOriginal.replace(/fim_algoritmo/gi, "");
        let linhaUsarTestes = null;

        if (!codigoFinal.toLowerCase().includes('usar "testes"')) {
            const regexAlgoritmo = /(algoritmo\s+"[^"]*")/i;
            const matchAlgoritmo = codigoFinal.match(regexAlgoritmo);
            if (matchAlgoritmo) {
                linhaUsarTestes = contarLinhas(codigoFinal.slice(0, matchAlgoritmo.index + matchAlgoritmo[0].length)) + 1;
            }
            codigoFinal = codigoFinal.replace(regexAlgoritmo, '$1\nusar "testes"');
        }

        const inicioAnexo = contarLinhas(codigoFinal) + 1;
        codigoFinal += `\n\n// --- TESTES AUTOMATIZADOS ---\n`;
        codigoFinal += desafioAtual.codigoTeste;
        codigoFinal += `\nfim_algoritmo`;

        infoMontagem = { linhaUsarTestes, inicioAnexo, linhaFimAnexado: contarLinhas(codigoFinal) };
    }

    term.write('\r\n\x1b[1;34m[COMPILANDO' + (desafioAtual ? ' COM DESAFIO' : '') + ']\x1b[0m\r\n');

    try {
        pyodideInstance.globals.set("codigo_portugol", codigoFinal);
        
        await pyodideInstance.runPythonAsync(`
import os
import sys
import io
from meuPia.compiler import main 

os.makedirs("output", exist_ok=True)
if os.path.exists("output/main.py"):
    os.remove("output/main.py")

with open("main.por", "w", encoding="utf-8") as f:
    f.write(codigo_portugol)

stdout_original = sys.stdout 
limbo = io.StringIO()
sys.stdout = limbo   

try:
    codigo_retorno = main("main.por", "output")
finally:
    sys.stdout = stdout_original

if codigo_retorno is None:
    codigo_retorno = -1
saida_compilador = limbo.getvalue()
gerou_py = os.path.exists("output/main.py")
        `);

        const codigoRetorno = pyodideInstance.globals.get("codigo_retorno");
        const saidaCompilador = pyodideInstance.globals.get("saida_compilador");
        const gerouPy = pyodideInstance.globals.get("gerou_py");

        if (codigoRetorno !== 0 || !gerouPy) {
            const erro = extrairMensagemErro(saidaCompilador);
            const mapeado = erro.linha !== null ? mapearLinhaErro(erro.linha, infoMontagem) : null;

            term.writeln('\x1b[1;31m[ERRO DE COMPILAÇÃO]\x1b[0m');
            formatarMensagemErro(erro, mapeado).split("\n").forEach(linha => term.writeln(linha));

            if (mapeado && mapeado.origem === "editor") {
                marcarErroCompilacao(view, mapeado.linha, erro.coluna);
            } else {
                limparErroCompilacao(view);
            }
            return;
        }

        limparErroCompilacao(view);

        await pyodideInstance.runPythonAsync(`
with open("output/main.py", "r", encoding="utf-8") as f:
    codigo_python_gerado = f.read()

print("\\033[1;32m[EXECUTANDO]\\033[0m")
print("")

try:
    exec(codigo_python_gerado, {"__name__": "__main__"})
except SystemExit:
    pass
        `);
        term.write('\r\n\x1b[1;32m[FIM DO PROGRAMA]\x1b[0m\r\n');
    } catch (err) {
        term.writeln(`\r\n\x1b[1;31m[ERRO DO SISTEMA]\x1b[0m`);
        term.writeln(err.toString());
    }
}