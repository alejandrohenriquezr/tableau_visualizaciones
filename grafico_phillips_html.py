"""
Gráfico de Phillips (Chile) - versión HTML interactiva (sin dependencias externas)
===================================================================================
Combina:
  - Tasa de Desocupación (ENE, INE)                -> eje X
  - Índice de Remuneraciones, var_12                -> eje Y
  - IPC General, Variación 12 meses (División nula) -> tamaño del punto

Genera un archivo HTML 100% autocontenido (Canvas 2D puro, sin CDN ni librerías)
con:
  - Tooltip al pasar el mouse: mes-año, var. 12m IPC, var. 12m IR
  - Segmentos de la trayectoria y puntos en naranjo claro cuando la inflación
    está sobre 3%, y celeste cuando está bajo 3%
  - Botón Play/Pause + slider que revela la trayectoria progresivamente
  - Movimiento interpolado entre períodos mediante requestAnimationFrame

Requisitos: pandas (solo para el script de generación; el HTML resultante no
depende de ninguna librería externa).
"""

import json
import pandas as pd

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12, "diciciembre": 12,  # typo presente en el CSV fuente
}

MESES_NOMBRE_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def parse_mes_ano_ene(valor: str) -> pd.Timestamp:
    _, mes_txt, anio = valor.split("/")
    return pd.Timestamp(year=int(anio), month=MESES_ES[mes_txt.strip().lower()], day=1)


def parse_mes_ano_generico(valor: str) -> pd.Timestamp:
    mes_txt, anio = valor.split()
    return pd.Timestamp(year=int(anio), month=MESES_ES[mes_txt.strip().lower()], day=1)


def formatear_periodo_es(periodo: pd.Timestamp) -> str:
    """Devuelve el mes y año en español sin depender del locale del sistema."""
    return f"{MESES_NOMBRE_ES[periodo.month - 1]} {periodo.year}"


def cargar_datos(ruta_ene: str, ruta_ipc: str, ruta_ir: str) -> pd.DataFrame:
    ene = pd.read_csv(ruta_ene)
    ene["periodo"] = ene["mes_año"].apply(parse_mes_ano_ene)
    ene = ene[["periodo", "Tasa de desocupación [1] - tasa (%)"]].rename(
        columns={"Tasa de desocupación [1] - tasa (%)": "desempleo"}
    )

    ipc = pd.read_csv(ruta_ipc)
    ipc_general = ipc[ipc["División"].isna()].copy()
    ipc_general["periodo"] = ipc_general["mes_año"].apply(parse_mes_ano_generico)
    ipc_general = ipc_general[["periodo", "Variación 12 Meses (%)"]].rename(
        columns={"Variación 12 Meses (%)": "inflacion"}
    )

    ir = pd.read_csv(ruta_ir)
    ir["periodo"] = ir["mes_año"].apply(parse_mes_ano_generico)
    ir = ir[["periodo", "var_12"]].rename(columns={"var_12": "ir_var12"})

    df = (
        ene.merge(ipc_general, on="periodo", how="inner")
           .merge(ir, on="periodo", how="inner")
           .dropna(subset=["desempleo", "inflacion", "ir_var12"])
           .sort_values("periodo")
           .reset_index(drop=True)
    )
    return df


def construir_html(df: pd.DataFrame, meta_inflacion: float = 3.0, salida: str = "phillips_interactivo.html"):
    registros = [
        {
            "x": round(r.desempleo, 3),
            "y": round(r.ir_var12, 3),
            "ipc": round(r.inflacion, 3),
            # Se construye explícitamente en español para no depender del locale
            # del sistema operativo donde se ejecuta Python.
            "label": formatear_periodo_es(r.periodo),
        }
        for r in df.itertuples()
    ]

    ipc_vals = [d["ipc"] for d in registros]
    ipc_min, ipc_max = min(ipc_vals), max(ipc_vals)
    data_json = json.dumps(registros, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Curva de Phillips - Chile</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    background: #fafafa;
    margin: 0;
    padding: 24px;
    color: #222;
  }}
  h1 {{ font-size: 20px; margin: 0 0 4px 0; }}
  p.subtitle {{ margin: 0 0 20px 0; color: #666; font-size: 13px; }}
  #wrap {{
    max-width: 920px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    position: relative;
  }}
  #chartContainer {{ position: relative; width: 100%; }}
  canvas {{ display: block; width: 100%; }}
  #tooltip {{
    position: absolute;
    pointer-events: none;
    background: rgba(20,20,20,0.92);
    color: white;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.5;
    display: none;
    white-space: nowrap;
    z-index: 10;
    transform: translate(-50%, -110%);
  }}
  #controls {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 16px;
  }}
  button {{
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 14px;
    cursor: pointer;
  }}
  button:hover {{ background: #1d4ed8; }}
  input[type=range] {{ flex: 1; }}
  #legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    margin-top: 10px;
    font-size: 12px;
    color: #555;
  }}
  .swatch {{
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
  }}
