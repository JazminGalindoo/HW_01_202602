import argparse
import json
import os
import re
import sys
from datetime import datetime

import pandas as pd
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_USERNAME = "DrNykterstein"
DEFAULT_MAX_GAMES = 50
OUTPUT_DIR = "output"


def fetch_games(username: str, max_games: int) -> list:
    """
    Descarga las partidas de un usuario desde la API publica de Lichess
    en formato PGN (texto), y las parsea a una lista de diccionarios.
    """
    url = f"https://lichess.org/api/games/user/{username}"
    params = {"max": max_games}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"Descargando hasta {max_games} partidas de '{username}'...")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"ERROR: la API respondio con codigo {response.status_code}")
            print(f"URL solicitada: {response.url}")
            print(f"Respuesta del servidor: {response.text[:500]}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR al conectar con la API de Lichess: {e}")
        sys.exit(1)

    raw_text = response.text
    chunks = re.split(r'(?=\[Event )', raw_text)
    games = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        tags = dict(re.findall(r'\[(\w+)\s+"(.*?)"\]', chunk))
        if tags:
            games.append(tags)

    if not games:
        print("No se encontraron partidas para ese usuario (o el usuario no existe).")
        sys.exit(1)

    print(f"Se descargaron {len(games)} partidas.")
    return games


def _parse_elo(value):
    """Convierte el Elo del PGN a numero, o None si no aplica (ej. rival IA con '?')."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def games_to_dataframe(games: list, username: str) -> pd.DataFrame:
    """
    Transforma la lista de partidas (diccionarios de etiquetas PGN) en un
    DataFrame de pandas, calculando el resultado y el color desde la
    perspectiva del usuario.
    """
    username_lower = username.lower()
    rows = []

    for tags in games:
        white_name = tags.get("White", "").lower()
        black_name = tags.get("Black", "").lower()

        if white_name == username_lower:
            color = "white"
            my_rating = _parse_elo(tags.get("WhiteElo"))
            opp_rating = _parse_elo(tags.get("BlackElo"))
        elif black_name == username_lower:
            color = "black"
            my_rating = _parse_elo(tags.get("BlackElo"))
            opp_rating = _parse_elo(tags.get("WhiteElo"))
        else:
            continue

        result_tag = tags.get("Result", "*")
        if result_tag == "1/2-1/2":
            result = "draw"
        elif (result_tag == "1-0" and color == "white") or (result_tag == "0-1" and color == "black"):
            result = "win"
        else:
            result = "loss"

        event = tags.get("Event", "")
        rated = "rated" in event.lower()
        event_words = event.split()
        speed = event_words[1].lower() if len(event_words) >= 2 else "unknown"

        date_str = f"{tags.get('UTCDate', '')} {tags.get('UTCTime', '')}".strip()
        date = pd.to_datetime(date_str, format="%Y.%m.%d %H:%M:%S", errors="coerce")

        rows.append({
            "game_id": tags.get("GameId", tags.get("Site", "")),
            "date": date,
            "speed": speed,
            "rated": rated,
            "color": color,
            "my_rating": my_rating,
            "opponent_rating": opp_rating,
            "result": result,
            "status": tags.get("Termination"),
        })

    df = pd.DataFrame(rows)
    return df


def generate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Genera un resumen de estadisticas a partir del DataFrame de partidas."""
    stats = {
        "total_partidas": len(df),
        "victorias": int((df["result"] == "win").sum()),
        "derrotas": int((df["result"] == "loss").sum()),
        "tablas": int((df["result"] == "draw").sum()),
        "rating_promedio": round(df["my_rating"].mean(), 1) if not df["my_rating"].isna().all() else None,
        "rating_min": df["my_rating"].min(),
        "rating_max": df["my_rating"].max(),
        "partidas_blancas": int((df["color"] == "white").sum()),
        "partidas_negras": int((df["color"] == "black").sum()),
    }
    return pd.DataFrame([stats])


def make_visualizations(df: pd.DataFrame, output_dir: str):
    """Crea graficos con matplotlib y los guarda como PNG en output_dir."""

    plt.figure(figsize=(6, 4))
    df["result"].value_counts().reindex(["win", "loss", "draw"]).plot(kind="bar", color=["green", "red", "gray"])
    plt.title("Resultados de partidas")
    plt.xlabel("Resultado")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "resultados.png"))
    plt.close()

    plt.figure(figsize=(7, 4))
    df_sorted = df.sort_values("date")
    plt.plot(df_sorted["date"], df_sorted["my_rating"], marker="o", markersize=3)
    plt.title("Evolucion del rating")
    plt.xlabel("Fecha")
    plt.ylabel("Rating")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rating_evolucion.png"))
    plt.close()

    plt.figure(figsize=(5, 5))
    df["color"].value_counts().plot(kind="pie", autopct="%1.0f%%")
    plt.title("Partidas por color")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "color_distribucion.png"))
    plt.close()

    plt.figure(figsize=(6, 4))
    df["speed"].value_counts().plot(kind="bar", color="steelblue")
    plt.title("Partidas por modo de juego")
    plt.xlabel("Modo")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "modo_juego.png"))
    plt.close()

    print(f"Graficos guardados en la carpeta '{output_dir}'.")


def main():
    parser = argparse.ArgumentParser(description="Analisis de partidas de Lichess")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="Nombre de usuario de Lichess")
    parser.add_argument("--max-games", type=int, default=DEFAULT_MAX_GAMES, help="Numero de partidas a descargar")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Carpeta de salida")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    games = fetch_games(args.username, args.max_games)
    df = games_to_dataframe(games, args.username)

    if df.empty:
        print("No se pudo construir el DataFrame (0 partidas validas).")
        sys.exit(1)

    games_csv_path = os.path.join(args.output_dir, "partidas.csv")
    df.to_csv(games_csv_path, index=False, encoding="utf-8")
    print(f"Partidas exportadas a: {games_csv_path}")

    stats_df = generate_stats(df)
    stats_csv_path = os.path.join(args.output_dir, "estadisticas.csv")
    stats_df.to_csv(stats_csv_path, index=False, encoding="utf-8")
    print(f"Estadisticas exportadas a: {stats_csv_path}")
    print(stats_df.to_string(index=False))

    make_visualizations(df, args.output_dir)

    print("\nProceso completado con exito.")


if __name__ == "__main__":
    main()
