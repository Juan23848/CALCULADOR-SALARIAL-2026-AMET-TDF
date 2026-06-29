from configuracion import (
    MONTO_SEGURO_VIDA_OBLIGATORIO,
    TASA_JUBILACION,
    TASA_OBRA_SOCIAL,
)


SINDICATOS = {
    "AMET": {"remunerativo": 0.015, "foid": 0.015},
    "ATE": {"remunerativo": 0.022, "foid": 0.0},
    "SUTEF": {"remunerativo": 0.02, "foid": 0.02},
    "UDA": {"remunerativo": 0.015, "foid": 0.015},
    "UDAF": {"remunerativo": 0.013, "foid": 0.013},
    "OTROS": {"remunerativo": 0.02, "foid": 0.02},
}


def descuentos_legales(
    bruto_remunerativo: float,
    incluir_jubilacion: bool = True,
    incluir_obra_social: bool = True,
    tasa_obra_social: float = TASA_OBRA_SOCIAL,
) -> dict:
    jubilacion = bruto_remunerativo * TASA_JUBILACION if incluir_jubilacion else 0.0
    obra_social = (
        bruto_remunerativo * float(tasa_obra_social or 0.0)
        if incluir_obra_social
        else 0.0
    )
    seguro_vida = MONTO_SEGURO_VIDA_OBLIGATORIO
    total = jubilacion + obra_social + seguro_vida
    return {
        "jubilacion": jubilacion,
        "obra_social": obra_social,
        "osef": obra_social,
        "seguro_vida": seguro_vida,
        "total": total,
        "tasa_jubilacion": TASA_JUBILACION if incluir_jubilacion else 0.0,
        "tasa_obra_social": float(tasa_obra_social or 0.0)
        if incluir_obra_social
        else 0.0,
        "tasa_total": (TASA_JUBILACION if incluir_jubilacion else 0.0)
        + (float(tasa_obra_social or 0.0) if incluir_obra_social else 0.0),
    }


def descuentos_adicionales(
    bruto_remunerativo: float,
    porcentaje: float = 0.0,
    monto_fijo: float = 0.0,
) -> dict:
    porcentaje = max(0.0, float(porcentaje or 0.0))
    monto_fijo = max(0.0, float(monto_fijo or 0.0))
    monto_porcentual = bruto_remunerativo * porcentaje
    total = monto_porcentual + monto_fijo
    return {
        "porcentaje": porcentaje,
        "monto_porcentual": monto_porcentual,
        "monto_fijo": monto_fijo,
        "total": total,
    }


def descuento_sindical(
    bruto_remunerativo: float,
    monto_foid: float,
    sindicatos: list[str] | None = None,
) -> dict:
    vistos, unicos = set(), []
    for sindicato in sindicatos or []:
        sindicato = str(sindicato or "").strip().upper()
        if sindicato in SINDICATOS and sindicato not in vistos:
            unicos.append(sindicato)
            vistos.add(sindicato)

    detalle = []
    total_remunerativo = 0.0
    total_foid = 0.0
    bruto_remunerativo = max(0.0, float(bruto_remunerativo or 0.0))
    monto_foid = max(0.0, float(monto_foid or 0.0))

    for sindicato in unicos:
        tasas = SINDICATOS[sindicato]
        monto_remunerativo = bruto_remunerativo * tasas["remunerativo"]
        monto_foid_sindicato = monto_foid * tasas["foid"]
        total_remunerativo += monto_remunerativo
        total_foid += monto_foid_sindicato
        detalle.append(
            {
                "sindicato": sindicato,
                "tasa_remunerativo": tasas["remunerativo"],
                "tasa_foid": tasas["foid"],
                "monto_remunerativo": monto_remunerativo,
                "monto_foid": monto_foid_sindicato,
                "total": monto_remunerativo + monto_foid_sindicato,
            }
        )

    return {
        "sindicatos": unicos,
        "base_remunerativo": bruto_remunerativo,
        "base_foid": monto_foid,
        "tasa_remunerativo_total": sum(
            SINDICATOS[sindicato]["remunerativo"] for sindicato in unicos
        ),
        "tasa_foid_total": sum(SINDICATOS[sindicato]["foid"] for sindicato in unicos),
        "monto_remunerativo": total_remunerativo,
        "monto_foid": total_foid,
        "total": total_remunerativo + total_foid,
        "detalle": detalle,
    }


def descuento_gremial_foid(monto_foid: float, gremios: list[str]) -> dict:
    calculo = descuento_sindical(0.0, monto_foid, gremios)
    return {
        "gremios": calculo["sindicatos"],
        "tasa_total": calculo["tasa_foid_total"],
        "base_foid": calculo["base_foid"],
        "total": calculo["monto_foid"],
    }
