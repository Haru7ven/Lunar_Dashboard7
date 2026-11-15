"""Demonstracao com dados sinteticos: DEM de uma cratera inventada e um Sol fictício.

Nao usa dados do desafio. Serve para ver o fluxo completo: DEM -> horizonte ->
iluminacao e maior escuridao.
"""
import numpy as np
from horizon import perfil_horizonte, sol_iluminado, fraccao, maior_escuridao

# DEM sintetico: plano com uma cratera de 1,5 km de raio e 300 m de profundidade,
# pixeis de 20 m (a escala do produto de 20 m que o projecto vai usar).
n, ps = 401, 20.0
y, x = np.mgrid[0:n, 0:n]
r = np.hypot(y - n / 2, x - n / 2) * ps
dem = np.where(r < 1500.0, -300.0 * (1 - (r / 1500.0) ** 2), 0.0)

lin, col = 200, 230           # observador dentro da cratera, a leste do centro
for h_obs in (0.0, 2.0, 10.0):
    az, hor = perfil_horizonte(dem, ps, lin, col, altura_observador=h_obs)
    # Sol fictício: 30 dias, 1 h de passo, a oscilar entre -12 e +12 graus de elevacao
    t = np.arange(0, 30 * 24)
    fase = 2 * np.pi * t / (29.5 * 24)
    sol_az = (np.degrees(fase)) % 360.0
    sol_el = 12.0 * np.sin(fase + 1.0)
    lit = sol_iluminado(sol_az, sol_el, az, hor)
    print(f"altura {h_obs:4.1f} m | horizonte max {hor.max():5.2f} graus | "
          f"iluminacao {100 * fraccao(lit):5.1f} % | "
          f"maior escuridao {maior_escuridao(lit, 1.0):5.1f} h")
