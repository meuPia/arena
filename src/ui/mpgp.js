export function initPackageManager(getPyodideInstance) {
  const packagesModal = document.getElementById('packages-modal');
  const packagesBtn = document.getElementById('packages-btn');
  const closePackagesBtn = document.getElementById('close-packages-btn');
  const installButtons = document.querySelectorAll('.install-btn');
  const packageLog = document.getElementById('package-status-log');

  const pluginRegistry = {
      "grid": "https://cdn.jsdelivr.net/gh/meuPia/grid@main/dist/meupia_grid-1.0.2-py3-none-any.whl",
      "ia": "https://cdn.jsdelivr.net/gh/meuPia/ia@master/dist/meupia_ia-0.1.0-py3-none-any.whl",
  };

  packagesBtn.addEventListener('click', () => { packagesModal.classList.remove('hidden'); });
  closePackagesBtn.addEventListener('click', () => { packagesModal.classList.add('hidden'); });
  packagesModal.addEventListener('click', (e) => {
    if (e.target === packagesModal) packagesModal.classList.add('hidden');
  });

  installButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const pyodide = getPyodideInstance();
      if (!pyodide) {
          packageLog.style.color = "#f44336";
          packageLog.textContent = "[ERRO] O motor Wasm ainda não está pronto.";
          return;
      }

      const pluginName = e.target.getAttribute('data-plugin');
      const pluginUrl = pluginRegistry[pluginName];
      
      e.target.disabled = true;
      e.target.textContent = "Instalando...";
      packageLog.style.color = "#ffeb3b";
      packageLog.textContent = `[mpgp] Baixando pacote '${pluginName}' do GitHub... aguarde.`;

      try {
        if (!pluginUrl) {
            throw new Error(`Plugin '${pluginName}' não encontrado no registro do Lab.`);
        }

        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        
        await micropip.install(pluginUrl);
        
        e.target.textContent = "Instalado";
        e.target.classList.add("installed");
        packageLog.style.color = "#4CAF50";
        packageLog.textContent = `[mpgp] Sucesso! Pacote '${pluginName}' pronto para uso.`;
        if (pluginName === 'grid') {
            const tabGrid = document.getElementById('tab-grid');
            if (tabGrid) tabGrid.style.display = '';
        }
        
      } catch (error) {
        e.target.disabled = false;
        e.target.textContent = "Tentar Novamente";
        packageLog.style.color = "#f44336";
        packageLog.textContent = `[mpgp] Erro ao instalar ${pluginName}: ${error.message}`;
      }
    });
  });
}