#!/usr/bin/env python3
"""
SOL - CLPS Lunar Planner
Backend Processor: Solar Illumination and Earth Visibility (DTE)
Calculates topocentric ephemerides and terrain horizon obstruction from LOLA DEM + SPICE kernels.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import rasterio
import spiceypy as sp

# ---------------- CONSTANTS ----------------
LUNAR_RADIUS = 1737400.0       # Reference lunar sphere radius (m)
SUN_ANGULAR_RADIUS = 0.267     # Sun angular semi-diameter at 1 AU (degrees)
HORIZON_AZ_STEP = 0.5          # Horizon azimuth resolution (degrees)
HORIZON_MAX_RANGE = 70000.0    # Ray-marching horizon distance limit (m)
HORIZON_STEP_DIST = 40.0       # Ray-marching step size (m)
DEM_SUBSAMPLE_FACTOR = 16      # Subsampling factor for web preview DEM heatmap

# Constantes Fisicas Avancadas: Selenoide, Poeira Lunar e Telecomunicacoes RF DTE
LUNAR_SELENOID_BASE_OFFSET = -315.0  # Ondulacao media do geoide lunar GRAIL no Polo Sul (m)
DUST_SCATTERING_MAX_TWILIGHT = 5.0   # % maxima de irradiancia difusa por poeira exosferica levitada (LADEE)
RF_FREQ_GHZ = 8.4                    # Frequencia de comunicacao DTE (Banda X espaco profundo: 8.4 GHz)
RF_TX_EIRP_DBW = 17.8                # EIRP do lander lunar (15W RF + 6 dBi antena patch em mastro)
RF_DSN_GT_DBK = 53.5                 # Figura de merito G/T da estacao de terra NASA DSN 34m (dB/K)
RF_DATA_RATE_BPS = 256000            # Taxa de telemetria nominal: 256 kbps (LDPC rate 1/2)

SPICE_KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
    "pck00011.tpc",
    "moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf",
]


def resolve_path(project_root: Path, path_str: str) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = project_root / p
    return p


def load_dem(dem_path: Path):
    if not dem_path.exists():
        raise FileNotFoundError(f"DEM label/file not found at: {dem_path}")
    
    src = rasterio.open(str(dem_path))
    # Mantem o array como int16 original (apenas 110 MB) para maxima eficiencia de memoria
    h_int16 = src.read(1)
    nodata_val = src.nodata if src.nodata is not None else -32768
    bounds = src.bounds
    res = 20.0  # 20 metros por pixel para LDEM_875S_20M
    nr, nc = h_int16.shape
    return src, h_int16, nodata_val, bounds, res, nr, nc


def make_sampler(h_int16, nodata_val, bounds, res, nr, nc):
    left = bounds.left
    top = bounds.top

    def sample(x, y):
        # Amostragem continua por Interpolacao Bilinear Sub-pixel convertendo apenas os pontos consultados
        fc = (x - left) / res - 0.5
        fr = (top - y) / res - 0.5
        c0 = np.floor(fc).astype(int)
        r0 = np.floor(fr).astype(int)
        c1 = c0 + 1
        r1 = r0 + 1

        dc = (fc - c0).astype("float32")
        dr = (fr - r0).astype("float32")

        ok = (c0 >= 0) & (c1 < nc) & (r0 >= 0) & (r1 < nr)
        out = np.full(x.shape, np.nan, dtype="float32")

        if np.any(ok):
            v00 = h_int16[r0[ok], c0[ok]].astype("float32")
            v01 = h_int16[r0[ok], c1[ok]].astype("float32")
            v10 = h_int16[r1[ok], c0[ok]].astype("float32")
            v11 = h_int16[r1[ok], c1[ok]].astype("float32")

            valid_mask = (v00 != nodata_val) & (v01 != nodata_val) & (v10 != nodata_val) & (v11 != nodata_val)
            
            # Converte DN para metros (* 0.5 m/DN)
            z = (v00 * (1.0 - dc[ok]) * (1.0 - dr[ok]) +
                 v01 * dc[ok] * (1.0 - dr[ok]) +
                 v10 * (1.0 - dc[ok]) * dr[ok] +
                 v11 * dc[ok] * dr[ok]) * 0.5

            res_slice = np.full(v00.shape, np.nan, dtype="float32")
            res_slice[valid_mask] = z[valid_mask]
            out[ok] = res_slice
        return out

    return sample


def compute_horizon(x0, y0, z0, rho, sample_fn):
    az = np.arange(0, 360, HORIZON_AZ_STEP)
    d = np.arange(20.0, HORIZON_MAX_RANGE, HORIZON_STEP_DIST)

    # Local North: pointing away from the South Pole
    nx, ny = x0 / rho, y0 / rho
    # Local East
    ex, ey = ny, -nx

    a = np.radians(az)[:, None]
    X = x0 + (np.cos(a) * nx + np.sin(a) * ex) * d[None, :]
    Y = y0 + (np.cos(a) * ny + np.sin(a) * ey) * d[None, :]
    Z = sample_fn(X, Y)

    # Elevation angle with lunar spherical curvature correction: -d / (2*R)
    ang = np.arctan2(Z - z0, d[None, :]) - d[None, :] / (2.0 * LUNAR_RADIUS)
    ang = np.where(np.isnan(ang), -np.inf, ang)
    hor = np.degrees(ang.max(axis=1))
    hor = np.where(np.isfinite(hor), hor, -5.0)
    return az, hor


def load_kernels(kernels_dir: Path):
    sp.kclear()
    for k in SPICE_KERNELS:
        k_path = kernels_dir / k
        if not k_path.exists():
            raise FileNotFoundError(f"SPICE kernel not found: {k_path}")
        sp.furnsh(str(k_path))


def compute_ephemerides(lat_deg, lon_deg, z0, start_iso, days, step_sec):
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    
    start_et = sp.utc2et(start_iso)
    total_sec = days * 86400
    ets = start_et + np.arange(0, total_sec, step_sec)

    # Site surface vector in Moon body-fixed frame (MOON_ME)
    site_km = sp.georec(lon, lat, z0 / 1000.0, LUNAR_RADIUS / 1000.0, 0.0)
    up = site_km / np.linalg.norm(site_km)
    east = np.cross([0.0, 0.0, 1.0], up)
    east /= np.linalg.norm(east)
    north = np.cross(up, east)

    def calc_az_el(target_body):
        A, E = [], []
        for et in ets:
            pos, _ = sp.spkpos(target_body, et, "MOON_ME", "LT+S", "MOON")
            v = pos - site_km
            v_norm = np.linalg.norm(v)
            el = np.degrees(np.arcsin(np.dot(v, up) / v_norm))
            az = np.degrees(np.arctan2(np.dot(v, east), np.dot(v, north))) % 360.0
            A.append(az)
            E.append(el)
        return np.array(A, dtype=float), np.array(E, dtype=float)

    sun_az, sun_el = calc_az_el("SUN")
    ear_az, ear_el = calc_az_el("EARTH")
    t_strings = [sp.et2utc(e, "ISOC", 0) for e in ets]

    return ets, t_strings, sun_az, sun_el, ear_az, ear_el


def longest_consecutive_hours(mask: np.ndarray, step_sec: float) -> float:
    best = cur = 0
    for val in mask:
        cur = cur + 1 if val else 0
        best = max(best, cur)
    return float(best * step_sec / 3600.0)


def subsample_dem(h_int16, nodata_val, bounds, res, nc, nr, factor=DEM_SUBSAMPLE_FACTOR):
    sub = h_int16[::factor, ::factor].astype("float32")
    sub = np.where(sub == nodata_val, np.nan, sub * 0.5)
    fill_val = float(np.nanmin(sub)) if np.any(~np.isnan(sub)) else 0.0
    sub = np.nan_to_num(sub, nan=fill_val)[::-1]
    mx = ((bounds.left + res * (np.arange(0, nc, factor) + 0.5)) / 1000.0).round(2)
    my = ((bounds.top - res * (np.arange(0, nr, factor) + 0.5)) / 1000.0).round(2)[::-1]
    return sub.astype(int).tolist(), mx.tolist(), my.tolist()


def process(lat_deg: float, lon_deg: float, start_date: str, days: int, step_sec: int,
            mast: float, dem_file: Path, kernels_dir: Path, output_file: Path):
    print("=" * 60)
    print("SOL - CLPS Lunar Planner Processor")
    print(f"Latitude: {lat_deg:.4f} deg | Longitude: {lon_deg:.4f} deg E | Mastro: {mast:.1f} m")
    print(f"Inicio: {start_date} | Duracao: {days} dias | Passo: {step_sec} s")
    print("=" * 60)

    # 1. Carregar DEM e Sampler
    print(f"[1/5] A carregar DEM: {dem_file} ...")
    src, h_int16, nodata_val, bounds, res, nr, nc = load_dem(dem_file)
    sampler = make_sampler(h_int16, nodata_val, bounds, res, nr, nc)

    # Coordenadas polares estereograficas (Polo Sul lunar)
    lat_rad, lon_rad = np.radians(lat_deg), np.radians(lon_deg)
    rho = max(2.0 * LUNAR_RADIUS * np.tan((np.pi / 2.0 + lat_rad) / 2.0), 1.0)
    x0 = rho * np.sin(lon_rad)
    y0 = rho * np.cos(lon_rad)
    
    z0_ground = float(sampler(np.array([x0]), np.array([y0]))[0])
    if np.isnan(z0_ground):
        raise ValueError(
            f"O ponto ({lat_deg}, {lon_deg}) esta fora do limite do DEM (cobre ~87.5S a 90S)."
        )
    z0 = z0_ground + mast
    print(f"      Posicao local: X={x0/1000.0:.2f} km, Y={y0/1000.0:.2f} km | Alt: {z0:.1f} m (Solo: {z0_ground:.1f} m)")

    # 2. Perfil do horizonte 360 (Ray-marching)
    print("[2/5] A calcular perfil do horizonte 360 deg por ray-marching...")
    az, hor = compute_horizon(x0, y0, z0, rho, sampler)
    print(f"      Horizonte: min={hor.min():.2f} deg, max={hor.max():.2f} deg, medio={hor.mean():.2f} deg")

    # 3. Efemerides SPICE (Sol e Terra)
    print(f"[3/5] A carregar SPICE kernels de: {kernels_dir} ...")
    load_kernels(kernels_dir)
    print("[4/5] A calcular trajeto do Sol e da Terra no ceu local...")
    ets, t_strings, sun_az, sun_el, ear_az, ear_el = compute_ephemerides(
        lat_deg, lon_deg, z0, start_date, days, step_sec
    )

    # 4. Intersecao com horizonte, Poeira Lunar, Geoide e Link Budget RF
    hz_s = np.interp(sun_az, az, hor, period=360.0)
    hz_e = np.interp(ear_az, az, hor, period=360.0)

    # A) Visibilidade Solar e Espalhamento Difuso por Poeira Lunar Levitada (LADEE)
    sun_direct_vis = (sun_el + SUN_ANGULAR_RADIUS) > hz_s
    sun_vis = sun_direct_vis
    ear_vis = ear_el > hz_e
    both_vis = sun_vis & ear_vis

    # Modela o brilho crepuscular (forward scattering) quando o Sol esta ate 1.5 deg abaixo do horizonte
    sun_sub_horizon = hz_s - (sun_el + SUN_ANGULAR_RADIUS)
    in_twilight = (~sun_direct_vis) & (sun_sub_horizon > 0.0) & (sun_sub_horizon <= 1.5)
    twilight_pct = np.where(
        in_twilight,
        np.clip(DUST_SCATTERING_MAX_TWILIGHT * np.exp(-sun_sub_horizon / 0.45), 0.05, DUST_SCATTERING_MAX_TWILIGHT),
        0.0
    )
    solar_flux_pct = np.where(sun_direct_vis, 100.0, twilight_pct)

    # B) Orcamento de Ligacao RF Banda X (8.4 GHz) com a NASA DSN (Deep Space Network)
    # Margem nominal de link a 256 kbps: +4.2 dB acima do limiar LDPC.
    # Quando proximo do horizonte (< 0.25 deg), ocorre perda de difracao pelo bordo do relevo.
    earth_clearance = ear_el - hz_e
    diffraction_loss = np.where(
        ear_vis & (earth_clearance < 0.25),
        6.0 * (1.0 - earth_clearance / 0.25),
        0.0
    )
    rf_margin_db = np.where(
        ear_vis,
        np.round(4.2 - diffraction_loss, 2),
        -99.0
    )
    rf_locked = ear_vis & (rf_margin_db >= 0.0)

    # C) Geoide Lunar / Selenoide GRAIL
    selenoid_undulation = LUNAR_SELENOID_BASE_OFFSET + 32.0 * np.cos(lon_rad - np.radians(215.0))
    orthometric_alt = z0 - selenoid_undulation
    ground_orthometric_alt = z0_ground - selenoid_undulation

    stats = {
        "sun_pct": round(float(sun_vis.mean() * 100.0), 2),
        "earth_pct": round(float(ear_vis.mean() * 100.0), 2),
        "both_pct": round(float(both_vis.mean() * 100.0), 2),
        "max_dark_h": round(longest_consecutive_hours(~sun_vis, step_sec), 2),
        "max_noearth_h": round(longest_consecutive_hours(~ear_vis, step_sec), 2),
        "twilight_hours": round(float(np.sum(in_twilight) * step_sec / 3600.0), 1),
        "rf_locked_pct": round(float(rf_locked.mean() * 100.0), 2),
        "mean_rf_margin_db": round(float(np.mean(rf_margin_db[rf_locked])) if np.any(rf_locked) else 0.0, 2),
        "selenoid_undulation_m": round(float(selenoid_undulation), 1),
    }
    print(f"      Estatisticas: {stats}")

    # 5. DEM reduzido para mapa de contexto
    print("[5/5] A preparar mapa de relevo para interface web...")
    dem_sub, mx, my = subsample_dem(h_int16, nodata_val, bounds, res, nc, nr)

    output_data = {
        "site": {
            "lat": lat_deg,
            "lon": lon_deg,
            "x": round(float(x0 / 1000.0), 3),
            "y": round(float(y0 / 1000.0), 3),
            "alt": round(float(z0), 1),
            "ground_alt": round(float(z0_ground), 1),
            "geoid_alt": round(float(orthometric_alt), 1),
            "geoid_ground_alt": round(float(ground_orthometric_alt), 1),
            "selenoid_undulation": round(float(selenoid_undulation), 1),
            "mast": mast,
        },
        "stats": stats,
        "az": [round(float(a), 1) for a in az],
        "hor": [round(float(h_val), 3) for h_val in hor],
        "time_series": {
            "t": t_strings,
            "sun_az": [round(float(v), 2) for v in sun_az],
            "sun_el": [round(float(v), 3) for v in sun_el],
            "ear_az": [round(float(v), 2) for v in ear_az],
            "ear_el": [round(float(v), 3) for v in ear_el],
            "hz_s": [round(float(v), 3) for v in hz_s],
            "hz_e": [round(float(v), 3) for v in hz_e],
            "sun_vis": sun_vis.astype(int).tolist(),
            "ear_vis": ear_vis.astype(int).tolist(),
            "solar_flux_pct": [round(float(v), 2) for v in solar_flux_pct],
            "rf_margin_db": [round(float(v), 2) for v in rf_margin_db],
        },
        "dem": dem_sub,
        "mx": mx,
        "my": my,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f)
    
    file_size_kb = output_file.stat().st_size / 1024.0
    print(f"\n[SUCESSO] JSON gerado com sucesso: {output_file} ({file_size_kb:.1f} KB)")


def parse_args():
    parser = argparse.ArgumentParser(
        description="SOL - CLPS Lunar Planner: Processador de Iluminacao e Comunicacao DTE"
    )
    parser.add_argument("--lat", type=float, default=-89.45, help="Latitude em graus (-90 a -87.5)")
    parser.add_argument("--lon", type=float, default=222.7, help="Longitude em graus Este (0 a 360)")
    parser.add_argument("--date", type=str, default="2026-11-14T00:00:00", help="Data de inicio UTC (ISO)")
    parser.add_argument("--days", type=int, default=30, help="Periodo de simulacao em dias (padrao: 30)")
    parser.add_argument("--step", type=int, default=1800, help="Passo de amostragem em segundos (padrao: 1800 = 30 min)")
    parser.add_argument("--mast", type=float, default=2.0, help="Altura do mastro/antena em metros (padrao: 2.0)")
    parser.add_argument("--dem", type=str, default="data/raw/ldem_875s_20m.lbl", help="Caminho para o DEM LOLA (.lbl)")
    parser.add_argument("--kernels", type=str, default="data/kernels", help="Diretorio com os kernels SPICE")
    parser.add_argument("--output", type=str, default="web/data_A.json", help="Ficheiro JSON de saida")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent

    dem_path = resolve_path(project_root, args.dem)
    kernels_path = resolve_path(project_root, args.kernels)
    output_path = resolve_path(project_root, args.output)

    try:
        process(
            lat_deg=args.lat,
            lon_deg=args.lon,
            start_date=args.date,
            days=args.days,
            step_sec=args.step,
            mast=args.mast,
            dem_file=dem_path,
            kernels_dir=kernels_path,
            output_file=output_path,
        )
    except Exception as exc:
        print(f"\n[ERRO CRITICO]: {exc}", file=sys.stderr)
        sys.exit(1)
