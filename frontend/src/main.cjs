/**
 * main.cjs — Electron main (Windows)
 */
const { app, BrowserWindow, ipcMain, nativeTheme, shell } = require('electron');
const path = require('path');
const axios = require('axios');

// Load .env from frontend/.env (fallback-safe)
try {
  const envPath = path.resolve(__dirname, '..', '.env');
  require('dotenv').config({ path: envPath, override: true });
} catch {}

// API keys (frontend-only usage here)
const FINNHUB_API_KEY = process.env.FINNHUB_API_KEY || '';
const TIINGO_API_KEY  = process.env.TIINGO_API_KEY  || '';

if (!FINNHUB_API_KEY) console.warn('[WARN] FINNHUB_API_KEY is missing. Create frontend/.env with FINNHUB_API_KEY=...');
if (!TIINGO_API_KEY)  console.warn('[INFO] TIINGO_API_KEY not set (only needed if you call Tiingo from main).');

// Single axios client
const http = axios.create({
  timeout: 10_000,
  headers: { 'User-Agent': 'MIDAS-HUD/1.0 (+electron)' },
  validateStatus: (s) => s >= 200 && s < 300
});

let mainWindow;

function createWindow () {
  // Ensure Windows taskbar uses our identity + icon
  if (process.platform === 'win32') {
    // Must be set BEFORE creating BrowserWindow for taskbar icon consistency
    app.setAppUserModelId('com.midas.hud');
  }

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 120,
    minWidth: 900,
    // You’re treating this like a thin HUD; we clamp height to 40 in resize handler
    maxHeight: 120,
    useContentSize: true,
    resizable: true,
    movable: true,
    frame: false,
    thickFrame: false,
    transparent: true,
    alwaysOnTop: true,
    hasShadow: true,
    backgroundColor: '#00000000',
    // ✅ Window/Taskbar icon (built by your gen-icon script -> build/icon.ico)
    icon: path.join(__dirname, '..', 'build', 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true,
      sandbox: true
    }
  });

  // // Keep height ~40px while allowing width to change
  // mainWindow.on('resize', () => {
  //   const [w] = mainWindow.getSize();
  //   if (mainWindow) mainWindow.setSize(w, 40);
  // });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  mainWindow.webContents.openDevTools({ mode: 'detach' });

  nativeTheme.themeSource = 'dark';
}

// Optional Chromium flags
app.commandLine.appendSwitch('enable-experimental-web-platform-features');

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

/* ---------- IPC: open external link (renderer -> main) ---------- */
ipcMain.handle('open-external', async (_evt, url) => {
  try {
    if (typeof url === 'string' && /^https?:\/\//i.test(url)) {
      await shell.openExternal(url);
      return { ok: true };
    }
    return { ok: false, error: 'invalid-url' };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

/* ---------- Additional IPC stubs ---------- */

// validate-ticker
ipcMain.handle('validate-ticker', async (_evt, ticker) => {
  try {
    const value = String(ticker || '').trim().toUpperCase();
    if (!/^[A-Z]{1,5}$/.test(value)) {
      return { success: false, reason: 'invalid_format', message: '*Invalid ticker format. Use letters only (1–5, e.g., AAPL).' };
    }
    if (!FINNHUB_API_KEY) return { success: false, reason: 'missing_api_key', message: '*Server missing FINNHUB_API_KEY.' };

    const url = `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(value)}&token=${FINNHUB_API_KEY}`;
    const { data } = await http.get(url);
    if (!data || typeof data.c !== 'number') {
      return { success: false, reason: 'not_found', message: '*Ticker not recognized. Check the symbol.' };
    }
    return { success: true, data };
  } catch (error) {
    console.error('[validate-ticker] error:', error.message);
    return { success: false, reason: 'network_error', message: '*Network error. Please try again later.' };
  }
});

// getQuote
ipcMain.handle('getQuote', async (_evt, ticker) => {
  try {
    const value = String(ticker || '').trim().toUpperCase();
    if (!/^[A-Z]{1,5}$/.test(value)) return { success: false, error: 'Invalid ticker format.' };
    if (!FINNHUB_API_KEY) return { success: false, error: 'Missing FINNHUB_API_KEY on server.' };

    const url = `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(value)}&token=${FINNHUB_API_KEY}`;
    const { data } = await http.get(url);
    return { success: true, data };
  } catch (error) {
    console.error('[getQuote] error:', error.message);
    return { success: false, error: error.message };
  }
});

// getNews
ipcMain.handle('getNews', async (_evt, ticker) => {
  try {
    const value = String(ticker || '').trim().toUpperCase();
    if (!/^[A-Z]{1,5}$/.test(value)) return { success: false, error: 'Invalid ticker format.' };
    if (!FINNHUB_API_KEY) return { success: false, error: 'Missing FINNHUB_API_KEY on server.' };

    const today = new Date();
    const to = today.toISOString().slice(0, 10);
    const from = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    const url = `https://finnhub.io/api/v1/company-news?symbol=${encodeURIComponent(value)}&from=${from}&to=${to}&token=${FINNHUB_API_KEY}`;
    const { data } = await http.get(url);

    const top = Array.isArray(data)
      ? data.slice(0, 3).map(n => ({
          datetime: n.datetime, headline: n.headline, source: n.source, url: n.url, id: n.id
        }))
      : [];
    return { success: true, data: top };
  } catch (error) {
    console.error('[getNews] error:', error.message);
    return { success: false, error: error.message };
  }
});
