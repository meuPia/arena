export function setupLayout(term, fitAddon) {
    const defaultSettings = { layout: 'horizontal', fontSize: 14 };
    let userSettings = JSON.parse(localStorage.getItem('meupia_settings')) || defaultSettings;

    const settingsModal = document.getElementById('settings-modal');
    const layoutSelect = document.getElementById('layout-select');
    const fontsizeInput = document.getElementById('fontsize-input');
    const fontsizeDisplay = document.getElementById('fontsize-display');

    const tabInstrucoes = document.getElementById('tab-instrucoes');
    const tabGrid = document.getElementById('tab-grid');
    const contentInstrucoes = document.getElementById('test-content');
    const contentGrid = document.getElementById('grid-content');

    let mainSplitInstance = null;
    let sideSplitInstance = null;
    let currentInstructions = "";

    window.setInstructions = function (markdownText) {
        currentInstructions = markdownText;
        document.getElementById('test-content').innerHTML = markdownText;
        applySettings();
    };

    function applySettings() {
        const ideContainer = document.getElementById('main-split');
        const sidePane = document.getElementById('side-pane');
        const testPane = document.getElementById('test-pane');
        const terminalPane = document.getElementById('terminal-pane');

        if (mainSplitInstance) mainSplitInstance.destroy();
        if (sideSplitInstance) sideSplitInstance.destroy();

        testPane.style = ''; terminalPane.style = ''; sidePane.style = '';

        const hasInstructions = currentInstructions.trim().length > 0;
        hasInstructions ? testPane.classList.remove('hidden') : testPane.classList.add('hidden');

        ideContainer.style.flexDirection = userSettings.layout === 'vertical' ? 'column' : 'row';

        mainSplitInstance = Split(['#editor-pane', '#side-pane'], {
            direction: userSettings.layout, sizes: [55, 45], minSize: 200, gutterSize: 6,
            onDrag: () => { fitAddon.fit(); }
        });

        sidePane.style.flexDirection = 'column';

        if (hasInstructions) {
            sideSplitInstance = Split(['#test-pane', '#terminal-pane'], {
                direction: 'vertical', sizes: [40, 60], minSize: 100, gutterSize: 6,
                onDrag: () => { fitAddon.fit(); }
            });
        } else {
            terminalPane.style.height = '100%'; terminalPane.style.width = '100%';
        }

        document.documentElement.style.setProperty('--editor-font-size', `${userSettings.fontSize}px`);
        term.options.fontSize = parseInt(userSettings.fontSize);

        setTimeout(() => { fitAddon.fit(); if (window.lucide) window.lucide.createIcons(); }, 50);
        localStorage.setItem('meupia_settings', JSON.stringify(userSettings));

        if (tabInstrucoes && tabGrid) {
            tabInstrucoes.addEventListener('click', () => {
                tabInstrucoes.classList.add('active');
                tabGrid.classList.remove('active');
                contentInstrucoes.classList.remove('hidden');
                contentGrid.classList.add('hidden');
            });
    
            tabGrid.addEventListener('click', () => {
                tabGrid.classList.add('active');
                tabInstrucoes.classList.remove('active');
                contentGrid.classList.remove('hidden');
                contentInstrucoes.classList.add('hidden');
                
                if (window.lucide) window.lucide.createIcons();
            });
        }
    }

    document.getElementById('settings-btn').addEventListener('click', () => {
        layoutSelect.value = userSettings.layout;
        fontsizeInput.value = userSettings.fontSize;
        fontsizeDisplay.textContent = `${userSettings.fontSize}px`;
        settingsModal.classList.remove('hidden');
    });

    document.getElementById('close-settings-btn').addEventListener('click', () => settingsModal.classList.add('hidden'));
    settingsModal.addEventListener('click', (e) => { if (e.target === settingsModal) settingsModal.classList.add('hidden'); });

    layoutSelect.addEventListener('change', (e) => { userSettings.layout = e.target.value; applySettings(); });
    fontsizeInput.addEventListener('input', (e) => {
        userSettings.fontSize = e.target.value;
        fontsizeDisplay.textContent = `${userSettings.fontSize}px`;
        applySettings();
    });

    applySettings(); 
}