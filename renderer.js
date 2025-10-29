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
  ticker: $('ticker'),
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


/**
 * APIs/Ticker Info Fetch/Validation
 */

document.addEventListener('DOMContentLoaded', () => {
  const tickerInput = document.getElementById('ticker');

  /*tickerInput.addEventListener('input', () => {

    // Auto Resize Width based on text length
    function adjustWidth() {
      const textInput = ticker.textContent.trim() || ticker.dataset.placeholder;
      measure.textContent = textInput;

      tickerInput.style.width = `${measure.offsetWidth}px`;
    }

    tickerInput.addEventListener('input', adjustWidth);
    tickerInput.addEventListener('focus', adjustWidth);
    tickerInput.addEventListener('blur', adjustWidth);

    adjustWidth();

    /*const tempWidth = document.createElement('span');
    tempWidth.style.visibility = 'hidden';
    tempWidth.style.position = 'absolute';
    tempWidth.style.whiteSpace = 'pre';
    tempWidth.style.font = window.getComputedStyle(tickerInput).font;
    tempWidth.textContent = tickerInput.textContent;
    document.body.appendChild(tempWidth);

    const newWidth = Math.min(Math.max(tempWidth.offsetWidth + 24, 100), 250);
    tickerInput.style.width = `${newWidth}px`;

    document.body.removeChild(tempWidth); 

    // Display full ticker input on hover
    tickerInput.title = tickerInput.textContent.trim();
  });*/

  const validationPrompt = document.getElementById('validationPrompt');
  const hudInfo = document.getElementById('hud-info');
  // WELCOME PROMPT (first view) - Intializes HUD with user's welcome page 
  validationPrompt.textContent = "Welcome to MIDAS! Enter a ticker symbol to begin.";
  validationPrompt.classList.add('neutral'); // Neutral Theme signifies unentered ticker

  // RESETS & DISPLAYS validation message upon Enter key
  function showValidationMessage(message, isError = true) {
    validationPrompt.textContent = message;
    validationPrompt.classList.remove('neutral'); // Removes neutral theme for invalid input
    validationPrompt.style.color = isError ? '#FF5F57' : '#AAA';
  }

  function clearValidationMessage() {
    validationPrompt.textContent = '';
    validationPrompt.classList.remove('neutral');
  }

  /** -------------------
   * TICKER VALIDATION
   -------------------- */
  async function validateTicker() {
    const rawValue = tickerInput.textContent.trim();
    const ticker = rawValue.toUpperCase();
    tickerInput.textContent = ticker;
    validationPrompt.classList.remove('neutral');

    // VALIDATION PROMPT CASE 1: Empty Input
    if (ticker === '') {
      showValidationMessage('Please enter a ticker');
      tickerInput.classList.add('invalid');
      return false;
    }

    // VALIDATION PROMPT CASE 2: Invalid Format
    if (!/^[A-Z]{1,5}$/.test(ticker)) {
      showValidationMessage('*Invalid ticker format. Use letters only (1-5 characters, e.g., AAPL).');
      tickerInput.classList.add('invalid');
      return false;
    }

    // VALIDATION PROMPT CASE 3: Proper Format - Check to confirm ticker validity

    try {
      const response = await window.electronAPI.validateTicker(ticker);

      if (!response.success) {
        switch (response.reason) {
          case 'not_found':
            showValidationMessage('*Ticker not recognized. Please check the spelling or try a different ticker.');
            break;
          case 'invalid_format':
            showValidationMessage('*Invalid ticker format. Use letters only (1-5 characters, e.g., AAPL');
            break;
          case 'network_error':
            showValidationMessage('*Network error. Please try again later.');
            break;
          default:
            showValidationMessage('*Unable to validate ticker. Please try again later.');
        }

        tickerInput.classList.add('invalid');
        validationPrompt.classList.remove('hidden');
        return false;
      }

    
      // VALID TICKER - Shows Ticker Info/Clears validation prompts/invalid theme
      clearValidationMessage();
      tickerInput.classList.remove('invalid');
      
      // Displays HUD's ticker info when ticker is validated successfully
      if (response.success) {
          const hudInfo = document.getElementById('hud-info');
          hudInfo.classList.add('active'); // Reveals Ticker Info
          validationPrompt.style.color = '#AAA';
          validationPrompt.classList.add('hidden');
        }

      console.log('Valid ticker confirmed: ', ticker);
      return true;

    } catch (error) {
      showValidationMessage('*Unexpected error validating ticker.');
      console.error(error);
      return false;
    }
  }

  // Handles Enter key to search for ticker info
  tickerInput.addEventListener('input', adjustTickerWidth);
  tickerInput.addEventListener('keydown', async (event) => {
    if (event.key === 'Enter') {
      event.preventDefault(); // Prevents creation of newline
      adjustTickerWidth(); // Recalculates width before validation
      await validateTicker();

      // Hide HUD info immediately when new ticker is being validated
      hudInfo.classList.remove('active');
      hudInfo.classList.add('hidden');
      validationPrompt.classList.remove('hidden');

      // Clear existing HUD values before validating
      [
      '#last',
      '#m1',
      '#m5',
      '#sent',
      '#sigma',
      '#strat',
      '#conf',
      '#one',
      '#cache'
      ].forEach(id => {
        const el = document.querySelector(id);
        if (el) el.textContent = '-';
      });

      // Reruns ticker validation
      const isValid = await validateTicker();

      // HUD info displayed once validation succeeds
      if (isValid) {
        hudInfo.classList.remove('hidden');
        hudInfo.classList.add('active');
        validationPrompt.classList.add('hidden');
      }
    }
  });

  // Hook up IPC Stream
  if (window.mainWindow && typeof update === 'function') {
    window.mainWindow.onUpdate(update);
  }

  // Responsive Width of ticker input, adjusts width as user populates input
  function adjustTickerWidth() {
    const tickerText = tickerInput.textContent.trim();

    // If empty → reset to default placeholder width
    if (!tickerText) {
      tickerInput.style.width = '90px';
      return;
    }

    // Measure text width
    const tickerSpan = document.createElement('span');
    tickerSpan.style.visibility = 'hidden';
    tickerSpan.style.position = 'absolute';
    tickerSpan.style.font = window.getComputedStyle(tickerInput).font;
    tickerSpan.textContent = tickerText;
    document.body.appendChild(tickerSpan);
    const textWidth = tickerSpan.offsetWidth;
    document.body.removeChild(tickerSpan);

    // Adjust within your limits
    const minWidth = 20;
    const maxWidth = 150;
    const newWidth = Math.min(Math.max(textWidth + 20, minWidth), maxWidth);
    tickerInput.style.width = `${newWidth}px`;
}
  
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



/** ---------------------------------
 *  RENDER/UPDATE TICKER INFORMATION
 -----------------------------------*/

function update(payload) {  // Updates Ticker Information
  const { symbol, quote, sentiment, strategy, one_liner, cache_age_seconds } = payload;

  // Sets visible ticker symbol
  el.sym.textContent = symbol;
  
  // Displays last traded price
  el.last.textContent = quote.last.toFixed(2);
  el.last.className = `sec num ${signClass(quote.ret_1m_pct)}`; // signClass -> Pos/neg return style (green or red)

  // Displays Bid/Ask
  el.ba.textContent = `${quote.bid.toFixed(2)}/${quote.ask.toFixed(2)}`;  

  // Displays Returns/Trends
  el.m1.textContent = `1m ${(quote.ret_1m_pct >= 0 ? '+' : '')}${quote.ret_1m_pct.toFixed(2)}%`; 
  el.m1.className = `sec num ${signClass(quote.ret_1m_pct)}`; // 1 min return w/ sign

  el.m5.textContent = `5m ${(quote.ret_5m_pct >= 0 ? '+' : '')}${quote.ret_5m_pct.toFixed(2)}%`; 
  el.m5.className = `sec num ${signClass(quote.ret_5m_pct)}`; // 5 min return w/ sign

  // SMA Arrow indicates trend direction
  const arrow = quote.sma20_distance_pct >= 0 ? '↑' : '↓';
  el.sma.textContent = `${arrow}${Math.abs(quote.sma20_distance_pct).toFixed(2)}%`; 
  el.sma.className = `sec num ${signClass(quote.sma20_distance_pct)}`;
  // Computes if current price is above or below 20-period SMA

  // Sentiment Display
  el.sent.textContent = (sentiment.mean >= 0 ? '+' : '') + sentiment.mean.toFixed(2); 
  el.sent.className = `val ${signClass(sentiment.mean)}`; // avg sent. score
  el.sigma.textContent = `σ${sentiment.stdev.toFixed(2)}`;  // sent. standard deviation

  // Strategy Recommender + Confidence Bar
  el.strat.textContent = strategy.code; // NA, IC, CS, PS, CC
  const pct = Math.max(0, Math.min(100, strategy.confidence_pct));
  el.bar.style.width = `${pct * 0.8}px`; // 0, .80px fill
  el.conf.textContent = `${pct}%`;

  // For generated one-liner
  el.one.textContent = one_liner;
  el.one.title = one_liner;

  // Cache Timer - Displays data age in seconds
  el.cache.textContent = `⟳${cache_age_seconds}s`;
} 