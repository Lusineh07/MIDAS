/**
 * preload.cjs (Windows copy)
 * Bridge from renderer -> Electron main via contextBridge + IPC
 */
const { contextBridge, ipcRenderer } = require("electron");

const GATEWAY = "http://127.0.0.1:8015";

async function hit(url) {
  const res = await fetch(url, { method: "GET", cache: "no-store", headers: { "Accept": "application/json" } });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}
function validTicker(t) { return /^[A-Z]{1,5}$/.test(String(t || "").trim().toUpperCase()); }

contextBridge.exposeInMainWorld("electronAPI", {
  async validateTicker(ticker) {
    const tk = String(ticker || "").trim().toUpperCase();
    if (!validTicker(tk)) return { success: false, reason: "invalid_format" };
    try {
      const data = await hit(`${GATEWAY}/api/run?ticker=${encodeURIComponent(tk)}`);
      if (data && data.features && data.recommendation) return { success: true };
      return { success: false, reason: "not_found" };
    } catch {
      return { success: false, reason: "network_error" };
    }
  },
  async fetchRun(ticker) {
    const tk = String(ticker || "").trim().toUpperCase();
    return hit(`${GATEWAY}/api/run?ticker=${encodeURIComponent(tk)}`);
  },

  // Use IPC -> main to open external links (most robust with sandbox/contextIsolation)
  openExternal(url) {
    if (typeof url === "string" && /^https?:\/\//i.test(url)) {
      ipcRenderer.invoke("open-external", url);
    }
  },
});
