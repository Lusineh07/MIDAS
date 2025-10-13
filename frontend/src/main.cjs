/**
 * main.cjs
 * ==========================================================
 * Electron Main process
 * -- Creates the transparent always-on-top HUD window
 * -- Connects to external APIs (Finnhub, etc.)
 * -- Handles app lifecycle events
 * 
 * -- Prevents direct Node.js access in renderer for security 
 *    for safe communication via IPC (inter-process communication)
 * 
 * -- Mock data is available to visualize ticker information in 
 *    comment blocks
 * 
 * TO DO:
 * -- link strat recommender/one-liner + any unlisted components
 * -- tooltips
 * -- rate limiting or caching?
 *  ====================================================== */

const { app, BrowserWindow, ipcMain, nativeTheme } = require('electron');
const path = require('path');
const axios = require('axios'); // for HTTP requests (APIs)
// require('dotenv').config(); load api keys from .env


let mainWindow;

/** -----------------------
 * Creates main HUD window
 * --------------------- */

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 40,   // Creates thin ribbon window 
        minWidth: 900,
        maxHeight: 40,    // Prevents vertical resizing
        useContentSize: true,
        resizable: true,    // Users can expand or collapse window horizontally 
        movable: true,
        frame: false,   // For transparent look
        thickFrame: false,
        transparent: true,
        alwaysOnTop: true,
        hasShadow: true,
        backgroundColor: '#00000000',
        webPreferences: {
          preload: path.join(__dirname, 'preload.cjs'),
          contextIsolation: true,
          nodeIntegration: false,
          devTools: true,
          sandbox: true
    },
  });
      

 // Allow only horizontal resize: lock height after resize attempts.
mainWindow.on('resize', () => {
    const [w] = win.getSize();
    mainWindow.setSize(w, 40);
  });

// Loads the renderer
mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

// Aligns dark mode with Windows theme
  nativeTheme.themeSource = 'dark';
}


app.commandLine.appendSwitch('enable-expiermental-web-platform-features');


/** -----------------------
 * App's Lifecycle
 * --------------------- */

app.whenReady().then(() => { // When ready, HUD window is created
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Allows clean quits
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});



/** -----------------------------
 * IPC Listener - Stock Quotes
 * -- Fetches ticker data from stock quotes - Finnhub ()
 * -- Triggered when renderer sends "getQuote"
 * ----------------------------*/

ipcMain.handle('getQuote', async (event, ticker) => {
  try {
    const url = `finnhub? api url/key here`;
    const response = await axios.get(url);
    return { success: true, data: response.data };
  }
  catch (err) {
    return { success: false, error:err.message };
  }
});



/** -----------------------------
 * IPC Listener - News Headlines
 * -- Fetches ticker data from stock quotes - Finnhub ()
 * -- Triggered when renderer sends "getQuote"
 * ----------------------------*/

ipcMain.handle('getNews', async (event, ticker) => {
  try {
    const url = `finnhub? api url/key here`;
    const response = await axios.get(url);
    return { success: true, data: response.data.slice(0,3) }; // grabs top 3 headlines (feel free to change)
  }
  catch (err) {
    return { success: false, error:err.message };
  }
});



/** -----------------------------
 * IPC Listener - Sentiment (Dammy/Isaac)
 * -- Fetches ticker data from FinBERT/LLM ?
 * -- Triggered when renderer sends "analyzeSentiment"
 * ----------------------------*/

ipcMain.handle('analyzeSentiment', async (event, headlines) => {
  try {
    const response = await axios.post('llm api url for sentiment here', {
      text: headlines.join('\n')
    });
    return { success: true, data: response.data };
  }
  catch (err) {
    return { success: false, error:err.message };
  }
});



/** -----------------------------
 * IPC Listener - Strategy Recommender
 * ----------------------------*/



/** -----------------------------
 * IPC Listener - One-Liner 
 * ----------------------------*/



/** Placeholder Code for Mock Data
 * -- To visualize code, remove comment block to allow code to be implemented.
ipcMain.handle('hud:getVersion', () => app.getVersion());

// MOCK DATA FOR VISUALIZATION
let tick = 0;
function mockPayload() {
  tick++;
  const pos = Math.sin(tick / 6) * 0.4; // toy movement
  return {
    symbol: 'NVDA',   // Ticker
    quote: {  // News & Quotes
      last: +(486.00 + pos).toFixed(2),
      bid: 485.9,
      ask: 486.1,
      ret_1m_pct: +(pos * 0.5).toFixed(2),    // 1m Short-Term Return
      ret_5m_pct: +(pos * 0.8).toFixed(2),    // 5m Short-Term Return
      sma20_distance_pct: +(1.7 + pos * 0.3).toFixed(2)
    },
    sentiment: { mean: +(0.31 + pos * 0.2).toFixed(2), stdev: 0.12 },
    strategy: { code: 'IC', confidence_pct: 76 },
    one_liner:
      'Iron condor. Mean ~0; range day. Risk: trend break. Reuters • WSJ',
    sources: ['Reuters', 'WSJ'],
    cache_age_seconds: tick
  };
}

setInterval(() => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('hud:update', mockPayload());
  }
}, 1000); */



