"""
Barrido de parametros (grid search) para la estrategia de backtest_googl.

- Descarga los datos UNA sola vez (reutiliza la logica de backtest_googl.py.txt).
- Prueba todas las combinaciones de la rejilla de abajo.
- Ordena por rentabilidad e informa tambien del max drawdown (el trade-off).

USO:
  python tune.py
"""

import itertools
import importlib.util
from importlib.machinery import SourceFileLoader

import pandas as pd

# --- Cargar backtest_googl.py.txt como modulo (la extension .txt no es estandar) ---
RUTA = "backtest_googl.py.txt"
loader = SourceFileLoader("bt", RUTA)
spec = importlib.util.spec_from_loader("bt", loader)
bt = importlib.util.module_from_spec(spec)
loader.exec_module(bt)   # no ejecuta el bloque __main__ (su __name__ es "bt")


def max_drawdown(eq):
    roll_max = eq["equity"].cummax()
    dd = (eq["equity"] / roll_max - 1) * 100
    return dd.min()


# ----------------------------- REJILLA A PROBAR -----------------------------
# Edita estas listas para explorar mas/menos combinaciones.
REJILLA = {
    "RIESGO_PCT":     [0.01, 0.02, 0.03],
    "TRAIL_ATR_MULT": [2.0, 3.0, 4.0],
    "LOOKBACK":       [10, 20, 40],
    "TENDENCIA_SMA":  [100, 200],
}
# ----------------------------------------------------------------------------


def main():
    # 1) Descargar datos una sola vez
    print("Descargando datos de", bt.TICKER, "...")
    df = bt.cargar_datos(bt.TICKER, bt.START, bt.END)

    # Buy & Hold de referencia
    bh_ret = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100

    nombres = list(REJILLA.keys())
    combinaciones = list(itertools.product(*REJILLA.values()))
    print(f"Probando {len(combinaciones)} combinaciones...\n")

    resultados = []
    for combo in combinaciones:
        # Fijar los parametros globales del modulo para esta corrida
        for nombre, valor in zip(nombres, combo):
            setattr(bt, nombre, valor)

        capital_final, eq, tr = bt.backtest(df)
        ret = (capital_final / bt.CAPITAL_INICIAL - 1) * 100
        dd = max_drawdown(eq) if len(eq) else 0.0
        n_trades = len(tr)
        win_rate = (len(tr[tr["pnl"] > 0]) / n_trades * 100) if n_trades else 0.0

        fila = dict(zip(nombres, combo))
        fila.update({
            "ret_%": round(ret, 2),
            "max_dd_%": round(dd, 2),
            "trades": n_trades,
            "win_%": round(win_rate, 0),
        })
        resultados.append(fila)

    tabla = pd.DataFrame(resultados).sort_values("ret_%", ascending=False)

    print("=" * 70)
    print(f"  Buy & Hold {bt.TICKER} mismo periodo: {bh_ret:+.1f}%")
    print("=" * 70)
    print("\n  Top 10 combinaciones por rentabilidad:\n")
    print(tabla.head(10).to_string(index=False))
    print("\n  Peores 3 (para ver el rango):\n")
    print(tabla.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
