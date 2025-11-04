// renderer.js — HUD (Windows copy) with HEADLINE-as-link + word-boundary clamp

// ---------- helpers ----------
function $(id) { return document.getElementById(id); }
function signClass(n) { if (n > 0) return "pos"; if (n < 0) return "neg"; return "neu"; }
function escapeHtml(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function fmtPct(x, dp=2) { return `${(x*100).toFixed(dp)}%`; }

// Remove "<CLASS>:" prefix & "Conf XX%" then tidy spacing
function stripClassAndConf(text, klass){
  if (!text) return "—";
  let t = String(text);
  if (klass) {
    const rePrefix = new RegExp("^\\s*" + klass.replace(/[-/\\^$*+?.()|[\\]{}]/g,"\\$&") + "\\s*:\\s*", "i");
    t = t.replace(rePrefix, "");
  }
  t = t.replace(/\bConf\s+\d{1,3}%\.?/i, "");
  t = t.replace(/\s{2,}/g, " ").replace(/\s+([.,;:!?])/g, "$1").trim();
  return t || "—";
}
function capitalizeFirstWord(s){
  if (!s) return s;
  const i = s.search(/[A-Za-z]/);
  if (i < 0) return s;
  return s.slice(0, i) + s.charAt(i).toUpperCase() + s.slice(i + 1);
}

// Clamp span/anchor text at a word boundary to fit `maxPx`
function truncateAtWord(el, fullText, maxPx){
  el.textContent = fullText;
  if (el.scrollWidth <= maxPx) return;

  let lo = 0, hi = fullText.length, best = "…";
  while (lo < hi){
    const mid = (lo + hi) >> 1;
    const slice = fullText.slice(0, mid);
    const cut   = slice.lastIndexOf(" ");
    const cand  = (cut > 0 ? slice.slice(0, cut) : slice).trimEnd() + "…";
    el.textContent = cand;
    if (el.scrollWidth <= maxPx){ best = cand; lo = mid + 1; }
    else { hi = mid; }
  }
  el.textContent = best;
}

// Re-clamp only the HEADLINE (now the link itself) based on available width
function clampHeadline(){
  const line = el.one;
  if (!line) return;

  const prefix   = line.querySelector(".one-prefix");
  const headline = line.querySelector(".one-headline"); // <a> if link, <span> if no link
  if (!headline) return;

  const boxW  = line.clientWidth || 0;
  const prefW = prefix ? prefix.getBoundingClientRect().width : 0;
  const gap   = 0;  // no separate link anymore

  const maxPx = Math.max(0, Math.floor(boxW - prefW - gap));
  if (maxPx <= 0) return;

  const full = headline.getAttribute("data-full") || headline.textContent || "";
  truncateAtWord(headline, full, maxPx);
}

// ---------- DOM refs ----------
const el = {
  ticker: $("ticker"),
  last: $("last"),
  ba: $("ba"),
  m1: $("m1"),
  m5: $("m5"),
  sma: $("sma"),
  sent: $("sent"),
  sigma: $("sigma"),
  strat: $("strat"),
  bar: $("bar"),
  conf: $("conf"),
  one: $("one"),
  cache: $("cache"),
  hudInfo: $("hud-info"),
  validationPrompt: $("validationPrompt"),
};

// ---------- config ----------
const GATEWAY_URL = "http://127.0.0.1:8015";
let currentTicker = null;
let isFetching = false;

// ---------- validation ----------
function formatAndValidateTicker(raw){
  const t = (raw || "").trim().toUpperCase();
  if (!t) return { ok:false, msg:"Please enter a ticker" };
  if (!/^[A-Z]{1,5}$/.test(t)) return { ok:false, msg:"*Invalid ticker format. Use letters only (1-5 characters, e.g., AAPL)." };
  return { ok:true, ticker:t };
}
function showValidationMessage(message, isError = true){
  el.validationPrompt.textContent = message;
  el.validationPrompt.classList.remove("neutral");
  el.validationPrompt.style.color = isError ? "#FF5F57" : "#AAA";
  el.validationPrompt.classList.remove("hidden");
}
function clearValidationMessage(){
  el.validationPrompt.textContent = "";
  el.validationPrompt.classList.remove("neutral");
  el.validationPrompt.classList.add("hidden");
}

// ---------- networking ----------
async function fetchRun(ticker){
  const res = await fetch(`${GATEWAY_URL}/api/run?ticker=${encodeURIComponent(ticker)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ---------- HUD helpers ----------
function clearHud(){
  [["last","—"],["ba","B/A"],["m1","—"],["m5","—"],["sma","SMA20"],
   ["sent","—"],["sigma","σ—"],["strat","NA"],["conf","—"],["one","Loading…"],["cache","⟳—s"]]
    .forEach(([k,v])=>{ if(el[k]) el[k].textContent=v; });
  if(el.bar) el.bar.style.width="0px";
  el.hudInfo.classList.remove("active");
  el.hudInfo.classList.add("hidden");
}

function render(payload){
  const f    = payload?.features || {};
  const rec  = payload?.recommendation || {};
  const line = payload?.one_liner?.text || "—";
  const head = payload?.top_headline;
  const q    = payload?.quote || null;
  const age  = payload?.cache_age_seconds;

  // Last / B&A
  if (q && typeof q.last === "number" && isFinite(q.last) && q.last > 0) el.last.textContent = q.last.toFixed(2);
  else el.last.textContent = "—";
  if (q && q.bid!=null && q.ask!=null && isFinite(q.bid) && isFinite(q.ask) && q.ask>q.bid)
    el.ba.textContent = `${Number(q.bid).toFixed(2)}/${Number(q.ask).toFixed(2)}`;
  else el.ba.textContent = "B/A";

  // Returns
  const r1 = (typeof f.r_1m === "number") ? f.r_1m : null;
  const r5 = (typeof f.r_5m === "number") ? f.r_5m : null;
  el.m1.textContent = r1 == null ? "—" : `1m ${(r1 >= 0 ? "+" : "")}${fmtPct(r1)}`;
  el.m1.className   = `sec num ${signClass(r1 ?? 0)}`;
  el.m5.textContent = r5 == null ? "—" : `5m ${(r5 >= 0 ? "+" : "")}${fmtPct(r5)}`;
  el.m5.className   = `sec num ${signClass(r5 ?? 0)}`;

  // SMA20
  const above = !!f.above_sma20;
  el.sma.textContent = above ? "↑" : "↓";
  el.sma.className   = `sec muted ${above ? "pos" : "neg"}`;

  // Sentiment
  const sMean = (typeof f.sent_mean === "number") ? f.sent_mean : null;
  const sStd  = (typeof f.sent_std  === "number") ? f.sent_std  : null;
  el.sent.textContent  = sMean==null ? "—" : `${sMean>=0?"+":""}${sMean.toFixed(2)}`;
  el.sent.className    = sMean==null ? "val neu" : `val ${signClass(sMean)}`;
  el.sigma.textContent = sStd==null ? "σ—" : `σ${sStd.toFixed(2)}`;

  // Strategy badge + confidence
  const klass   = rec.class || "NA";
  const confPct = Math.round(((rec.confidence ?? 0) * 100));
  el.strat.textContent = klass;
  el.bar.style.width   = `${Math.max(0, Math.min(100, confPct)) * 0.8}px`;
  el.conf.textContent  = Number.isFinite(confPct) ? `${confPct}%` : "—";

  // ----- One-liner pieces -----
  // Clean/Capitalise base sentence
  let cleaned = stripClassAndConf(line, klass);
  cleaned = capitalizeFirstWord(cleaned);

  // Prefix text (up to "Source:") + Publisher
  let prefixText = cleaned;
  if (cleaned.toLowerCase().includes("source:")) {
    prefixText = cleaned.split(/source:/i)[0].trim();
  }
  const publisher = (head?.publisher || "").trim();
  const headlineTitle = (head?.title || "").trim();
  const prefixHtml =
    escapeHtml(prefixText ? `${prefixText}. ` : "") +
    (publisher ? `Source: ${escapeHtml(publisher)} — ` : "Source: ");

  // Build: prefix (plain) + headline (link or span)
  if (head?.url) {
    el.one.innerHTML =
      `<span class="one-prefix">${prefixHtml}</span>` +
      `<a href="#" data-external="${escapeHtml(head.url)}" class="one-headline src-link" data-full="${escapeHtml(headlineTitle)}">${escapeHtml(headlineTitle)}</a>`;
  } else {
    el.one.innerHTML =
      `<span class="one-prefix">${prefixHtml}</span>` +
      `<span class="one-headline" data-full="${escapeHtml(headlineTitle)}">${escapeHtml(headlineTitle || cleaned)}</span>`;
  }

  // Click-through for the HEADLINE (link)
  if (!el.one._wired) {
    el.one.addEventListener("click", (ev) => {
      const a = ev.target.closest('a[data-external]');
      if (!a) return;
      ev.preventDefault();
      const href = a.getAttribute("data-external");
      if (href) window.electronAPI?.openExternal(href);
    });
    el.one._wired = true;
  }

  // Cache age
  el.cache.textContent = (typeof age === "number" && age >= 0) ? `⟳${age}s` : "⟳—s";

  // Show HUD row then clamp HEADLINE only
  el.hudInfo.classList.remove("hidden");
  el.hudInfo.classList.add("active");
  requestAnimationFrame(clampHeadline);
}

// ---------- main handler ----------
async function handleEnter(){
  const v = formatAndValidateTicker(el.ticker.textContent);

  if (!v.ok) {
    showValidationMessage(v.msg, true);
    el.ticker.classList.add("invalid");
    clearHud();
    currentTicker = null;
    return;
  }

  clearValidationMessage();
  el.ticker.classList.remove("invalid");

  if (isFetching) return;
  if (currentTicker === v.ticker) return;
  currentTicker = v.ticker;

  try {
    isFetching = true;
    const payload = await fetchRun(currentTicker);
    render(payload);
  } catch (err) {
    console.error(err);
    showValidationMessage("*Unable to fetch data. Is the gateway running on 8015?", true);
    clearHud();
    currentTicker = null;
  } finally {
    isFetching = false;
  }
}

// ---------- boot ----------
document.addEventListener("DOMContentLoaded", () => {
  el.validationPrompt.textContent = "Welcome to MIDAS! Enter a ticker symbol to begin.";
  el.validationPrompt.classList.add("neutral");

  el.ticker.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") { ev.preventDefault(); handleEnter(); }
  });

  // Re-clamp headline when window width changes
  window.addEventListener("resize", () => requestAnimationFrame(clampHeadline));
});

// ---------- Tooltip hover handler (3-second delay) ----------
const tooltip = $("tooltip");
let tooltipTimer = null;

document.body.addEventListener("mouseover", (ev) => {
  const target = ev.target.closest("[data-tooltip]");
  if (!target) return;
  const text = target.getAttribute("data-tooltip");
  if (!text) return;

  // Start a timer — show tooltip only after 3 seconds of hover
  tooltipTimer = setTimeout(() => {
    tooltip.innerHTML = text;
    tooltip.style.opacity = "1";
    tooltip.style.transform = "translateY(0)";
  }, 2000);
});

document.body.addEventListener("mousemove", (ev) => {
  const hudRect = document.getElementById("hud").getBoundingClientRect();
  tooltip.style.left = (ev.pageX - hudRect.left + 12) + "px";
  tooltip.style.top = (ev.pageY - hudRect.top + 12) + "px";
});

document.body.addEventListener("mouseout", () => {
  // cancel pending tooltip or hide existing one
  clearTimeout(tooltipTimer);
  tooltip.style.opacity = "0";
  tooltip.style.transform = "translateY(4px)";
});
