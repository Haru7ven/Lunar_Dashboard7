import sys, os, json, webbrowser
import numpy as np, rasterio, spiceypy as sp

# ---------------- CONFIGURACAO ----------------
BASE = r"C:\Users\lenovo\sol-clps-planner"
LAT = float(sys.argv[1]) if len(sys.argv) > 1 else -89.45   # graus (negativo = sul)
LON = float(sys.argv[2]) if len(sys.argv) > 2 else 222.7    # graus Este, 0 a 360
MAST = 2.0                       # altura do observador (m)
START, DAYS, STEP = "2026-11-14T00:00:00", 30, 1800   # inicio, dias, passo (s)
R = 1737400.0                    # raio de referencia lunar (m)
SUN_RADIUS = 0.267               # raio angular do Sol (graus)
KERNELS = ["naif0012.tls", "de440s.bsp", "pck00011.tpc",
           "moon_pa_de440_200625.bpc", "moon_de440_250416.tf"]

# ---------------- DEM ----------------
src = rasterio.open(BASE + r"\data\raw\ldem_875s_20m.lbl")
raw = src.read(1).astype("float32")
h = np.where(raw == src.nodata, np.nan, raw * 0.5)       # metros acima de R
b, RES = src.bounds, 20.0
NR, NC = h.shape

def sample(x, y):
    c = np.floor((x - b.left) / RES).astype(int)
    r = np.floor((b.top - y) / RES).astype(int)
    ok = (c >= 0) & (c < NC) & (r >= 0) & (r < NR)
    out = np.full(x.shape, np.nan, dtype="float32")
    out[ok] = h[r[ok], c[ok]]
    return out

# posicao do local em estereografica polar (sul)
lat, lon = np.radians(LAT), np.radians(LON)
rho = max(2 * R * np.tan((np.pi / 2 + lat) / 2), 1.0)
x0, y0 = rho * np.sin(lon), rho * np.cos(lon)
z0 = float(sample(np.array([x0]), np.array([y0]))[0])
if np.isnan(z0):
    sys.exit("Local fora do DEM (so cobre 87.5S a 90S). Escolhe outra latitude/longitude.")
z0 += MAST
print(f"Local: lat {LAT}, lon {LON}, x={x0:.0f} m, y={y0:.0f} m, altitude {z0:.1f} m")

# ---------------- HORIZONTE (ray-marching) ----------------
az = np.arange(0, 360, 0.5)
d = np.arange(20.0, 70000.0, 40.0)
nx, ny = x0 / rho, y0 / rho            # norte local = para fora do polo
ex, ey = ny, -nx                       # este local
a = np.radians(az)[:, None]
X = x0 + (np.cos(a) * nx + np.sin(a) * ex) * d[None, :]
Y = y0 + (np.cos(a) * ny + np.sin(a) * ey) * d[None, :]
Z = sample(X, Y)
ang = np.arctan2(Z - z0, d[None, :]) - d[None, :] / (2 * R)   # inclui curvatura
ang = np.where(np.isnan(ang), -np.inf, ang)
hor = np.degrees(ang.max(axis=1))
hor = np.where(np.isfinite(hor), hor, -5.0)
print(f"Horizonte: min {hor.min():.2f}, max {hor.max():.2f} graus")

# ---------------- SOL E TERRA (SPICE) ----------------
for k in KERNELS:
    sp.furnsh(BASE + "\\data\\kernels\\" + k)
ets = sp.utc2et(START) + np.arange(0, DAYS * 86400, STEP)
site = sp.georec(lon, lat, z0 / 1000.0, R / 1000.0, 0.0)
up = site / np.linalg.norm(site)
east = np.cross([0, 0, 1], up); east /= np.linalg.norm(east)
north = np.cross(up, east)

def azel(body):
    A, E = [], []
    for et in ets:
        v = sp.spkpos(body, et, "MOON_ME", "LT+S", "MOON")[0] - site
        E.append(np.degrees(np.arcsin(np.dot(v, up) / np.linalg.norm(v))))
        A.append(np.degrees(np.arctan2(np.dot(v, east), np.dot(v, north))) % 360)
    return np.array(A), np.array(E)

sun_az, sun_el = azel("SUN")
ear_az, ear_el = azel("EARTH")
hz_s = np.interp(sun_az, az, hor, period=360)
hz_e = np.interp(ear_az, az, hor, period=360)
sun_vis = (sun_el + SUN_RADIUS) > hz_s        # limbo superior
ear_vis = ear_el > hz_e                       # centro da Terra

