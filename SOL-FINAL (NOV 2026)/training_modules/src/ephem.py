"""Posicoes do Sol e da Terra no ceu local de um ponto da Lua (SOL, treino).

A parte geometrica (local_azel, posicao_local_km) nao precisa de SPICE e testa-se
com vectores inventados. A parte que usa o SpiceyPy (serie_azel, utc_para_et) precisa
dos kernels da NAIF carregados com carregar_kernels().

Notas de rigor
- O tempo interno e o tempo de efemerides (ET); converte-se UTC para ET com utc_para_et.
- O referencial lunar tem de ser escolhido e registado. IAU_MOON (por omissao) so exige
  um kernel PCK de constantes planetarias; o referencial de eixos principais (MOON_PA)
  e mais rigoroso mas exige kernels adicionais (binario PCK e frame kernel lunar).
"""
import numpy as np

RAIO_LUA_KM = 1737.4


def posicao_local_km(lat_deg, lon_deg, raio_km=RAIO_LUA_KM, altura_km=0.0):
    """Posicao de um ponto da superficie no referencial fixo da Lua (km)."""
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    r = raio_km + altura_km
    return r * np.array([np.cos(lat) * np.cos(lon),
                         np.cos(lat) * np.sin(lon),
                         np.sin(lat)])


def local_azel(vetores, lat_deg, lon_deg):
    """Converte vectores (N, 3) do referencial fixo da Lua em (azimute, elevacao).

    Os vectores sao posicoes do alvo relativas ao observador. Azimute em graus,
    no sentido horario a partir do norte; elevacao em graus acima do horizonte plano.
    """
    v = np.atleast_2d(np.asarray(vetores, dtype=float))
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    este = np.array([-np.sin(lon), np.cos(lon), 0.0])
    norte = np.array([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)])
    cima = np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
    e, n, u = v @ este, v @ norte, v @ cima
    az = np.degrees(np.arctan2(e, n)) % 360.0
    el = np.degrees(np.arcsin(u / np.linalg.norm(v, axis=1)))
    return az, el


def carregar_kernels(caminhos):
    """Carrega kernels SPICE (leap seconds, efemerides, PCK, frames)."""
    import spiceypy as sp
    for c in caminhos:
        sp.furnsh(str(c))


def utc_para_et(utc_strings):
    """Converte datas UTC (texto) em tempo de efemerides. Exige o kernel de leap seconds."""
    import spiceypy as sp
    return np.array([sp.str2et(s) for s in utc_strings])


def serie_azel(alvo, et, lat_deg, lon_deg, referencial="IAU_MOON",
               correccao="LT+S", raio_km=RAIO_LUA_KM, altura_km=0.0):
    """Azimute e elevacao de 'alvo' ('SUN' ou 'EARTH') ao longo de uma serie de ET."""
    import spiceypy as sp
    obs = posicao_local_km(lat_deg, lon_deg, raio_km, altura_km)
    pos = np.array([sp.spkpos(alvo, t, referencial, correccao, "MOON")[0] for t in et])
    return local_azel(pos - obs, lat_deg, lon_deg)
