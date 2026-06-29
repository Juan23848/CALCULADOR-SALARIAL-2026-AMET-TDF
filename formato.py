def parse_decimal(valor, nombre_campo: str = "valor") -> float:
    """Acepta coma o punto decimal sin perder precision de entrada."""
    if valor is None:
        raise ValueError(f"{nombre_campo} es obligatorio.")

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    if not texto:
        raise ValueError(f"{nombre_campo} es obligatorio.")

    texto = texto.replace("$", "").replace("%", "").replace(" ", "")
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError as exc:
        raise ValueError(f"{nombre_campo} debe ser numerico.") from exc


def parse_porcentajes_acumulados(texto: str) -> list[float]:
    if not texto or not texto.strip():
        return []

    partes = texto.replace("\n", ";").replace("+", ";").split(";")
    porcentajes = []
    for parte in partes:
        limpia = parte.strip()
        if not limpia:
            continue
        porcentajes.append(parse_decimal(limpia, "porcentaje de aumento") / 100)
    return porcentajes


def moneda(valor: float) -> str:
    numero = f"{float(valor or 0):,.2f}"
    numero = numero.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {numero}"


def porcentaje(valor: float) -> str:
    numero = f"{float(valor or 0) * 100:.2f}".replace(".", ",")
    return f"{numero}%"
