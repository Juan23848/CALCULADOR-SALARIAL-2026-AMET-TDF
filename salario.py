from antiguedad import calcular_antiguedad_factor
from configuracion import (
    INCLUIR_ADICIONAL_JERARQUICO_EN_ZONA,
    INCLUIR_BONIFICACION_DOCENTE_EN_ZONA,
    INCLUIR_TRANSFORMACION_EN_ZONA,
    TASA_FUNCION_DOCENTE,
    TASA_TRANSFORMACION_EDUCATIVA,
    TASA_ZONA,
)
from descuentos import descuento_sindical, descuentos_adicionales, descuentos_legales
from no_remunerativos import calcular_no_remunerativos
from remunerativos import calcular_asignacion_hora_catedra


def _redondear_monto(valor: float) -> float:
    return round(float(valor or 0.0) + 0.000000001, 2)


def _validar_cargo(item: dict) -> tuple[str, str, float, float]:
    codigo = str(item.get("codigoCargo") or item.get("codigo") or "").strip()
    descripcion = str(item.get("descripcion") or item.get("cargo") or "").strip()
    puntaje = item.get("puntajeCargo", item.get("puntaje"))
    cantidad = item.get("cantidad", 1)

    if not codigo:
        raise ValueError("Falta el codigo del cargo seleccionado.")
    if puntaje is None or float(puntaje) <= 0:
        raise ValueError(
            "No se encontro puntaje asociado al codigo seleccionado. "
            "Revise la tabla de cargos."
        )
    if float(cantidad or 0) <= 0:
        raise ValueError("La cantidad debe ser mayor a cero.")

    return codigo, descripcion, float(puntaje), float(cantidad)


def calcular_componentes(
    cargos_seleccionados: list[dict],
    valor_indice: float,
    anios_antiguedad: int,
    tasa_zona: float = TASA_ZONA,
) -> dict:
    if valor_indice <= 0:
        raise ValueError("El Valor Indice debe ser mayor a cero.")
    if float(tasa_zona or 0.0) < 0:
        raise ValueError("El porcentaje de zona no puede ser negativo.")

    tasa_zona = float(tasa_zona or 0.0)

    total_puntaje = 0.0
    total_horas = 0.0
    total_cargos = 0.0
    basico = 0.0
    antiguedad = 0.0
    funcion_docente = 0.0
    transformacion_educativa = 0.0
    bonificacion_docente = 0.0
    adicional_jerarquico = 0.0
    base_zona = 0.0
    zona = 0.0
    detalle = []
    porcentaje_antiguedad = calcular_antiguedad_factor(anios_antiguedad)

    for item in cargos_seleccionados:
        codigo, descripcion, puntaje_cargo, cantidad = _validar_cargo(item)
        es_hora = bool(item.get("esHoraCatedra")) or "hora" in descripcion.lower()
        puntaje_total = puntaje_cargo * cantidad
        basico_item = _redondear_monto(puntaje_total * valor_indice)
        antiguedad_item = _redondear_monto(basico_item * porcentaje_antiguedad)
        funcion_item = _redondear_monto(basico_item * TASA_FUNCION_DOCENTE)
        transformacion_item = _redondear_monto(
            basico_item * TASA_TRANSFORMACION_EDUCATIVA
        )
        bonif_porcentaje = float(item.get("bonificacionDocentePorcentaje") or 0.0)
        bonif_fija = float(item.get("bonificacionDocenteMonto") or 0.0)
        base_bonificacion_item = basico_item + antiguedad_item
        bonificacion_item = _redondear_monto(
            base_bonificacion_item * bonif_porcentaje + bonif_fija
        )
        jerarquico_porcentaje = float(item.get("adicionalJerarquicoPorcentaje") or 0.0)
        jerarquico_item = _redondear_monto(basico_item * jerarquico_porcentaje)
        base_zona_item = basico_item + antiguedad_item + funcion_item
        if INCLUIR_TRANSFORMACION_EN_ZONA:
            base_zona_item += transformacion_item
        if INCLUIR_BONIFICACION_DOCENTE_EN_ZONA:
            base_zona_item += bonificacion_item
        if INCLUIR_ADICIONAL_JERARQUICO_EN_ZONA:
            base_zona_item += jerarquico_item
        zona_item = _redondear_monto(base_zona_item * tasa_zona)

        total_puntaje += puntaje_total
        basico += basico_item
        antiguedad += antiguedad_item
        funcion_docente += funcion_item
        transformacion_educativa += transformacion_item
        bonificacion_docente += bonificacion_item
        adicional_jerarquico += jerarquico_item
        base_zona += base_zona_item
        zona += zona_item

        if es_hora:
            total_horas += cantidad
        else:
            total_cargos += cantidad

        detalle.append(
            {
                "codigoCargo": codigo,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "puntajeCargo": puntaje_cargo,
                "puntajeTotal": puntaje_total,
                "valorIndice": valor_indice,
                "basico": basico_item,
                "antiguedad": antiguedad_item,
                "funcionDocente": funcion_item,
                "transformacionEducativa": transformacion_item,
                "bonificacionDocente": bonificacion_item,
                "adicionalJerarquico": jerarquico_item,
                "zona": zona_item,
                "esHoraCatedra": es_hora,
            }
        )

    if total_puntaje <= 0:
        raise ValueError("Seleccione al menos un cargo u hora catedra con puntaje valido.")

    bruto_remunerativo = (
        basico
        + antiguedad
        + funcion_docente
        + zona
        + transformacion_educativa
        + bonificacion_docente
        + adicional_jerarquico
    )

    return {
        "detalle": detalle,
        "totalPuntaje": total_puntaje,
        "totalHoras": total_horas,
        "totalCargos": total_cargos,
        "basico": basico,
        "porcentajeAntiguedad": porcentaje_antiguedad,
        "antiguedad": antiguedad,
        "funcionDocente": funcion_docente,
        "bonificacionDocente": bonificacion_docente,
        "adicionalJerarquico": adicional_jerarquico,
        "transformacionEducativa": transformacion_educativa,
        "baseZona": base_zona,
        "tasaZona": tasa_zona,
        "zona": zona,
        "brutoRemunerativo": bruto_remunerativo,
    }


