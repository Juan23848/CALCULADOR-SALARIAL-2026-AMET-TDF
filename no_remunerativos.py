from cargos import normalizar_busqueda
from configuracion import (
    HORAS_CATEDRA_EQUIVALENTES_CARGO_SIMPLE,
    MONTO_FOID_CARGO_SIMPLE,
    MONTO_MATERIAL_DIDACTICO_CARGO_SIMPLE,
    TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
)


def _redondear_monto(valor: float) -> float:
    return round(float(valor or 0.0) + 0.000000001, 2)


def _es_hora_catedra(cargo: dict) -> bool:
    descripcion = normalizar_busqueda(cargo.get("descripcion", ""))
    return bool(cargo.get("esHoraCatedra")) or (
        "hora" in descripcion and "catedra" in descripcion
    )


def _equivalente_cargo_simple(cargo: dict) -> float:
    descripcion = normalizar_busqueda(cargo.get("descripcion", ""))
    if "t c" in descripcion or "jornada completa" in descripcion:
        return 2.0
    return 1.0


def calcular_no_remunerativos(cargos_seleccionados: list[dict]) -> dict:
    horas_catedra = 0.0
    equivalentes_cargos = 0.0
    detalle = []

    for cargo in cargos_seleccionados:
        cantidad = max(0.0, float(cargo.get("cantidad") or 0.0))
        if cantidad <= 0:
            continue

        if _es_hora_catedra(cargo):
            horas_catedra += cantidad
            detalle.append(
                {
                    "codigoCargo": cargo.get("codigoCargo"),
                    "descripcion": cargo.get("descripcion"),
                    "cantidad": cantidad,
                    "tipoNoRemunerativo": "hora_catedra",
                    "equivalenteCargoSimple": 0.0,
                }
            )
            continue

        equivalente_unitario = _equivalente_cargo_simple(cargo)
        equivalente_total = equivalente_unitario * cantidad
        equivalentes_cargos += equivalente_total
        detalle.append(
            {
                "codigoCargo": cargo.get("codigoCargo"),
                "descripcion": cargo.get("descripcion"),
                "cantidad": cantidad,
                "tipoNoRemunerativo": (
                    "jornada_completa"
                    if equivalente_unitario == 2.0
                    else "jornada_simple"
                ),
                "equivalenteCargoSimple": equivalente_total,
            }
        )

    equivalentes_cargos_computados = min(
        TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
        equivalentes_cargos,
    )
    equivalentes_disponibles_para_horas = max(
        0.0,
        TOPE_EQUIVALENTES_NO_REMUNERATIVOS - equivalentes_cargos_computados,
    )
    max_horas_computables = (
        equivalentes_disponibles_para_horas * HORAS_CATEDRA_EQUIVALENTES_CARGO_SIMPLE
    )
    horas_computadas = min(horas_catedra, max_horas_computables)
    equivalentes_horas = horas_computadas / HORAS_CATEDRA_EQUIVALENTES_CARGO_SIMPLE
    equivalente_total = min(
        TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
        equivalentes_cargos_computados + equivalentes_horas,
    )

    foid = _redondear_monto(MONTO_FOID_CARGO_SIMPLE * equivalente_total)
    material = _redondear_monto(MONTO_MATERIAL_DIDACTICO_CARGO_SIMPLE * equivalente_total)
    total = _redondear_monto(foid + material)

    return {
        "foid": foid,
        "materialDidactico": material,
        "total": total,
        "equivalenteTotal": equivalente_total,
        "equivalenteCargosSimplesCargados": equivalentes_cargos,
        "equivalenteCargosSimplesComputados": equivalentes_cargos_computados,
        "horasCatedraCargadas": horas_catedra,
        "horasCatedraComputadas": horas_computadas,
        "maxHorasCatedraComputables": max_horas_computables,
        "topeEquivalentes": TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
        "detalle": detalle,
    }
