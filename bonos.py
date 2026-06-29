
FOID_POR_19HS = 45000.0  # por cargo simple
CONECTIVIDAD_TOTAL = 142600.0

def unidades_bono(simples: int, completos: int, total_horas: int) -> int:
    return min(38, max(0, int(simples) + 2 * int(completos)))

def foid(simples: int, completos: int, total_horas: int) -> float:
    unidades_cargo = simples + 2 * completos
    if unidades_cargo > 0:
        return min(unidades_cargo, 2) * 45000.0
    if total_horas > 0:
        return min(total_horas * 3000.0, 90000.0)
    return 0.0

def conectividad(unidades: int, conect_total: float = CONECTIVIDAD_TOTAL) -> float:
    unidades = min(38, max(0, int(unidades)))
    return conect_total * (unidades / 38.0)
