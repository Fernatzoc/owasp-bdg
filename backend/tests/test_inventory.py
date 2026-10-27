import pytest
from app.schemas.request import RequestLineReceive, RequestReceiveRequest


def test_receive_schema_validation():
    # Línea recibida válida
    line_ok = RequestLineReceive(
        producto_id="507f1f77bcf86cd799439011",
        recibido=True,
        cant_recibida=5.0,
        motivo=None
    )
    assert line_ok.cant_recibida == 5.0
    assert line_ok.recibido is True

    # Solicitud de recepción
    req_receive = RequestReceiveRequest(
        lineas=[line_ok],
        comentario="Lote completo"
    )
    assert len(req_receive.lineas) == 1
    assert req_receive.comentario == "Lote completo"


def test_reception_status_determination():
    # Simular lógica de cálculo de estado según cantidades recibidas vs confirmadas
    def calcular_estado(confirmadas, recibidas):
        total_conf = sum(confirmadas)
        total_rec = sum(recibidas)
        return "Entregada" if total_rec >= total_conf else "Entregada parcial"

    assert calcular_estado([10, 20], [10, 20]) == "Entregada"
    assert calcular_estado([10, 20], [10, 15]) == "Entregada parcial"
    assert calcular_estado([10, 20], [0, 0]) == "Entregada parcial"
