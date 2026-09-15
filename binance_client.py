"""Cliente mínimo para el endpoint público de mercado de Binance."""
import requests

BASE_URL = "https://api.binance.com"


class BinanceClientError(Exception):
    pass


class BinanceClient:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def get_24h_tickers(self):
        """Devuelve las estadísticas de 24h de todos los símbolos del exchange."""
        try:
            resp = requests.get(
                f"{BASE_URL}/api/v3/ticker/24hr", timeout=self.timeout
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise BinanceClientError(f"Error al consultar Binance: {exc}") from exc
        return resp.json()
