"use strict";

const EXCHANGES = {
  "Binance": {
    urls: [
      "https://data-api.binance.vision/api/v3/ticker/24hr",
      "https://api.binance.com/api/v3/ticker/24hr",
    ],
  },
  "Binance.US": {
    urls: ["https://api.binance.us/api/v3/ticker/24hr"],
  },
};

const LEVERAGED_MARKERS = ["UP", "DOWN", "BULL", "BEAR"];

const PARAMETERS = {
  "Cambio 24h (%)": (t) => Number(t.priceChangePercent),
  "Variación absoluta 24h": (t) => Number(t.priceChange),
  "Precio actual": (t) => Number(t.lastPrice),
  "Volumen 24h (en USDT/cotización)": (t) => Number(t.quoteVolume),
  "Volumen 24h (en unidades)": (t) => Number(t.volume),
  "N° de operaciones 24h": (t) => Number(t.count),
  "Máximo 24h": (t) => Number(t.highPrice),
  "Mínimo 24h": (t) => Number(t.lowPrice),
  "Rango máx-mín 24h (%)": (t) => {
    const low = Number(t.lowPrice);
    const high = Number(t.highPrice);
    if (!(low > 0)) return 0;
    return ((high - low) / low) * 100;
  },
};

const CONDITIONS = {
  "mayor que (>)": (a, b) => a > b,
  "mayor o igual (>=)": (a, b) => a >= b,
  "menor que (<)": (a, b) => a < b,
  "menor o igual (<=)": (a, b) => a <= b,
};

const QUOTE_ASSET_OPTIONS = ["USDT", "BUSD", "BTC", "ETH", "Todos"];
const MIN_INTERVAL_SECONDS = 5;
const FETCH_TIMEOUT_MS = 10000;

const el = (id) => document.getElementById(id);

function fillSelect(select, options, selected) {
  select.innerHTML = "";
  for (const opt of options) {
    const o = document.createElement("option");
    o.value = opt;
    o.textContent = opt;
    if (opt === selected) o.selected = true;
    select.appendChild(o);
  }
}

function isLeveraged(symbol) {
  return LEVERAGED_MARKERS.some((m) => symbol.includes(m));
}

function filterTickers(tickers, quoteAsset, criteria, sortParam, descending) {
  const candidates = [];
  for (const t of tickers) {
    const symbol = t.symbol || "";
    if (quoteAsset !== "Todos" && !symbol.endsWith(quoteAsset)) continue;
    if (isLeveraged(symbol)) continue;

    let ok = true;
    for (const { param, cond, threshold } of criteria) {
      const value = PARAMETERS[param](t);
      if (!Number.isFinite(value) || !CONDITIONS[cond](value, threshold)) {
        ok = false;
        break;
      }
    }
    if (ok) candidates.push(t);
  }

  const sortFn = PARAMETERS[sortParam];
  candidates.sort((a, b) => (descending ? sortFn(b) - sortFn(a) : sortFn(a) - sortFn(b)));
  return candidates.slice(0, 10);
}

async function fetchTickers(exchangeName) {
  const { urls } = EXCHANGES[exchangeName];
  let lastError;
  for (const url of urls) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const resp = await fetch(url, { signal: controller.signal });
      clearTimeout(timer);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      clearTimeout(timer);
      lastError = err;
    }
  }
  throw new Error(
    `No se pudo consultar ${exchangeName} (${lastError ? lastError.message : "error desconocido"}). ` +
      "Verifique su conexión a internet; si el problema persiste, el exchange podría estar bloqueado " +
      "desde su país/red o un bloqueador de contenido podría estar interceptando la solicitud."
  );
}

let timerHandle = null;
let running = false;

