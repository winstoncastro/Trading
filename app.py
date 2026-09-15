"""Interfaz gráfica para monitorear las 10 principales criptomonedas de
Binance que cumplan dos criterios parametrizables, con consulta periódica."""
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from binance_client import BinanceClient, BinanceClientError
from screener import CONDITIONS, PARAMETERS, QUOTE_ASSET_OPTIONS, filter_tickers

INTERVAL_UNITS = {"Segundos": 1, "Minutos": 60}

COLUMNS = (
    ("rank", "#", 40),
    ("symbol", "Símbolo", 90),
    ("price", "Precio", 100),
    ("change", "Cambio 24h (%)", 110),
    ("volume", "Volumen 24h", 130),
    ("trades", "Operaciones", 90),
    ("range", "Rango % 24h", 90),
)


class CriterioFrame(ttk.LabelFrame):
    def __init__(self, master, titulo, param_default, cond_default, umbral_default):
        super().__init__(master, text=titulo, padding=10)

        ttk.Label(self, text="Parámetro:").grid(row=0, column=0, sticky="w", pady=2)
        self.param_var = tk.StringVar(value=param_default)
        param_combo = ttk.Combobox(
            self, textvariable=self.param_var, values=list(PARAMETERS.keys()),
            state="readonly", width=30,
        )
        param_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self, text="Condición:").grid(row=1, column=0, sticky="w", pady=2)
        self.cond_var = tk.StringVar(value=cond_default)
        cond_combo = ttk.Combobox(
            self, textvariable=self.cond_var, values=list(CONDITIONS.keys()),
            state="readonly", width=30,
        )
        cond_combo.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self, text="Umbral:").grid(row=2, column=0, sticky="w", pady=2)
        self.umbral_var = tk.StringVar(value=umbral_default)
        ttk.Entry(self, textvariable=self.umbral_var, width=33).grid(
            row=2, column=1, padx=5, pady=2
        )

    def get_criterio(self):
        umbral_text = self.umbral_var.get().strip().replace(",", ".")
        umbral = float(umbral_text)
        return self.param_var.get(), self.cond_var.get(), umbral


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Screener de Criptomonedas - Binance")
        self.geometry("820x560")
        self.minsize(760, 520)

        self.client = BinanceClient()
        self.result_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.running = False

        self._build_ui()
        self.after(150, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        criterios_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        criterios_frame.pack(fill="x")

        self.criterio1 = CriterioFrame(
            criterios_frame, "Criterio 1", "Cambio 24h (%)", "mayor que (>)", "5"
        )
        self.criterio1.pack(side="left", expand=True, fill="both", padx=(0, 5))

        self.criterio2 = CriterioFrame(
            criterios_frame, "Criterio 2", "Volumen 24h (en USDT/cotización)",
            "mayor que (>)", "10000000",
        )
        self.criterio2.pack(side="left", expand=True, fill="both", padx=(5, 0))

        opciones_frame = ttk.LabelFrame(self, text="Opciones de resultado", padding=10)
        opciones_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(opciones_frame, text="Activo de cotización:").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.quote_var = tk.StringVar(value="USDT")
        ttk.Combobox(
            opciones_frame, textvariable=self.quote_var, values=QUOTE_ASSET_OPTIONS,
            state="readonly", width=10,
        ).grid(row=0, column=1, padx=5)

        ttk.Label(opciones_frame, text="Ordenar por:").grid(
            row=0, column=2, sticky="w", padx=(20, 5)
        )
        self.sort_var = tk.StringVar(value="Volumen 24h (en USDT/cotización)")
        ttk.Combobox(
            opciones_frame, textvariable=self.sort_var, values=list(PARAMETERS.keys()),
            state="readonly", width=30,
        ).grid(row=0, column=3, padx=5)

        self.desc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opciones_frame, text="Descendente", variable=self.desc_var
        ).grid(row=0, column=4, padx=(20, 0))

        freq_frame = ttk.LabelFrame(self, text="Frecuencia de consulta", padding=10)
        freq_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(freq_frame, text="Cada:").grid(row=0, column=0, sticky="w")
        self.interval_var = tk.StringVar(value="60")
        ttk.Entry(freq_frame, textvariable=self.interval_var, width=8).grid(
            row=0, column=1, padx=5
        )
        self.unit_var = tk.StringVar(value="Segundos")
        ttk.Combobox(
            freq_frame, textvariable=self.unit_var, values=list(INTERVAL_UNITS.keys()),
            state="readonly", width=10,
        ).grid(row=0, column=2, padx=5)

        self.start_button = ttk.Button(
            freq_frame, text="Iniciar monitoreo", command=self._start
        )
        self.start_button.grid(row=0, column=3, padx=(20, 5))
        self.stop_button = ttk.Button(
            freq_frame, text="Detener", command=self._stop, state="disabled"
        )
        self.stop_button.grid(row=0, column=4, padx=5)

        self.status_var = tk.StringVar(value="Listo. Configure los criterios y presione Iniciar.")
        ttk.Label(self, textvariable=self.status_var, foreground="#555").pack(
            fill="x", padx=12
        )

        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            tree_frame, columns=[c[0] for c in COLUMNS], show="headings"
        )
        for key, label, width in COLUMNS:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _read_config(self):
        criterio1 = self.criterio1.get_criterio()
        criterio2 = self.criterio2.get_criterio()

        interval_value = float(self.interval_var.get().strip().replace(",", "."))
        if interval_value <= 0:
            raise ValueError("El intervalo debe ser mayor que cero.")
        interval_seconds = interval_value * INTERVAL_UNITS[self.unit_var.get()]

        return {
            "criteria": [criterio1, criterio2],
            "quote_asset": self.quote_var.get(),
            "sort_param": self.sort_var.get(),
            "descending": self.desc_var.get(),
            "interval_seconds": interval_seconds,
        }

    def _start(self):
        if self.running:
            return
        try:
            config = self._read_config()
        except ValueError as exc:
            messagebox.showerror("Datos inválidos", f"Revise los valores ingresados.\n{exc}")
            return

        self.running = True
        self.stop_event.clear()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_var.set("Monitoreo iniciado...")

        self.worker_thread = threading.Thread(
            target=self._worker_loop, args=(config,), daemon=True
        )
        self.worker_thread.start()

    def _stop(self):
        self.stop_event.set()
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Monitoreo detenido.")

    def _worker_loop(self, config):
        while not self.stop_event.is_set():
            try:
                tickers = self.client.get_24h_tickers()
                results = filter_tickers(
                    tickers,
                    quote_asset=config["quote_asset"],
                    criteria=config["criteria"],
                    sort_param=config["sort_param"],
                    descending=config["descending"],
                )
                self.result_queue.put(("ok", results))
            except BinanceClientError as exc:
                self.result_queue.put(("error", str(exc)))
            except Exception as exc:  # noqa: BLE001 - reportar cualquier falla al usuario
                self.result_queue.put(("error", f"Error inesperado: {exc}"))

            self.stop_event.wait(config["interval_seconds"])

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "ok":
                    self._render_results(payload)
                else:
                    self.status_var.set(f"Error: {payload}")
        except queue.Empty:
            pass
        self.after(150, self._poll_queue)

    def _render_results(self, results):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, t in enumerate(results, start=1):
            change = PARAMETERS["Cambio 24h (%)"](t)
            volume = PARAMETERS["Volumen 24h (en USDT/cotización)"](t)
            range_pct = PARAMETERS["Rango máx-mín 24h (%)"](t)
            self.tree.insert(
                "", "end",
                values=(
                    i,
                    t["symbol"],
                    f"{float(t['lastPrice']):.6g}",
                    f"{change:.2f}",
                    f"{volume:,.0f}",
                    t["count"],
                    f"{range_pct:.2f}",
                ),
            )

        hora = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(
            f"Última actualización: {hora} — {len(results)} criptomoneda(s) encontrada(s)."
        )

    def _on_close(self):
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
