"""
Gráfico de Phillips (Chile) - animado e interactivo
=====================================================
Cruza la Tasa de Desocupación (ENE, INE) con la Variación en 12 meses
del IPC General (División nula = IPC General) para construir un gráfico
de dispersión animado: eje X = desempleo, eje Y = inflación (var. 12 meses),
con un botón "Play/Pause" que hace avanzar un punto en el tiempo dejando
un rastro (trail) de los periodos ya visitados.

Requisitos: pandas, matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button

# ---------------------------------------------------------------------------
# 1. Carga y limpieza de datos
# ---------------------------------------------------------------------------

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12, "diciciembre": 12,  # typo presente en el CSV fuente
}


def parse_mes_ano_ene(valor: str) -> pd.Timestamp:
    """Convierte '01/febrero/2010' -> Timestamp(2010-02-01)."""
    _, mes_txt, anio = valor.split("/")
    mes = MESES_ES[mes_txt.strip().lower()]
    return pd.Timestamp(year=int(anio), month=mes, day=1)


def parse_mes_ano_ipc(valor: str) -> pd.Timestamp:
    """Convierte 'Enero 2024' -> Timestamp(2024-01-01)."""
    mes_txt, anio = valor.split()
    mes = MESES_ES[mes_txt.strip().lower()]
    return pd.Timestamp(year=int(anio), month=mes, day=1)


def cargar_datos(ruta_ene: str, ruta_ipc: str) -> pd.DataFrame:
    ene = pd.read_csv(ruta_ene)
    ipc = pd.read_csv(ruta_ipc)

    ene["periodo"] = ene["mes_año"].apply(parse_mes_ano_ene)
    ene = ene[["periodo", "Tasa de desocupación [1] - tasa (%)"]].rename(
        columns={"Tasa de desocupación [1] - tasa (%)": "desempleo"}
    )

    # Filtrar IPC General: División nula
    ipc_general = ipc[ipc["División"].isna()].copy()
    ipc_general["periodo"] = ipc_general["mes_año"].apply(parse_mes_ano_ipc)
    ipc_general = ipc_general[["periodo", "Variación 12 Meses (%)"]].rename(
        columns={"Variación 12 Meses (%)": "inflacion"}
    )

    df = pd.merge(ene, ipc_general, on="periodo", how="inner").sort_values("periodo")
    df = df.dropna(subset=["desempleo", "inflacion"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 2. Animación interactiva
# ---------------------------------------------------------------------------

def crear_animacion(df: pd.DataFrame, intervalo_ms: int = 500):
    x = df["desempleo"].to_numpy()
    y = df["inflacion"].to_numpy()
    labels = df["periodo"].dt.strftime("%b-%Y").to_numpy()

    fig, ax = plt.subplots(figsize=(9, 6.5))
    plt.subplots_adjust(bottom=0.18)

    ax.set_xlim(x.min() - 0.5, x.max() + 0.5)
    ax.set_ylim(y.min() - 1, y.max() + 1)
    ax.set_xlabel("Tasa de Desocupación (%)")
    ax.set_ylabel("Inflación - Variación 12 meses IPC (%)")
    ax.set_title("Curva de Phillips - Chile")
    ax.grid(alpha=0.5)

    # Rastro (trail) de todos los puntos ya recorridos
    trail_line, = ax.plot([], [], "-", color="tab:blue", alpha=0.5, lw=1.5, zorder=2)
    trail_points, = ax.plot([], [], "o", color="tab:blue", alpha=0.35, ms=5, zorder=2)
    # Punto actual (cabeza de la animación)
    head_point, = ax.plot([], [], "o", color="tab:red", ms=12, zorder=3)
    label_text = ax.text(0.02, 0.96, "", transform=ax.transAxes, fontsize=11,
                          va="top", ha="left",
                          bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    state = {"frame": 0, "playing": False}

    def init():
        trail_line.set_data([], [])
        trail_points.set_data([], [])
        head_point.set_data([], [])
        label_text.set_text("")
        return trail_line, trail_points, head_point, label_text

    def update(frame):
        i = frame
        state["frame"] = i
        # Rastro: todo lo recorrido hasta el punto anterior
        trail_line.set_data(x[: i + 1], y[: i + 1])
        trail_points.set_data(x[:i], y[:i])
        # Punto actual
        head_point.set_data([x[i]], [y[i]])
        label_text.set_text(f"{labels[i]}\nDesempleo: {x[i]:.1f}%\nInflación: {y[i]:.1f}%")

        if i == len(x) - 1:
            state["playing"] = False
            anim.event_source.stop()

        return trail_line, trail_points, head_point, label_text

    anim = FuncAnimation(
        fig, update, frames=len(x), init_func=init,
        interval=intervalo_ms, blit=True, repeat=False,
    )
    anim.event_source.stop()  # arranca detenida, se activa con el botón Play

    # --- Botón Play/Pause ---
    ax_button = plt.axes([0.45, 0.03, 0.12, 0.06])
    button = Button(ax_button, "▶ Play")

    def on_click(event):
        if state["playing"]:
            anim.event_source.stop()
            button.label.set_text("▶ Play")
            state["playing"] = False
        else:
            # Si llegó al final, reinicia
            if state["frame"] >= len(x) - 1:
                state["frame"] = 0
                update(0)
            anim.event_source.start()
            button.label.set_text("⏸ Pause")
            state["playing"] = True
        fig.canvas.draw_idle()

    button.on_clicked(on_click)

    return fig, anim, button


if __name__ == "__main__":
    df = cargar_datos("ine_ene_chile.csv", "ine_ipc_chile.csv")
    print(f"Periodos combinados: {len(df)}  ({df['periodo'].min():%b-%Y} a {df['periodo'].max():%b-%Y})")
    fig, anim, button = crear_animacion(df)
    plt.show()
