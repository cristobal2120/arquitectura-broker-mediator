"""
tests/test_mediator.py

Pruebas unitarias del patrón Mediator.
Verifican que las entidades nunca se comunican directamente.
"""

import pytest
from mediator.coordinador import (
    Almacen, Camion, Seguros,
    CoordinadorDespacho, crear_subsistema_despacho,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def subsistema():
    almacen = Almacen(id_almacen="TEST", stock={"prod-PED001": 5, "prod-PED002": 0})
    seguros = Seguros(id_poliza="TEST-POL", vigente=True, cobertura_max_kg=5000)
    coord   = CoordinadorDespacho(almacen, seguros)
    camion  = Camion(id_camion="C-TEST", capacidad_max_kg=3000)
    coord.registrar_camion(camion)
    return coord, camion, almacen, seguros


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestMediatorAislamiento:

    def test_camion_no_tiene_referencia_a_almacen(self, subsistema):
        """El camión no debe tener atributo directo 'almacen'."""
        _, camion, _, _ = subsistema
        assert not hasattr(camion, "_almacen"), (
            "Camion no debe conocer directamente al Almacen — viola el Mediator."
        )

    def test_camion_no_tiene_referencia_a_seguros(self, subsistema):
        """El camión no debe tener atributo directo 'seguros'."""
        _, camion, _, _ = subsistema
        assert not hasattr(camion, "_seguros"), (
            "Camion no debe conocer directamente a Seguros — viola el Mediator."
        )

    def test_almacen_no_tiene_referencia_a_camion(self, subsistema):
        _, _, almacen, _ = subsistema
        assert not hasattr(almacen, "_camion")

    def test_seguros_no_tiene_referencia_a_almacen(self, subsistema):
        _, _, _, seguros = subsistema
        assert not hasattr(seguros, "_almacen")


class TestFlujoDespacho:

    def test_despacho_exitoso(self, subsistema):
        coord, camion, _, _ = subsistema
        resultado = camion.solicitar_despacho("PED001", peso_kg=500)
        assert resultado["ok"] is True
        assert resultado["pedido_id"] == "PED001"

    def test_despacho_sin_stock(self, subsistema):
        coord, camion, _, _ = subsistema
        # PED002 tiene stock 0
        resultado = camion.solicitar_despacho("PED002", peso_kg=100)
        assert resultado["ok"] is False
        assert resultado["razon"] == "sin_stock"

    def test_despacho_seguro_invalido_por_peso(self, subsistema):
        coord, camion, _, seguros = subsistema
        # Cobertura máxima es 5000 kg — enviamos 9000
        resultado = camion.solicitar_despacho("PED001", peso_kg=9000)
        assert resultado["ok"] is False
        assert resultado["razon"] == "seguro_invalido"

    def test_despacho_seguro_invalido_por_vigencia(self):
        almacen = Almacen(id_almacen="T2", stock={"prod-PED001": 10})
        seguros = Seguros(id_poliza="VENCIDA", vigente=False)
        coord   = CoordinadorDespacho(almacen, seguros)
        camion  = Camion(id_camion="C-T2")
        coord.registrar_camion(camion)
        resultado = camion.solicitar_despacho("PED001", peso_kg=100)
        assert resultado["ok"] is False

    def test_log_de_eventos_capturado(self, subsistema):
        coord, camion, _, _ = subsistema
        camion.solicitar_despacho("PED001", peso_kg=200)
        log = coord.get_log()
        eventos = [e["evento"] for e in log]
        assert "camion_solicita_despacho" in eventos
        assert "stock_verificado" in eventos
        assert "poliza_validada" in eventos
        assert "stock_reservado" in eventos


class TestSinMediator:

    def test_camion_sin_mediator_lanza_excepcion(self):
        camion = Camion(id_camion="SOLITARIO")
        with pytest.raises(RuntimeError, match="mediator no configurado"):
            camion.solicitar_despacho("X", 100)


class TestFactory:

    def test_factory_crea_subsistema_completo(self):
        coord, camiones = crear_subsistema_despacho()
        assert len(camiones) == 2
        assert coord is not None
        # Todos los camiones tienen mediator
        for c in camiones:
            assert c._mediator is coord
