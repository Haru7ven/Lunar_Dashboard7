# Compara az/el do Sol e da Terra calculados com SPICE contra o JPL Horizons.
# Uso: python validar.py [LAT] [LON]        (precisa de internet)
import sys, os, numpy as np, spiceypy as sp
from astroquery.jplhorizons import Horizons
from astropy.time import Time

BASE = os.path.dirname(os.path.abspath(__file__))
LAT = float(sys.argv[1]) if len(sys.argv) > 1 else -89.45
LON = float(sys.argv[2]) if len(sys.argv) > 2 else 222.7
TOL = 0.1   # graus
for k in ["naif0012.tls", "de440s.bsp", "pck00011.tpc", "moon_pa_de440_200625.bpc", "moon_de440_250416.tf"]:
    sp.furnsh(os.path.join(BASE, "data", "kernels", k))

site = sp.georec(np.radians(LON), np.radians(LAT), 0.0, 1737.4, 0.0)   # altitude 0 nos dois lados
up = site / np.linalg.norm(site)
east = np.cross([0, 0, 1], up); east /= np.linalg.norm(east)
north = np.cross(up, east)

def spice_azel(body, utc):
    v = sp.spkpos(body, sp.utc2et(utc), "MOON_ME", "LT+S", "MOON")[0] - site
    el = np.degrees(np.arcsin(np.dot(v, up) / np.linalg.norm(v)))
    az = np.degrees(np.arctan2(np.dot(v, east), np.dot(v, north))) % 360
    return az, el

epochs = ["2026-11-14T00:00:00", "2026-11-17T06:00:00", "2026-11-22T12:00:00",
          "2026-12-01T18:00:00", "2026-12-10T03:00:00"]
worst = 0.0
print(f"{'corpo':6} {'UTC':20} {'dAz':>8} {'dEl':>8}")
for body, hid in (("SUN", "10"), ("EARTH", "399")):
    for e in epochs:
        az, el = spice_azel(body, e)
        q = Horizons(id=hid, location={"lon": LON, "lat": LAT, "elevation": 0.0, "body": 301},
                     epochs=Time(e, scale="utc").jd).ephemerides()
        daz = (az - float(q["AZ"][0]) + 180) % 360 - 180
        delv = el - float(q["EL"][0])
        worst = max(worst, abs(daz), abs(delv))
        print(f"{body:6} {e:20} {daz:8.4f} {delv:8.4f}")
print(f"\nErro maximo: {worst:.4f} graus ->", "VALIDADO" if worst < TOL else "REVER (tolerancia %.2f)" % TOL)
