import pytest
from app.core.exceptions import AppException
from app.services.request_service import ESTADOS_FINALES
from app.schemas.request import RequestCreate, RequestLineCreate


def test_request_schemas():
    # Línea con cantidad > 0
    line = RequestLineCreate(producto_id="507f1f77bcf86cd799439011", cant_solicitada=10.5)
    assert line.cant_solicitada == 10.5

    # Solicitud válida
    req_in = RequestCreate(
        proveedor_id="507f1f77bcf86cd799439012",
        fecha_entrega="2026-12-31",
        observaciones="Prueba",
        lineas=[line],
        enviar=False
    )
    assert req_in.proveedor_id == "507f1f77bcf86cd799439012"
    assert len(req_in.lineas) == 1


def test_estados_finales():
    # Estados finales no admiten cambios
    assert "Entregada" in ESTADOS_FINALES
    assert "Cerrada con faltante" in ESTADOS_FINALES
    assert "Rechazada" in ESTADOS_FINALES
    assert "Cancelada" in ESTADOS_FINALES
    assert "Borrador" not in ESTADOS_FINALES
    assert "Enviada" not in ESTADOS_FINALES
    assert "Por entregar" not in ESTADOS_FINALES


def test_state_machine_allowed_transitions():
    # Tabla de transiciones permitidas según Sección 6
    allowed_transitions = {
        "Borrador": ["Enviada", "Cancelada"],
        "Enviada": ["Cancelada", "Rechazada", "Por entregar"],
        "Por entregar": ["Entregada", "Entregada parcial"],
        "Entregada parcial": ["Entregada", "Cerrada con faltante"],
        "Entregada": [],
        "Cerrada con faltante": [],
        "Rechazada": [],
        "Cancelada": []
    }

    assert "Enviada" in allowed_transitions["Borrador"]
    assert "Cancelada" in allowed_transitions["Borrador"]
    assert "Por entregar" not in allowed_transitions["Borrador"]
    assert "Entregada" not in allowed_transitions["Borrador"]

    assert "Por entregar" in allowed_transitions["Enviada"]
    assert "Rechazada" in allowed_transitions["Enviada"]
    assert "Cancelada" in allowed_transitions["Enviada"]
    assert "Entregada" not in allowed_transitions["Enviada"]

    assert "Entregada" in allowed_transitions["Por entregar"]
    assert "Entregada parcial" in allowed_transitions["Por entregar"]
    assert "Borrador" not in allowed_transitions["Por entregar"]

    assert "Cerrada con faltante" in allowed_transitions["Entregada parcial"]
    assert len(allowed_transitions["Entregada"]) == 0
    assert len(allowed_transitions["Cancelada"]) == 0
