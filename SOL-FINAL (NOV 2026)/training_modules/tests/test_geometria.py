import numpy as np
import pytest

from ephem import local_azel, posicao_local_km


def test_vector_radial_da_elevacao_90():
    obs = posicao_local_km(0.0, 0.0)
    az, el = local_azel([obs * 2.0 - obs], 0.0, 0.0)
    assert el[0] == pytest.approx(90.0, abs=1e-9)


def test_norte_este_sul_oeste_no_equador():
    # Observador em lat 0, lon 0: norte = +z, este = +y, sul = -z, oeste = -y.
    v = np.array([[0.0, 0.0, 1.0],
                  [0.0, 1.0, 0.0],
                  [0.0, 0.0, -1.0],
                  [0.0, -1.0, 0.0]])
    az, el = local_azel(v, 0.0, 0.0)
    assert np.allclose(az, [0.0, 90.0, 180.0, 270.0], atol=1e-9)
    assert np.allclose(el, 0.0, atol=1e-9)


def test_elevacao_de_vector_inclinado():
    # 45 graus acima do horizonte, a norte.
    v = np.array([[1.0, 0.0, 1.0]])
    az, el = local_azel(v, 0.0, 0.0)
    assert az[0] == pytest.approx(0.0, abs=1e-9)
    assert el[0] == pytest.approx(45.0, abs=1e-9)


def test_posicao_local_tem_o_raio_pedido():
    p = posicao_local_km(-89.9, 123.0, raio_km=1737.4)
    assert np.linalg.norm(p) == pytest.approx(1737.4)
    assert p[2] < 0


def test_polo_sul_o_norte_local_aponta_para_longe_do_polo():
    # Perto do polo sul, um vector para o centro da Lua (-posicao) tem elevacao -90.
    obs = posicao_local_km(-89.0, 45.0)
    az, el = local_azel([-obs], -89.0, 45.0)
    assert el[0] == pytest.approx(-90.0, abs=1e-9)
