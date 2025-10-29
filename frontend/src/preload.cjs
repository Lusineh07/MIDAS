/**
 * preload.cjs
 * ==========================================================
 * -- Script runs before renderer process is loaded.
 * -- Securely exposes specific backend functions to frontend 
 *    through Electron's contextBridge
 * 
 * -- Prevents direct Node.js access in renderer for security 
 *    for safe communication via IPC (inter-process communication)
 * 
 * TO DO
 * -- link each API
 *  ====================================================== */

const { contextBridge, ipcRenderer } = require('electron');

// Expose API methods to renderer
contextBridge.exposeInMainWorld('electronAPI', {

    // TICKER VALIDATION
    validateTicker: (ticker) => ipcRenderer.invoke('validate-ticker', ticker),

    // TICKER DATA - Fetch quote snapshot (price, bid/ask, SMA comparison)
    getQuote: (ticker) => ipcRenderer.invoke('getQuote', ticker),

    // NEWS/HEADLINES DATA - Retrieve top recent news headlines for ticker
    getNews: (ticker) => ipcRenderer.invoke('getNews', ticker),

    // SENTIMENT ANALYSIS - send fetched headlines to (FinBERT) backend for sent. scoring
    analyzeSentiment: (ticker) => ipcRenderer.invoke('analyzeSentiment', ticker),

    // STRATEGY RECOMMENDER
    getRecommendation: (features) => ipcRenderer.invoke('getRecommendation', features),
    
    // ONE-LINER SUGGESTION
    generateOneLiner: (prompt) => ipcRenderer.invoke('generateOneLiner', prompt),
});


/** Mock Payload Code
 * -- To visualize mock data, remove comment block to implement code
 
 const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('hud', {
    onUpdate: (cb) => {
        const listener = (_event, payload) => cb(payload);
        ipcRenderer.on('hud:update', listener);
    },
    getVersion: () => ipcRenderer.invoke('hud:getVersion')
});
 */
