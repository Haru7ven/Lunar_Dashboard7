#!/usr/bin/env python3
"""
SOL - CLPS Lunar Planner
Trade-Off & Comparison Suite: Site A (Connecting Ridge) vs Site B (Shackleton PSR)
Compares scientific metrics between candidate landing sites for the NASA Space Apps presentation.
"""

import sys
import json
import argparse
from pathlib import Path


def load_json(p: Path):
    if not p.exists():
        raise FileNotFoundError(f"Ficheiro de dados nao encontrado: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def compare(file_a: Path, file_b: Path):
    print("=" * 76)
    print("SOL - CLPS LUNAR PLANNER: RELATORIO COMPARATIVO CIENTIFICO (TRADE-OFF)")
    print("=" * 76)

    da = load_json(file_a)
    db = load_json(file_b)

    sa = da["site"]
    sb = db["site"]
    sta = da["stats"]
    stb = db["stats"]

    print(f"\n{'PARAMETRO DE MISSAO':<32} | {'SITE A':<20} | {'SITE B':<20}")
    print("-" * 76)
    print(f"{'Latitude':<32} | {sa['lat']:>18.2f} deg | {sb['lat']:>18.2f} deg")
    print(f"{'Longitude Este':<32} | {sa['lon']:>18.2f} deg | {sb['lon']:>18.2f} deg")
    print(f"{'Altitude Esfera (R=1737.4 km)':<32} | {sa['ground_alt']:>16.0f} m   | {sb['ground_alt']:>16.0f} m  ")
    print(f"{'Mastro de Comunicacoes':<32} | {sa['mast']:>18.1f} m   | {sb['mast']:>18.1f} m  ")
    print("-" * 76)
    print(f"{'Iluminacao Solar (% do tempo)':<32} | {sta['sun_pct']:>18.1f} %   | {stb['sun_pct']:>18.1f} %  ")
    print(f"{'Visibilidade da Terra DTE (%)':<32} | {sta['earth_pct']:>18.1f} %   | {stb['earth_pct']:>18.1f} %  ")
    print(f"{'Maior Periodo de Escuridao':<32} | {sta['max_dark_h']:>16.1f} h   | {stb['max_dark_h']:>16.1f} h  ")
    print(f"{'Maior Blecaute de Terra (DTE)':<32} | {sta['max_noearth_h']:>16.1f} h   | {stb['max_noearth_h']:>16.1f} h  ")
    print("=" * 76)

    print("\n[RESUMO] (calculado a partir dos ficheiros; resultados preliminares, nao validados)")
    for nome, st in (("SITE A", sta), ("SITE B", stb)):
        print(f" * {nome}: Sol visivel {st['sun_pct']:.1f} % do tempo, Terra visivel (geometria) {st['earth_pct']:.1f} %, "
              f"maior periodo sem Sol {st['max_dark_h']:.1f} h, maior periodo sem Terra {st['max_noearth_h']:.1f} h.")
    print(" * Visibilidade da Terra e geometrica; nao e disponibilidade de comunicacao.")
    print("=" * 76)


def parse_args():
    parser = argparse.ArgumentParser(description="Comparador de Locais SOL CLPS")
    parser.add_argument("--a", type=str, default="web/data_A.json", help="Ficheiro do Site A")
    parser.add_argument("--b", type=str, default="web/data_B.json", help="Ficheiro do Site B")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    fa = project_root / args.a if not Path(args.a).is_absolute() else Path(args.a)
    fb = project_root / args.b if not Path(args.b).is_absolute() else Path(args.b)

    try:
        compare(fa, fb)
    except Exception as exc:
        print(f"[ERRO]: {exc}", file=sys.stderr)
        sys.exit(1)