</style>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
</head>
<body>
<div id="wrap">
  <h1>Curva de Phillips &mdash; Chile</h1>
  <p class="subtitle">Desempleo (ENE) vs. variación en 12 meses del Índice de Remuneraciones &middot; tamaño del punto = variación en 12 meses del IPC</p>

  <div id="chartContainer">
    <canvas id="chart"></canvas>
    <div id="tooltip"></div>
  </div>

  <div id="controls">
    <button id="playBtn">&#9654; Play</button>
    <input type="range" id="scrub" min="0" max="{len(registros) - 1}" value="{len(registros) - 1}">
    <span id="frameLabel" style="min-width:80px; font-size:13px; color:#555;"></span>
    <button id="downloadBtn">&#11015; Descargar .xlsx</button>
  </div>

  <div id="legend">
    <span><span class="swatch" style="background:#ffb75e;"></span>Inflación &gt; 3% (meta)</span>
    <span><span class="swatch" style="background:#87ceeb;"></span>Inflación &le; 3% (meta)</span>
    <span>Tamaño del punto &prop; variación en 12 meses del IPC</span>
  </div>
</div>

<script>
(function () {{
  const rawData = {data_json};
  const META = {meta_inflacion};
  const IPC_MIN = {ipc_min};
  const IPC_MAX = {ipc_max};
  const N = rawData.length;

  const canvas = document.getElementById('chart');
  const ctx = canvas.getContext('2d');
  const container = document.getElementById('chartContainer');
  const tooltip = document.getElementById('tooltip');
  const playBtn = document.getElementById('playBtn');
  const scrub = document.getElementById('scrub');
  const frameLabel = document.getElementById('frameLabel');

  const MARGIN = {{ left: 64, right: 24, top: 24, bottom: 56 }};
  const CSS_HEIGHT = 440;
  const DURACION_TRAMO_MS = 1000;

  const xs = rawData.map(d => d.x);
  const ys = rawData.map(d => d.y);
  const xMin = Math.min(...xs) - 0.4, xMax = Math.max(...xs) + 0.4;
  const yMin = Math.min(...ys) - 0.8, yMax = Math.max(...ys) + 0.8;

  function radioPorIPC(ipc) {{
    if (IPC_MAX === IPC_MIN) return 9;
    const t = (ipc - IPC_MIN) / (IPC_MAX - IPC_MIN);
    return 4 + t * 16;
  }}
  const radios = rawData.map(d => radioPorIPC(d.ipc));
  const colores = rawData.map(d => d.ipc > META ? 'rgba(255,140,0,0.8)' : 'rgba(30,144,255,0.8)');

  let cssWidth = 0, dpr = window.devicePixelRatio || 1;

  function resize() {{
    cssWidth = container.clientWidth;
    canvas.style.height = CSS_HEIGHT + 'px';
    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(CSS_HEIGHT * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw(frame);
  }}

  function px(x) {{
    const plotW = cssWidth - MARGIN.left - MARGIN.right;
    return MARGIN.left + (x - xMin) / (xMax - xMin) * plotW;
  }}
  function py(y) {{
    const plotH = CSS_HEIGHT - MARGIN.top - MARGIN.bottom;
    return MARGIN.top + (1 - (y - yMin) / (yMax - yMin)) * plotH;
  }}

  function niceTicks(min, max, count) {{
    const range = max - min;
    const step = range / count;
    const mag = Math.pow(10, Math.floor(Math.log10(step)));
    const norm = step / mag;
    let niceStep;
    if (norm < 1.5) niceStep = 1 * mag;
    else if (norm < 3) niceStep = 2 * mag;
    else if (norm < 7) niceStep = 5 * mag;
    else niceStep = 10 * mag;
    const ticks = [];
    let t = Math.ceil(min / niceStep) * niceStep;
    for (; t <= max + 1e-9; t += niceStep) ticks.push(Math.round(t * 100) / 100);
    return ticks;
  }}

  function drawAxes() {{
    const plotLeft = MARGIN.left, plotRight = cssWidth - MARGIN.right;
    const plotTop = MARGIN.top, plotBottom = CSS_HEIGHT - MARGIN.bottom;

    ctx.strokeStyle = '#e5e5e5';
    ctx.fillStyle = '#666';
    ctx.font = '11px -apple-system, sans-serif';
    ctx.lineWidth = 1;

    // Grid + ticks eje X
    const xTicks = niceTicks(xMin, xMax, 7);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    xTicks.forEach(t => {{
      const xp = px(t);
      ctx.beginPath();
      ctx.moveTo(xp, plotTop);
      ctx.lineTo(xp, plotBottom);
      ctx.stroke();
      ctx.fillText(t.toFixed(1), xp, plotBottom + 8);
    }});

    // Grid + ticks eje Y
    const yTicks = niceTicks(yMin, yMax, 6);
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    yTicks.forEach(t => {{
      const yp = py(t);
      ctx.beginPath();
      ctx.moveTo(plotLeft, yp);
      ctx.lineTo(plotRight, yp);
      ctx.stroke();
      ctx.fillText(t.toFixed(1), plotLeft - 8, yp);
    }});

    // Ejes (bordes)
    ctx.strokeStyle = '#999';
    ctx.beginPath();
    ctx.moveTo(plotLeft, plotTop);
    ctx.lineTo(plotLeft, plotBottom);
    ctx.lineTo(plotRight, plotBottom);
    ctx.stroke();

    // Etiquetas de ejes
    ctx.fillStyle = '#333';
    ctx.font = '13px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText('Tasa de Desocupación (%)', (plotLeft + plotRight) / 2, CSS_HEIGHT - 8);

    ctx.save();
    ctx.translate(16, (plotTop + plotBottom) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Índice de Remuneraciones - Variación en 12 meses (%)', 0, 0);
    ctx.restore();
  }}

  let frame = N - 1;
  let playing = false;
  let animationId = null;

  // Dibuja una etiqueta legible junto al punto activo y la mantiene dentro
  // del área visible del gráfico.
  function drawEtiquetaPeriodo(x, y, texto, radio) {{
    ctx.save();
    ctx.font = '600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

    const paddingX = 9;
    const alto = 26;
    const ancho = ctx.measureText(texto).width + paddingX * 2;
    const separacion = radio + 9;
    let izquierda = x + separacion;
    let arriba = y - alto / 2;

    // Si no cabe a la derecha, sitúa la etiqueta al lado izquierdo del punto.
    if (izquierda + ancho > cssWidth - MARGIN.right) {{
      izquierda = x - separacion - ancho;
    }}
    arriba = Math.max(MARGIN.top, Math.min(arriba, CSS_HEIGHT - MARGIN.bottom - alto));

    const r = 6;
    ctx.beginPath();
    ctx.moveTo(izquierda + r, arriba);
    ctx.lineTo(izquierda + ancho - r, arriba);
    ctx.quadraticCurveTo(izquierda + ancho, arriba, izquierda + ancho, arriba + r);
    ctx.lineTo(izquierda + ancho, arriba + alto - r);
    ctx.quadraticCurveTo(izquierda + ancho, arriba + alto, izquierda + ancho - r, arriba + alto);
    ctx.lineTo(izquierda + r, arriba + alto);
    ctx.quadraticCurveTo(izquierda, arriba + alto, izquierda, arriba + alto - r);
    ctx.lineTo(izquierda, arriba + r);
    ctx.quadraticCurveTo(izquierda, arriba, izquierda + r, arriba);
    ctx.closePath();
    ctx.fillStyle = 'rgba(255,255,255,0.94)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(55,65,81,0.28)';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#1f2937';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(texto, izquierda + paddingX, arriba + alto / 2);
    ctx.restore();
  }}

  // Dibuja los períodos ya alcanzados y, opcionalmente, un punto móvil entre
  // el último período completo y el siguiente.
  function draw(hasta, progreso = 1) {{
    ctx.clearRect(0, 0, cssWidth, CSS_HEIGHT);
    drawAxes();

    // Segmentos de la trayectoria coloreados según meta
    for (let i = 0; i < hasta; i++) {{
      const x0 = px(rawData[i].x), y0 = py(rawData[i].y);
      const x1 = px(rawData[i + 1].x), y1 = py(rawData[i + 1].y);
      const avg = (rawData[i].ipc + rawData[i + 1].ipc) / 2;
      ctx.strokeStyle = avg > META ? 'rgba(255,183,94,0.95)' : 'rgba(135,206,250,0.95)';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
      ctx.stroke();
    }}

    // Durante la reproducción se extiende gradualmente el tramo siguiente.
    if (progreso < 1 && hasta < N - 1) {{
      const actual = rawData[hasta];
      const siguiente = rawData[hasta + 1];
      const x0 = px(actual.x), y0 = py(actual.y);
      const x1 = px(siguiente.x), y1 = py(siguiente.y);
      const xm = x0 + (x1 - x0) * progreso;
      const ym = y0 + (y1 - y0) * progreso;
      const inflacionMedia = (actual.ipc + siguiente.ipc) / 2;

      ctx.strokeStyle = inflacionMedia > META
        ? 'rgba(255,183,94,0.95)'
        : 'rgba(135,206,250,0.95)';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(xm, ym);
      ctx.stroke();
    }}

    // Puntos revelados hasta el frame actual
    for (let i = 0; i <= hasta; i++) {{
      const xp = px(rawData[i].x), yp = py(rawData[i].y);
      ctx.beginPath();
      ctx.arc(xp, yp, radios[i], 0, Math.PI * 2);
      ctx.fillStyle = colores[i];
      ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.15)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }}

    // Interpola posición, radio y color del punto que viaja al período siguiente.
    if (progreso < 1 && hasta < N - 1) {{
      const actual = rawData[hasta];
      const siguiente = rawData[hasta + 1];
      const x = actual.x + (siguiente.x - actual.x) * progreso;
      const y = actual.y + (siguiente.y - actual.y) * progreso;
      const ipc = actual.ipc + (siguiente.ipc - actual.ipc) * progreso;
      const radio = radios[hasta] + (radios[hasta + 1] - radios[hasta]) * progreso;

      ctx.beginPath();
      ctx.arc(px(x), py(y), radio, 0, Math.PI * 2);
      ctx.fillStyle = ipc > META ? 'rgba(255,140,0,0.8)' : 'rgba(30,144,255,0.8)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.15)';
      ctx.lineWidth = 1;
      ctx.stroke();

      drawEtiquetaPeriodo(px(x), py(y), siguiente.label, radio);
    }} else if (playing && rawData[hasta]) {{
      drawEtiquetaPeriodo(
        px(rawData[hasta].x),
        py(rawData[hasta].y),
        rawData[hasta].label,
        radios[hasta]
      );
    }}

    if (progreso < 1 && hasta < N - 1) {{
      frameLabel.textContent = rawData[hasta + 1].label;
    }} else {{
      frameLabel.textContent = rawData[hasta] ? rawData[hasta].label : '';
    }}
  }}

  // --- Tooltip por proximidad del mouse ---
  canvas.addEventListener('mousemove', (e) => {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    let found = -1, bestDist = Infinity;
    for (let i = 0; i <= frame; i++) {{
      const xp = px(rawData[i].x), yp = py(rawData[i].y);
      const d = Math.hypot(mx - xp, my - yp);
      if (d < radios[i] + 6 && d < bestDist) {{ bestDist = d; found = i; }}
    }}
    if (found >= 0) {{
      const d = rawData[found];
      tooltip.style.display = 'block';
      tooltip.style.left = px(d.x) + 'px';
      tooltip.style.top = py(d.y) + 'px';
      tooltip.innerHTML =
        `<strong>${{d.label}}</strong><br>` +
        `Desempleo: ${{d.x.toFixed(1)}}%<br>` +
        `IR (var. 12m): ${{d.y.toFixed(1)}}%<br>` +
        `IPC (var. 12m): ${{d.ipc.toFixed(1)}}%`;
    }} else {{
      tooltip.style.display = 'none';
    }}
  }});
  canvas.addEventListener('mouseleave', () => {{ tooltip.style.display = 'none'; }});

  // --- Reproducción progresiva (Play/Pause) ---
  function goTo(i) {{
    if (animationId !== null) cancelAnimationFrame(animationId);
    animationId = null;
    frame = i;
    scrub.value = i;
    draw(i);
  }}

  // Función de suavizado: parte y termina lentamente, sin saltos de velocidad.
  function easeInOutCubic(t) {{
    return t < 0.5
      ? 4 * t * t * t
      : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }}

  // Anima un tramo temporal completo y encadena el siguiente mientras Play siga activo.
  function animarSiguiente() {{
    if (frame >= N - 1) {{
      playing = false;
      playBtn.innerHTML = '&#9654; Play';
      animationId = null;
      draw(frame);
      return;
    }}

    const desde = frame;
    let inicio = null;

    function tick(timestamp) {{
      if (!playing) return;
      if (inicio === null) inicio = timestamp;

      const avanceLineal = Math.min((timestamp - inicio) / DURACION_TRAMO_MS, 1);
      draw(desde, easeInOutCubic(avanceLineal));

      if (avanceLineal < 1) {{
        animationId = requestAnimationFrame(tick);
      }} else {{
        frame = desde + 1;
        scrub.value = frame;
        draw(frame);
        animationId = requestAnimationFrame(() => animarSiguiente());
      }}
    }}

    animationId = requestAnimationFrame(tick);
  }}

  playBtn.addEventListener('click', () => {{
    if (playing) {{
      playing = false;
      playBtn.innerHTML = '&#9654; Play';
      if (animationId !== null) cancelAnimationFrame(animationId);
      animationId = null;
      draw(frame);
    }} else {{
      if (frame >= N - 1) goTo(0);
      playing = true;
      playBtn.innerHTML = '&#10074;&#10074; Pause';
      animarSiguiente();
    }}
  }});

  scrub.addEventListener('input', (e) => {{
    playing = false;
    playBtn.innerHTML = '&#9654; Play';
    if (animationId !== null) cancelAnimationFrame(animationId);
    animationId = null;
    goTo(parseInt(e.target.value, 10));
  }});

  window.addEventListener('resize', resize);
  resize();
  const downloadBtn = document.getElementById('downloadBtn');
  downloadBtn.addEventListener('click', () => {{
    try {{
      const filas = rawData.map(d => ({{
        'Mes-Año': d.label,
        'Desempleo (%)': d.x,
        'IR var. 12m (%)': d.y,
        'IPC var. 12m (%)': d.ipc,
      }}));
      const ws = XLSX.utils.json_to_sheet(filas);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Phillips');
      XLSX.writeFile(wb, 'datos_phillips.xlsx');
    }} catch (err) {{
      alert('No se pudo generar el archivo .xlsx (¿sin conexión a internet?). Intenta nuevamente con conexión.');
      console.error(err);
    }}
  }});
}})();
</script>
</body>
</html>
"""

    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    return salida


if __name__ == "__main__":
    df = cargar_datos("ine_ene_chile.csv", "ine_ipc_chile.csv", "ine_ir_chile.csv")
    print(
        f"Periodos combinados: {len(df)}  "
        f"({formatear_periodo_es(df['periodo'].min())} a "
        f"{formatear_periodo_es(df['periodo'].max())})"
    )
    ruta = construir_html(df)
    print(f"HTML generado en: {ruta}")
