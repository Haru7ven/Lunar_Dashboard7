"""Perfil de horizonte e metricas de iluminacao (SOL, treino com dados sinteticos).

Convencoes
- O raster do DEM tem as linhas a crescer para sul e as colunas a crescer para este
  (orientacao habitual de um raster com norte para cima).
- O azimute mede-se em graus, no sentido horario a partir do norte (0 = N, 90 = E).
- As alturas e as distancias estao em metros; os angulos em graus.
"""
import numpy as np
from scipy.ndimage import map_coordinates

R_LUA_M = 1_737_400.0       # raio medio da Lua (m)
RAIO_ANGULAR_SOL_DEG = 0.27  # raio angular aparente do Sol visto da Lua (aprox.)


def perfil_horizonte(dem, tam_pixel, linha, coluna, altura_observador=0.0,
                     n_azimutes=360, dist_max=None, passo=None,
                     curvatura=True):
    """Devolve (azimutes, horizonte) com o angulo de elevacao do relevo em cada azimute.

    dem: matriz 2D de altitudes (m).
    tam_pixel: lado do pixel (m).
    linha, coluna: posicao do observador no raster (pode ser fraccionaria).
    altura_observador: altura acima da superficie (m).
    dist_max: alcance do ray-marching (m); por omissao, ate ao bordo mais proximo.
    passo: passo ao longo do raio (m); por omissao, metade do pixel.
    curvatura: se verdadeiro, subtrai d^2 / (2 R) para a curvatura lunar.
    """
    dem = np.asarray(dem, dtype=float)
    nl, nc = dem.shape
    if passo is None:
        passo = tam_pixel / 2.0
    if dist_max is None:
        dist_max = tam_pixel * min(linha, coluna, nl - 1 - linha, nc - 1 - coluna)
    if dist_max < passo:
        raise ValueError("dist_max menor do que o passo: o observador esta no bordo do DEM")

    z0 = map_coordinates(dem, [[linha], [coluna]], order=1)[0] + altura_observador
    dist = np.arange(passo, dist_max + 1e-9, passo)
    az = np.arange(n_azimutes) * (360.0 / n_azimutes)
    az_rad = np.radians(az)[:, None]

    lin = linha - dist[None, :] * np.cos(az_rad) / tam_pixel   # norte = linhas a diminuir
    col = coluna + dist[None, :] * np.sin(az_rad) / tam_pixel  # este = colunas a aumentar
    z = map_coordinates(dem, [lin.ravel(), col.ravel()], order=1,
                        mode="nearest").reshape(lin.shape)

    dz = z - z0
    if curvatura:
        dz = dz - dist[None, :] ** 2 / (2.0 * R_LUA_M)
    ang = np.degrees(np.arctan2(dz, dist[None, :]))
    return az, ang.max(axis=1)


def horizonte_em(az_consulta, azimutes, horizonte):
    """Interpola o horizonte para azimutes arbitrarios (periodico, 360 graus)."""
    return np.interp(np.asarray(az_consulta) % 360.0, azimutes, horizonte,
                     period=360.0)


def sol_iluminado(sol_az, sol_el, azimutes, horizonte,
                  raio_sol=RAIO_ANGULAR_SOL_DEG):
    """Mascara booleana: o Sol fornece energia quando el - raio esta acima do horizonte."""
    h = horizonte_em(sol_az, azimutes, horizonte)
    return (np.asarray(sol_el) - raio_sol) > h


def terra_visivel(terra_az, terra_el, azimutes, horizonte):
    """Mascara booleana: a Terra esta acima do horizonte (comunicacao directa, DTE)."""
    h = horizonte_em(terra_az, azimutes, horizonte)
    return np.asarray(terra_el) > h


def fraccao(mascara):
    """Fraccao de instantes verdadeiros numa mascara."""
    m = np.asarray(mascara, dtype=bool)
    return float(m.mean()) if m.size else float("nan")


def maior_sequencia(mascara, dt_horas=1.0):
    """Duracao (horas) da maior sequencia contigua de valores verdadeiros."""
    m = np.asarray(mascara, dtype=bool)
    melhor = atual = 0
    for v in m:
        atual = atual + 1 if v else 0
        melhor = max(melhor, atual)
    return melhor * dt_horas


def maior_escuridao(sol_mask, dt_horas=1.0):
    """Maior periodo contiguo sem Sol (horas)."""
    return maior_sequencia(~np.asarray(sol_mask, dtype=bool), dt_horas)
