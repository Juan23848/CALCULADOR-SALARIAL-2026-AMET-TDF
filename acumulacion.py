from cargos import normalizar_busqueda


NIVELES_EXCEPCION = {
    "Sin excepcion": 0,
    "Primera excepcion Art. 7": 1,
    "Segunda excepcion Art. 7": 2,
}

TOPES_HORAS = {
    0: {
        "solo_horas": 42,
        "un_simple": 22,
        "dos_simples": 6,
        "un_completo": 16,
    },
    1: {
        "solo_horas": 48,
        "un_simple": 28,
        "dos_simples": 12,
        "un_completo": 22,
    },
    2: {
        "solo_horas": 54,
        "un_simple": 34,
        "dos_simples": 18,
        "un_completo": 28,
    },
}


def clasificar_cargo(cargo: dict) -> str:
    descripcion = normalizar_busqueda(cargo.get("descripcion", ""))
    if cargo.get("esHoraCatedra") or "hora catedra" in descripcion:
        return "hora_catedra"

    directivo = [
        "supervisor",
        "director",
        "dir",
        "vicedir",
        "vice",
        "rector",
        "regente",
        "secretario",
        "sec",
    ]
    if any(palabra in descripcion for palabra in directivo):
        return "directivo_jerarquico"

    if "t c" in descripcion or "jornada completa" in descripcion:
        return "jornada_completa"

    return "jornada_simple"


def _tope_por_combinacion(simples: float, completos: float, nivel_excepcion: int) -> tuple[int, str]:
    topes = TOPES_HORAS[nivel_excepcion]
    if completos > 0:
        return topes["un_completo"], "un cargo de jornada completa"
    if simples >= 2:
        return topes["dos_simples"], "dos cargos de jornada simple"
    if simples == 1:
        return topes["un_simple"], "un cargo de jornada simple"
    return topes["solo_horas"], "solo horas catedra"


def evaluar_acumulacion(cargos_seleccionados: list[dict], nivel_excepcion: int = 0) -> dict:
    nivel = max(0, min(2, int(nivel_excepcion or 0)))
    resumen = {
        "horasCatedra": 0.0,
        "jornadaSimple": 0.0,
        "jornadaCompleta": 0.0,
        "directivosJerarquicos": 0.0,
    }
    detalle = []

    for cargo in cargos_seleccionados:
        cantidad = float(cargo.get("cantidad") or 0)
        tipo = clasificar_cargo(cargo)
        if tipo == "hora_catedra":
            resumen["horasCatedra"] += cantidad
        elif tipo == "jornada_completa":
            resumen["jornadaCompleta"] += cantidad
        elif tipo == "directivo_jerarquico":
            resumen["directivosJerarquicos"] += cantidad
        else:
            resumen["jornadaSimple"] += cantidad

        detalle.append(
            {
                "codigoCargo": cargo.get("codigoCargo"),
                "descripcion": cargo.get("descripcion"),
                "cantidad": cantidad,
                "tipoLey761": tipo,
            }
        )

    advertencias = []
    articulos = []
    horas = resumen["horasCatedra"]
    simples = resumen["jornadaSimple"]
    completos = resumen["jornadaCompleta"]
    directivos = resumen["directivosJerarquicos"]

    if directivos > 1:
        advertencias.append(
            "La ley indica incompatibilidad entre cargos directivos o jerarquicos "
            "entre si. Revisar Art. 4."
        )
        articulos.append("Art. 4")

    if directivos >= 1 and (horas > 0 or simples > 0 or completos > 0):
        advertencias.append(
            "Hay cargo directivo/jerarquico junto con otros cargos u horas. "
            "El simulador no conoce establecimientos ni horarios; revisar Art. 10 y declaracion jurada."
        )
        articulos.extend(["Art. 10", "Art. 16"])

    if simples > 2:
        advertencias.append("El regimen comun contempla hasta dos cargos de jornada simple.")
        articulos.append("Art. 5")

    if completos > 1:
        advertencias.append("El regimen comun contempla hasta un cargo de jornada completa.")
        articulos.append("Art. 5")

    if simples > 0 and completos > 0:
        advertencias.append(
            "La combinacion de jornada simple y jornada completa no aparece como caso "
            "expreso en el Art. 5. Verificar compatibilidad."
        )
        articulos.append("Art. 5")

    max_horas, combinacion = _tope_por_combinacion(simples, completos, nivel)
    if horas > max_horas:
        etiqueta = ["regimen comun", "primera excepcion", "segunda excepcion"][nivel]
        advertencias.append(
            f"Para {combinacion}, el tope de {etiqueta} es {max_horas:g} horas catedra. "
            f"Se cargaron {horas:g}."
        )
        articulos.append("Art. 5" if nivel == 0 else "Art. 7")

    if nivel > 0:
        advertencias.append(
            "Se esta considerando una excepcion del Art. 7. Debe existir acto publico "
            "y necesidad de cobertura, hasta la finalizacion del ciclo escolar."
        )
        articulos.append("Art. 7")

    articulos = sorted(set(articulos))
    return {
        "estado": "ok" if not advertencias else "advertencia",
        "resumen": resumen,
        "detalle": detalle,
        "maxHorasPermitidas": max_horas,
        "combinacionEvaluada": combinacion,
        "nivelExcepcion": nivel,
        "advertencias": advertencias,
        "articulos": articulos,
    }