def calcular_salario(
    cargos_seleccionados: list[dict],
    valor_indice: float,
    anios_antiguedad: int,
    no_remunerativos: float = 0.0,
    otros_remunerativos: float = 0.0,
    descuento_adicional_porcentaje: float = 0.0,
    descuento_adicional_fijo: float = 0.0,
    incluir_jubilacion: bool = True,
    incluir_obra_social: bool = True,
    tasa_obra_social: float = 0.03,
    tasa_zona: float = TASA_ZONA,
    incluir_no_remunerativos_automaticos: bool = False,
    incluir_asignacion_hora_catedra: bool = False,
    sindicatos: list[str] | None = None,
) -> dict:
    componentes = calcular_componentes(
        cargos_seleccionados,
        valor_indice,
        anios_antiguedad,
        tasa_zona=tasa_zona,
    )

    otros_rem = max(0.0, float(otros_remunerativos or 0.0))
    detalle_asignacion = calcular_asignacion_hora_catedra(
        cargos_seleccionados,
        valor_indice,
        anios_antiguedad,
    )
    asignacion_hora_catedra = (
        detalle_asignacion["asignacionHoraCatedra"]
        if incluir_asignacion_hora_catedra
        else 0.0
    )
    remunerativos_automaticos = asignacion_hora_catedra
    bruto = componentes["brutoRemunerativo"] + otros_rem + remunerativos_automaticos
    otros_no_rem = max(0.0, float(no_remunerativos or 0.0))
    detalle_no_rem_auto = calcular_no_remunerativos(cargos_seleccionados)
    no_rem_auto = (
        detalle_no_rem_auto["total"]
        if incluir_no_remunerativos_automaticos
        else 0.0
    )
    foid_base_sindical = (
        detalle_no_rem_auto["foid"]
        if incluir_no_remunerativos_automaticos
        else 0.0
    )
    legales = descuentos_legales(
        bruto,
        incluir_jubilacion,
        incluir_obra_social,
        tasa_obra_social,
    )
    sindicales = descuento_sindical(bruto, foid_base_sindical, sindicatos)
    adicionales = descuentos_adicionales(
        bruto,
        descuento_adicional_porcentaje,
        descuento_adicional_fijo,
    )

    descuentos_totales = legales["total"] + sindicales["total"] + adicionales["total"]
    neto_sin_no_remunerativos = bruto - descuentos_totales
    no_rem = otros_no_rem + no_rem_auto
    neto_final = neto_sin_no_remunerativos + no_rem

    return {
        "componentes": componentes,
        "brutoRemunerativo": bruto,
        "remunerativosAutomaticos": remunerativos_automaticos,
        "asignacionHoraCatedra": asignacion_hora_catedra,
        "asignacionHoraCatedraDetalle": detalle_asignacion,
        "otrosRemunerativos": otros_rem,
        "descuentosLegales": legales,
        "descuentosSindicales": sindicales,
        "descuentosAdicionales": adicionales,
        "descuentosTotales": descuentos_totales,
        "netoSinNoRemunerativos": neto_sin_no_remunerativos,
        "noRemunerativosAutomaticos": no_rem_auto,
        "noRemunerativosAutomaticosDetalle": detalle_no_rem_auto,
        "otrosNoRemunerativos": otros_no_rem,
        "noRemunerativos": no_rem,
        "netoFinal": neto_final,
    }