def longest(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best * STEP / 3600

stats = {
    "sun_pct": float(sun_vis.mean() * 100), "earth_pct": float(ear_vis.mean() * 100),
    "both_pct": float((sun_vis & ear_vis).mean() * 100),
    "max_dark_h": longest(~sun_vis), "max_noearth_h": longest(~ear_vis),
}
print(stats)

# ---------------- MAPA DO DEM (reduzido) ----------------
K = 16
sub = h[::K, ::K]
sub = np.nan_to_num(sub, nan=float(np.nanmin(sub)))[::-1]
mx = ((b.left + RES * (np.arange(0, NC, K) + 0.5)) / 1000).round(2)
my = ((b.top - RES * (np.arange(0, NR, K) + 0.5)) / 1000).round(2)[::-1]

data = {
    "site": {"lat": LAT, "lon": LON, "x": x0 / 1000, "y": y0 / 1000, "z": z0, "mast": MAST},
    "stats": stats, "az": az.tolist(), "hor": hor.round(3).tolist(),
    "t": [sp.et2utc(e, "ISOC", 0) for e in ets],
    "sun_az": sun_az.round(2).tolist(), "sun_el": sun_el.round(3).tolist(),
    "ear_az": ear_az.round(2).tolist(), "ear_el": ear_el.round(3).tolist(),
    "hz_s": hz_s.round(3).tolist(), "hz_e": hz_e.round(3).tolist(),
    "sun_vis": sun_vis.astype(int).tolist(), "ear_vis": ear_vis.astype(int).tolist(),
    "mx": mx.tolist(), "my": my.tolist(), "dem": sub.astype(int).tolist(),
}

HTML = """<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8">
<title>SOL - Planeador lunar</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>body{font-family:Arial,sans-serif;margin:16px;background:#111;color:#eee}
.k{display:flex;gap:12px;flex-wrap:wrap}.c{background:#222;padding:10px 16px;border-radius:6px}
.c b{font-size:22px;color:#f5b700}.g{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
@media(max-width:900px){.g{grid-template-columns:1fr}}</style></head><body>
<h2>SOL - Iluminacao solar e visibilidade da Terra (DTE)</h2>
<p id="info"></p><div class="k" id="kpi"></div>
<div class="g"><div id="map"></div><div id="sky"></div>
<div id="sun"></div><div id="ear"></div></div><div id="vis"></div>
<script>
const D=__DATA__, S=D.stats, T={paper_bgcolor:'#111',plot_bgcolor:'#111',font:{color:'#eee'}};
document.getElementById('info').textContent=`Local: lat ${D.site.lat} , lon ${D.site.lon} E, altitude ${D.site.z.toFixed(0)} m (mastro ${D.site.mast} m). Passo de 30 min, ${D.t[0]} a ${D.t[D.t.length-1]} UTC.`;
const kp=[['Sol visivel',S.sun_pct.toFixed(1)+' %'],['Terra visivel',S.earth_pct.toFixed(1)+' %'],['Sol e Terra',S.both_pct.toFixed(1)+' %'],['Maior periodo sem Sol',S.max_dark_h.toFixed(1)+' h'],['Maior periodo sem Terra',S.max_noearth_h.toFixed(1)+' h']];
document.getElementById('kpi').innerHTML=kp.map(k=>`<div class="c">${k[0]}<br><b>${k[1]}</b></div>`).join('');
Plotly.newPlot('map',[{type:'heatmap',x:D.mx,y:D.my,z:D.dem,colorscale:'Gray',colorbar:{title:'m'}},
 {type:'scatter',x:[D.site.x],y:[D.site.y],mode:'markers',marker:{color:'red',size:10},name:'Local'}],
 {...T,title:'DEM LOLA (km a partir do polo)',yaxis:{scaleanchor:'x'},height:480});
const idx=(el)=>el.map((v,i)=>v>-3?i:-1).filter(i=>i>=0);
const si=idx(D.sun_el), ei=idx(D.ear_el);
Plotly.newPlot('sky',[
 {type:'scatterpolar',mode:'lines',r:D.hor.map(v=>90-v),theta:D.az,fill:'toself',fillcolor:'rgba(100,150,255,.15)',line:{color:'#8ab4ff'},name:'Horizonte'},
 {type:'scatterpolar',mode:'markers',r:si.map(i=>90-D.sun_el[i]),theta:si.map(i=>D.sun_az[i]),marker:{color:'orange',size:4},name:'Sol'},
 {type:'scatterpolar',mode:'markers',r:ei.map(i=>90-D.ear_el[i]),theta:ei.map(i=>D.ear_az[i]),marker:{color:'#4da3ff',size:4},name:'Terra'}],
 {...T,title:'Ceu visto do local (centro = zenite)',height:480,polar:{bgcolor:'#111',angularaxis:{direction:'clockwise',rotation:90},radialaxis:{range:[0,93],tickvals:[0,30,60,90],ticktext:['90','60','30','0']}}});
const L=(id,tt,el,hz,c)=>Plotly.newPlot(id,[{x:D.t,y:el,mode:'lines',name:'Elevacao',line:{color:c}},{x:D.t,y:hz,mode:'lines',name:'Horizonte',line:{color:'#888',dash:'dot'}}],{...T,title:tt,yaxis:{title:'graus'},height:320});
L('sun','Sol: elevacao vs horizonte',D.sun_el,D.hz_s,'orange');
L('ear','Terra: elevacao vs horizonte',D.ear_el,D.hz_e,'#4da3ff');
Plotly.newPlot('vis',[{type:'heatmap',x:D.t,y:['Sol','Terra (DTE)'],z:[D.sun_vis,D.ear_vis],colorscale:[[0,'#333'],[1,'#f5b700']],showscale:false}],{...T,title:'Visibilidade (amarelo = visivel)',height:220});
</script></body></html>"""

os.makedirs(BASE + r"\web", exist_ok=True)
out = BASE + r"\web\index.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML.replace("__DATA__", json.dumps(data)))
print("Gerado:", out)
webbrowser.open(out)
