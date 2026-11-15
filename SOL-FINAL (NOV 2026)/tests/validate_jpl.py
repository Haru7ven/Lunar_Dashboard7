#!/usr/bin/env python3
"""
SOL - validacao das direcoes do Sol e da Terra contra o JPL Horizons.
Compara azimute e elevacao (SPICE, guardados no JSON) com o Horizons para o mesmo local topocentrico lunar.
Nao valida o perfil do horizonte. Precisa de internet.
Uso: python tests/validate_jpl.py --json web/data_A.json --samples 10
"""
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import astropy.time
from astroquery.jplhorizons import Horizons

TOL_DEG = 0.1  # tolerancia adoptada pela equipa (azimute e elevacao)
BODIES = [("SUN", "10", "sun_az", "sun_el"), ("EARTH", "399", "ear_az", "ear_el")]


def angular_diff_deg(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def validate(json_path: Path, num_samples: int = 10):
    if not json_path.exists():
        raise FileNotFoundError(f"Ficheiro JSON nao encontrado: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    site, ts = data["site"], data["time_series"]
    lat, lon, alt_km = site["lat"], site["lon"], site["alt"] / 1000.0
    times = ts["t"]
    idx = np.linspace(0, len(times) - 1, num_samples, dtype=int)
    jds = [astropy.time.Time(times[i], scale="utc").jd for i in idx]

    print("=" * 76)
    print(f"Ficheiro: {json_path}")
    print(f"Observador: lat {lat:.4f}, lon {lon:.4f} E, altitude {site['alt']:.1f} m (Lua, corpo 301)")
    print(f"{num_samples} epocas | tolerancia {TOL_DEG} deg")
    worst = 0.0
    for nome, hid, kaz, kel in BODIES:
        eph = Horizons(id=hid, location={"lon": lon, "lat": lat, "elevation": alt_km, "body": "301"},
                       epochs=jds).ephemerides()
        print("-" * 76)
        print(f"{nome}\n{'UTC':<20} | {'Az SPICE':>9} {'Az JPL':>9} {'dAz':>8} | {'El SPICE':>9} {'El JPL':>9} {'dEl':>8}")
        d_az, d_el = [], []
        for k, i in enumerate(idx):
            s_az, s_el = float(ts[kaz][i]), float(ts[kel][i])
            j_az, j_el = float(eph["AZ"][k]), float(eph["EL"][k])
            d_az.append(angular_diff_deg(s_az, j_az)); d_el.append(abs(s_el - j_el))
            print(f"{times[i]:<20} | {s_az:>9.3f} {j_az:>9.3f} {d_az[-1]:>8.4f} | {s_el:>9.3f} {j_el:>9.3f} {d_el[-1]:>8.4f}")
        print(f"  Azimute:  RMS {np.sqrt(np.mean(np.square(d_az))):.4f} | maximo {max(d_az):.4f} deg")
        print(f"  Elevacao: RMS {np.sqrt(np.mean(np.square(d_el))):.4f} | maximo {max(d_el):.4f} deg")
        worst = max(worst, max(d_az), max(d_el))
    print("=" * 76)
    print(f"Erro maximo global: {worst:.4f} deg")
    print("RESULTADO:", "dentro da tolerancia" if worst < TOL_DEG else "FORA da tolerancia, investigar antes de usar os resultados")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Validacao JPL Horizons (SOL)")
    ap.add_argument("--json", default="web/data_A.json")
    ap.add_argument("--samples", type=int, default=10)
    a = ap.parse_args()
    p = Path(a.json)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / p
    try:
        validate(p, a.samples)
    except Exception as exc:
        print(f"\n[ERRO] Falha na validacao: {exc}", file=sys.stderr)
        sys.exit(1)
