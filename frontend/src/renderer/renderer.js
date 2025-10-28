/**
 * renderer.cjs
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


// Performance Indicator with Color by sign (negative - red, positive - green)
function signClass(n) {
  if (n > 0) return 'pos';
  if (n < 0) return 'neg';
  return 'neu';
}

// DOM refs for each item
const $ = (id) => document.getElementById(id);
const el = {
  sym: $('sym'),
  last: $('last'),
  ba: $('ba'),
  m1: $('m1'),
  m5: $('m5'),
  sma: $('sma'),
  sent: $('sent'),
  sigma: $('sigma'),
  strat: $('strat'),
  bar: $('bar'),
  conf: $('conf'),
  one: $('one'),
  cache: $('cache')
};


// Hook up IPC stream
window.hud.onUpdate(update);

// Show version on hover (sanity check)
window.hud.getVersion().then((v) => {
  document.title = `Trade HUD v${v}`;
});

/**
 * TO DO: Invalid ticker input triggers a brief shake animation
 */
const tickerInput = document.getElementById("tickerInput");

function triggerShake() {
  tickerInput.classList.add("shake");
  tickerInput.style.borderBottom = "1px solid red";

  // Remove class after animation so it can replay next time for invalid input
  setTimeout(() => {
    tickerInput.classList.remove("shake");
    tickerInput.style.borderBottom = "1px solid rgba(255,255,255,0.3)";
  }, 400);
};

/**
 * APIs
 */

document.addEventListener('DOMContentLoaded', () => {
  const tickerInput = document.getElementById('ticker');
  const hudOutput = document.getElementById('hud-output');

  tickerInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      const symbol = tickerInput.value.trim().toUpperCase(); // auto capitalizes each character
      hudOutput.textContent = 'Fetching data...';

      // Fetch ticker data
      const tickerResponse = await window.electronAPI.getTickerInfor(symbol);
      if (!tickerResponse.success) {
        hudOutput.textContent = ''; // validation TO DO
        return;
      }

      // Send data for analysis - Hugging Face?


      // Display result in HUD
      
    }
  });
});



/**
 * MOCK DATA - To visualize mock code, remove comment block to implement
 * 
 * function update(payload) {  // updates ticker information
  const { symbol, quote, sentiment, strategy, one_liner, cache_age_seconds } = payload;

  el.sym.textContent = symbol;

  el.last.textContent = quote.last.toFixed(2);  // last collected price
  el.last.className = `sec num ${signClass(quote.ret_1m_pct)}`;

  el.ba.textContent = `${quote.bid.toFixed(2)}/${quote.ask.toFixed(2)}`;  // displays quote of bid

  el.m1.textContent = `1m ${(quote.ret_1m_pct >= 0 ? '+' : '')}${quote.ret_1m_pct.toFixed(2)}%`; // displays 1m short-term return
  el.m1.className = `sec num ${signClass(quote.ret_1m_pct)}`;

  el.m5.textContent = `5m ${(quote.ret_5m_pct >= 0 ? '+' : '')}${quote.ret_5m_pct.toFixed(2)}%`;  // displays 5m short-term return
  el.m5.className = `sec num ${signClass(quote.ret_5m_pct)}`; 

  const arrow = quote.sma20_distance_pct >= 0 ? '↑' : '↓';
  el.sma.textContent = `${arrow}${Math.abs(quote.sma20_distance_pct).toFixed(2)}%`; 
  el.sma.className = `sec num ${signClass(quote.sma20_distance_pct)}`;

  el.sent.textContent = (sentiment.mean >= 0 ? '+' : '') + sentiment.mean.toFixed(2);
  el.sent.className = `val ${signClass(sentiment.mean)}`;
  el.sigma.textContent = `σ${sentiment.stdev.toFixed(2)}`;

  el.strat.textContent = strategy.code; // NA, IC, CS, PS, CC
  const pct = Math.max(0, Math.min(100, strategy.confidence_pct));
  el.bar.style.width = `${pct * 0.8}px`; // 0, .80px fill
  el.conf.textContent = `${pct}%`;

  el.one.textContent = one_liner;
  el.one.title = one_liner;

  el.cache.textContent = `⟳${cache_age_seconds}s`;
}


 */

