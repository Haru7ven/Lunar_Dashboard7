import numpy as np
import pytest

from horizon import (perfil_horizonte, horizonte_em, sol_iluminado, terra_visivel,
                     fraccao, maior_escuridao, RAIO_ANGULAR_SOL_DEG)


def test_terreno_plano_horizonte_zero():
    dem = np.zeros((101, 101))
    az, h = perfil_horizonte(dem, 10.0, 50, 50, curvatura=False)
    assert len(az) == 360
    assert np.allclose(h, 0.0, atol=1e-9)


def test_muro_a_norte_da_angulo_esperado():
    # Muro de 100 m a 200 m a norte do observador: atan(100/200) = 26,565 graus.
    dem = np.zeros((101, 101))
    dem[30, :] = 100.0           # linha 30 esta 20 pixeis (200 m) a norte da linha 50
    az, h = perfil_horizonte(dem, 10.0, 50, 50, curvatura=False)
    esperado = np.degrees(np.arctan(100.0 / 200.0))
    assert h[0] == pytest.approx(esperado, abs=1e-6)      # norte
    assert h[180] == pytest.approx(0.0, abs=1e-9)         # sul, sem relevo
    assert h[90] < 5.0                                    # este quase livre


def test_muro_a_este_aparece_no_azimute_90():
    dem = np.zeros((101, 101))
    dem[:, 70] = 50.0            # coluna 70 esta 20 pixeis (200 m) a este
    az, h = perfil_horizonte(dem, 10.0, 50, 50, curvatura=False)
    assert h[90] == pytest.approx(np.degrees(np.arctan(50.0 / 200.0)), abs=1e-6)
    assert h[270] == pytest.approx(0.0, abs=1e-9)


def test_altura_do_observador_baixa_o_horizonte():
    dem = np.zeros((101, 101))
    dem[30, :] = 100.0
    _, h0 = perfil_horizonte(dem, 10.0, 50, 50, altura_observador=0.0, curvatura=False)
    _, h2 = perfil_horizonte(dem, 10.0, 50, 50, altura_observador=10.0, curvatura=False)
    assert h2[0] < h0[0]
    assert h2[0] == pytest.approx(np.degrees(np.arctan(90.0 / 200.0)), abs=1e-6)


def test_curvatura_lunar_baixa_o_horizonte_em_terreno_plano():
    dem = np.zeros((2001, 2001))
    _, h = perfil_horizonte(dem, 100.0, 1000, 1000, curvatura=True)
    assert np.all(h < 0.0)


def test_observador_no_bordo_da_erro():
    with pytest.raises(ValueError):
        perfil_horizonte(np.zeros((10, 10)), 10.0, 0, 0)


def test_iluminacao_com_horizonte_constante():
    az = np.arange(360.0)
    horiz = np.full(360, 10.0)
    sol_el = np.array([5.0, 9.0, 10.2, 12.0, 20.0, 40.0])
    sol_az = np.full(6, 123.0)
    m = sol_iluminado(sol_az, sol_el, az, horiz)
    # com raio angular 0,27: precisa de el > 10,27
    assert list(m) == [False, False, False, True, True, True]
    assert fraccao(m) == pytest.approx(0.5)
    assert RAIO_ANGULAR_SOL_DEG == pytest.approx(0.27)


def test_horizonte_periodico_em_azimute():
    az = np.arange(360.0)
    horiz = np.where(az < 180, 5.0, 15.0)
    assert horizonte_em(-10.0, az, horiz) == pytest.approx(15.0)
    assert horizonte_em(370.0, az, horiz) == pytest.approx(5.0)


def test_terra_visivel_e_maior_escuridao():
    az = np.arange(360.0)
    horiz = np.full(360, 2.0)
    vis = terra_visivel(np.full(5, 80.0), np.array([1.0, 3.0, 4.0, 1.0, 5.0]), az, horiz)
    assert list(vis) == [False, True, True, False, True]
    sol = np.array([True, False, False, False, True, False])
    assert maior_escuridao(sol, dt_horas=2.0) == pytest.approx(6.0)
    assert maior_escuridao(np.array([True, True]), dt_horas=2.0) == 0.0
