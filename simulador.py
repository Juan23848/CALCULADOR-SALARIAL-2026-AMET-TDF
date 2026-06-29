from typing import Dict, List

from salario import calcular_salario


def calcular_simulacion(
    cargos: List[str],
    cantidades: List[int],
    puntajes_dict: Dict[str, float],
    vi: float,
    antiguedad: int,
    gremios: List[str] | None = None,
    no_remunerativos: float = 0.0,
    otros_remunerativos: float = 0.0,
    descuento_adicional_porcentaje: float = 0.0,
    descuento_adicional_fijo: float = 0.0,
) -> Dict:
    cargos_seleccionados = []
    for cargo, cantidad in zip(cargos, cantidades):
        if cargo and (cantidad or 0) > 0:
            cargos_seleccionados.append(
                {
                    "codigoCargo": str(cargo).split(" - ", 1)[0],
                    "descripcion": str(cargo),
                    "puntajeCargo": puntajes_dict.get(cargo),
                    "cantidad": int(cantidad),
                    "esHoraCatedra": "hora" in str(cargo).lower(),
                }
            )

    return calcular_salario(
        cargos_seleccionados,
        vi,
        antiguedad,
        no_remunerativos=no_remunerativos,
        otros_remunerativos=otros_remunerativos,
        descuento_adicional_porcentaje=descuento_adicional_porcentaje,
        descuento_adicional_fijo=descuento_adicional_fijo,
    )


def aplicar_aumentos_compuestos(valor_inicial: float, porcentajes: list[float]) -> float:
    valor = float(valor_inicial)
    for porcentaje in porcentajes:
        valor *= 1 + float(porcentaje)
    return valor


def comparar_resultados(actual: dict, propuesto: dict) -> dict:
    neto_actual = actual["netoFinal"]
    neto_propuesto = propuesto["netoFinal"]
    diferencia = neto_propuesto - neto_actual
    diferencia_porcentual = diferencia / neto_actual if neto_actual else 0.0
    return {
        "netoActual": neto_actual,
        "netoPropuesto": neto_propuesto,
        "diferenciaPesos": diferencia,
        "diferenciaPorcentual": diferencia_porcentual,
    }


def comparar_con_canasta(neto: float, canasta_basica: float) -> dict:
    canasta = float(canasta_basica or 0.0)
    diferencia = float(neto or 0.0) - canasta
    cobertura = float(neto or 0.0) / canasta if canasta > 0 else 0.0
    return {
        "neto": float(neto or 0.0),
        "canastaBasica": canasta,
        "diferencia": diferencia,
        "cobertura": cobertura,
        "montoFaltante": max(0.0, -diferencia),
    }
