# Trading

Este es un agente que consulta en los Exchanges las criptomonedas potenciales
para invertir, tomando como base los parámetros de búsqueda y los umbrales
que se le van a definir.

## Screener de criptomonedas (Binance)

Aplicación de escritorio con interfaz gráfica (Tkinter) que consulta el
Exchange de Binance y muestra las 10 principales criptomonedas que cumplen
dos criterios definidos por el usuario.

### Características

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
  (en segundos o minutos) se vuelve a consultar el exchange, con botones
  para iniciar y detener el monitoreo sin bloquear la interfaz.

### Requisitos

```bash
pip install -r requirements.txt
```

Requiere Python 3.8+ con Tkinter disponible (incluido por defecto en la
mayoría de las distribuciones de Python de escritorio; en Linux puede
requerir el paquete `python3-tk`).

### Ejecución

```bash
python3 app.py
```

### Estructura

- `app.py`: interfaz gráfica y planificación de las consultas periódicas.
- `binance_client.py`: cliente HTTP mínimo contra la API pública de Binance.
- `screener.py`: definición de parámetros/condiciones evaluables y lógica
  de filtrado y ranking.
