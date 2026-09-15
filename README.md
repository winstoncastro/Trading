# Trading

Este es un agente que consulta en los Exchanges las criptomonedas potenciales
para invertir, tomando como base los parámetros de búsqueda y los umbrales
que se le van a definir.

## Screener de criptomonedas

Dos implementaciones equivalentes que consultan las APIs públicas de
Binance y muestran las 10 principales criptomonedas que cumplen dos
criterios definidos por el usuario, con consulta periódica configurable:

- **`web/`**: aplicación web (HTML/CSS/JS puro, sin backend ni build)
  pensada para ejecutarse desde el navegador.
- **`app.py`**: aplicación de escritorio con interfaz gráfica (Tkinter).

### Características (ambas versiones)

- **Dos criterios parametrizables**: para cada uno se elige el parámetro de
  mercado (cambio % 24h, volumen 24h, precio, N° de operaciones, rango
  máx-mín 24h, etc.), la condición a evaluar (mayor que, mayor o igual,
  menor que, menor o igual) y el umbral numérico. Ambos criterios deben
  cumplirse (AND).
- **Orden y activo de cotización configurables**: se puede elegir contra qué
  activo de cotización filtrar (USDT, BUSD, BTC, ETH o todos) y por qué
  parámetro ordenar el resultado (ascendente/descendente) para quedarse con
  el top 10.
- **Frecuencia de consulta configurable**: se define cada cuánto tiempo
  (en segundos o minutos, mínimo 5 segundos) se vuelve a consultar el
  exchange, con botones para iniciar y detener el monitoreo.

### Versión web (`web/`)

No requiere instalación ni servidor: es HTML/CSS/JS estático que consulta
directamente desde el navegador las APIs públicas de mercado (sin API key).

- **Exchange**: selector con `Binance` (usa `data-api.binance.vision`, el
  mirror público de solo lectura pensado para apps web, con reintento
  automático contra `api.binance.com`) y `Binance.US` como alternativa para
  el caso de que Binance global esté bloqueado en tu país/red.
- **Ejecutar localmente**: abrir `web/index.html` directamente en el
  navegador, o servirlo con cualquier servidor estático, por ejemplo:
  ```bash
  cd web && python3 -m http.server 8000
  ```
  y luego visitar `http://localhost:8000`.
- **Publicar en la web**: al ser archivos estáticos, se puede alojar tal
  cual en GitHub Pages, Netlify, Vercel o cualquier hosting estático, sin
  configuración adicional.
- Si el estado muestra un error de conexión, puede deberse a que la red
  desde la que se accede bloquea el exchange, o a un bloqueador de
  contenido/extensión del navegador interceptando la solicitud; probar con
  el otro exchange del selector o desde otra red.

### Versión de escritorio (`app.py`)

```bash
pip install -r requirements.txt
python3 app.py
```

Requiere Python 3.8+ con Tkinter disponible (incluido por defecto en la
mayoría de las distribuciones de Python de escritorio; en Linux puede
requerir el paquete `python3-tk`).

### Estructura

- `web/index.html`, `web/styles.css`, `web/app.js`: aplicación web.
- `app.py`: interfaz gráfica de escritorio y planificación de las consultas.
- `binance_client.py`: cliente HTTP mínimo contra la API pública de Binance
  (usado por `app.py`).
- `screener.py`: definición de parámetros/condiciones evaluables y lógica
  de filtrado y ranking (usado por `app.py`; su equivalente en JS vive en
  `web/app.js`).
