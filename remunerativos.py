from antiguedad import calcular_antiguedad_factor
from cargos import normalizar_busqueda
from configuracion import (
    HORAS_CATEDRA_EQUIVALENTES_ASIGNACION,
    TASA_FUNCION_DOCENTE,
    TASA_TRANSFORMACION_EDUCATIVA,
    TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
)


PUNTAJE_HORA_CATEDRA_221 = 68.23224446597742


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


def _valor_hora_catedra_221(valor_indice: float, anios_antiguedad: int) -> float:
    basico = _redondear_monto(PUNTAJE_HORA_CATEDRA_221 * valor_indice)
    antiguedad = _redondear_monto(
        basico * calcular_antiguedad_factor(anios_antiguedad)
    )
    funcion_docente = _redondear_monto(basico * TASA_FUNCION_DOCENTE)
    transformacion = _redondear_monto(basico * TASA_TRANSFORMACION_EDUCATIVA)
    base_zona = basico + antiguedad + funcion_docente + transformacion
    zona = _redondear_monto(base_zona)
    return _redondear_monto(base_zona + zona)


def calcular_asignacion_hora_catedra(
    cargos_seleccionados: list[dict],
    valor_indice: float,
    anios_antiguedad: int,
) -> dict:
    horas_catedra = 0.0
    equivalentes_cargos = 0.0

    for cargo in cargos_seleccionados:
        cantidad = max(0.0, float(cargo.get("cantidad") or 0.0))
        if cantidad <= 0:
            continue
        if _es_hora_catedra(cargo):
            horas_catedra += cantidad
        else:
            equivalentes_cargos += _equivalente_cargo_simple(cargo) * cantidad

    equivalentes_cargos_computados = min(
        TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
        equivalentes_cargos,
    )
    equivalentes_disponibles_para_horas = max(
        0.0,
        TOPE_EQUIVALENTES_NO_REMUNERATIVOS - equivalentes_cargos_computados,
    )
    max_horas_computables = (
        equivalentes_disponibles_para_horas * HORAS_CATEDRA_EQUIVALENTES_ASIGNACION
    )
    horas_computadas = min(horas_catedra, max_horas_computables)
    equivalentes_horas = horas_computadas / HORAS_CATEDRA_EQUIVALENTES_ASIGNACION
    equivalente_total = min(
        TOPE_EQUIVALENTES_NO_REMUNERATIVOS,
        equivalentes_cargos_computados + equivalentes_horas,
    )

    valor_unidad = _valor_hora_catedra_221(valor_indice, anios_antiguedad)
    total = _redondear_monto(valor_unidad * equivalente_total)

    return {
        "asignacionHoraCatedra": total,
        "valorUnidad": valor_unidad,
        "equivalenteTotal": equivalente_total,
        "equivalenteCargosSimplesComputados": equivalentes_cargos_computados,
        "horasCatedraCargadas": horas_catedra,
        "horasCatedraComputadas": horas_computadas,
        "maxHorasCatedraComputables": max_horas_computables,
    }
