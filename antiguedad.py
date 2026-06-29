
from configuracion import TABLA_ANTIGUEDAD


def calcular_antiguedad_factor(anios_servicio: int) -> float:
    """Devuelve el porcentaje de antiguedad como factor decimal."""
    anios = max(0, int(anios_servicio or 0))
    for tramo in TABLA_ANTIGUEDAD:
        if tramo["desde"] <= anios <= tramo["hasta"]:
            return float(tramo["porcentaje"])
    return float(TABLA_ANTIGUEDAD[-1]["porcentaje"])