function readConfig() {
  const criteria = [
    {
      param: el("param1").value,
      cond: el("cond1").value,
      threshold: parseFloat(el("umbral1").value.replace(",", ".")),
    },
    {
      param: el("param2").value,
      cond: el("cond2").value,
      threshold: parseFloat(el("umbral2").value.replace(",", ".")),
    },
  ];
  for (const c of criteria) {
    if (Number.isNaN(c.threshold)) throw new Error("Los umbrales deben ser numéricos.");
  }

  const intervalValue = parseFloat(el("intervalValue").value.replace(",", "."));
  if (!(intervalValue > 0)) throw new Error("El intervalo debe ser mayor que cero.");
  const unit = Number(el("intervalUnit").value);
  const intervalSeconds = intervalValue * unit;
  if (intervalSeconds < MIN_INTERVAL_SECONDS) {
    throw new Error(`El intervalo mínimo permitido es ${MIN_INTERVAL_SECONDS} segundos.`);
  }

  return {
    exchange: el("exchange").value,
    quoteAsset: el("quoteAsset").value,
    sortParam: el("sortParam").value,
    descending: el("descending").checked,
    intervalSeconds,
    criteria,
  };
}

function setStatus(message, isError) {
  const status = el("status");
  status.textContent = message;
  status.classList.toggle("error", Boolean(isError));
}

function renderResults(results) {
  const body = el("resultsBody");
  body.innerHTML = "";

  if (results.length === 0) {
    const row = document.createElement("tr");
    row.className = "empty-row";
    row.innerHTML = `<td colspan="7">Ninguna moneda cumple ambos criterios.</td>`;
    body.appendChild(row);
    return;
  }

  results.forEach((t, i) => {
    const change = PARAMETERS["Cambio 24h (%)"](t);
    const volume = PARAMETERS["Volumen 24h (en USDT/cotización)"](t);
    const range = PARAMETERS["Rango máx-mín 24h (%)"](t);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${i + 1}</td>
      <td>${t.symbol}</td>
      <td>${Number(t.lastPrice).toPrecision(6)}</td>
      <td>${change.toFixed(2)}</td>
      <td>${volume.toLocaleString("es", { maximumFractionDigits: 0 })}</td>
      <td>${t.count}</td>
      <td>${range.toFixed(2)}</td>
    `;
    body.appendChild(row);
  });
}

async function tick(config) {
  try {
    const tickers = await fetchTickers(config.exchange);
    const results = filterTickers(
      tickers,
      config.quoteAsset,
      config.criteria,
      config.sortParam,
      config.descending
    );
    renderResults(results);
    const now = new Date().toLocaleTimeString("es");
    setStatus(`Última actualización: ${now} — ${results.length} criptomoneda(s) encontrada(s).`, false);
  } catch (err) {
    setStatus(`Error: ${err.message}`, true);
  }

  if (running) {
    timerHandle = setTimeout(() => tick(config), config.intervalSeconds * 1000);
  }
}

function start() {
  if (running) return;
  let config;
  try {
    config = readConfig();
  } catch (err) {
    setStatus(err.message, true);
    return;
  }

  running = true;
  el("startBtn").disabled = true;
  el("stopBtn").disabled = false;
  setStatus("Monitoreo iniciado...", false);
  tick(config);
}

function stop() {
  running = false;
  if (timerHandle) {
    clearTimeout(timerHandle);
    timerHandle = null;
  }
  el("startBtn").disabled = false;
  el("stopBtn").disabled = true;
  setStatus("Monitoreo detenido.", false);
}

function init() {
  fillSelect(el("param1"), Object.keys(PARAMETERS), "Cambio 24h (%)");
  fillSelect(el("cond1"), Object.keys(CONDITIONS), "mayor que (>)");
  fillSelect(el("param2"), Object.keys(PARAMETERS), "Volumen 24h (en USDT/cotización)");
  fillSelect(el("cond2"), Object.keys(CONDITIONS), "mayor que (>)");
  fillSelect(el("exchange"), Object.keys(EXCHANGES), "Binance");
  fillSelect(el("quoteAsset"), QUOTE_ASSET_OPTIONS, "USDT");
  fillSelect(el("sortParam"), Object.keys(PARAMETERS), "Volumen 24h (en USDT/cotización)");

  el("startBtn").addEventListener("click", start);
  el("stopBtn").addEventListener("click", stop);
}

init();
