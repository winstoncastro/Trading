"""Definición de parámetros/condiciones evaluables y lógica de filtrado."""
import operator

LEVERAGED_MARKERS = ("UP", "DOWN", "BULL", "BEAR")


def _range_percent(t):
    low = float(t["lowPrice"])
    high = float(t["highPrice"])
    if low <= 0:
        return 0.0
    return (high - low) / low * 100


PARAMETERS = {
    "Cambio 24h (%)": lambda t: float(t["priceChangePercent"]),
    "Variación absoluta 24h": lambda t: float(t["priceChange"]),
    "Precio actual": lambda t: float(t["lastPrice"]),
    "Volumen 24h (en USDT/cotización)": lambda t: float(t["quoteVolume"]),
    "Volumen 24h (en unidades)": lambda t: float(t["volume"]),
    "N° de operaciones 24h": lambda t: float(t["count"]),
    "Máximo 24h": lambda t: float(t["highPrice"]),
    "Mínimo 24h": lambda t: float(t["lowPrice"]),
    "Rango máx-mín 24h (%)": _range_percent,
}

CONDITIONS = {
    "mayor que (>)": operator.gt,
    "mayor o igual (>=)": operator.ge,
    "menor que (<)": operator.lt,
    "menor o igual (<=)": operator.le,
}

QUOTE_ASSET_OPTIONS = ["USDT", "BUSD", "BTC", "ETH", "Todos"]


def _is_leveraged(symbol):
    return any(marker in symbol for marker in LEVERAGED_MARKERS)


def filter_tickers(tickers, quote_asset, criteria, sort_param, descending=True, top_n=10):
    """Filtra `tickers` por dos criterios (parámetro, condición, umbral) y
    devuelve los `top_n` que cumplen ambos, ordenados por `sort_param`.

    `criteria` es una lista de tuplas (nombre_parametro, nombre_condicion, umbral).
    """
    candidates = []
    for t in tickers:
        symbol = t.get("symbol", "")
        if quote_asset != "Todos" and not symbol.endswith(quote_asset):
            continue
        if _is_leveraged(symbol):
            continue

        try:
            ok = True
            for param_name, cond_name, threshold in criteria:
                value = PARAMETERS[param_name](t)
                if not CONDITIONS[cond_name](value, threshold):
                    ok = False
                    break
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            continue

        if ok:
            candidates.append(t)

    sort_fn = PARAMETERS[sort_param]
    candidates.sort(key=sort_fn, reverse=descending)
    return candidates[:top_n]
