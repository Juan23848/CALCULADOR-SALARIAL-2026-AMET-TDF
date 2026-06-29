VALORES_INDICE_REFERENCIA = {
    "Mayo 2026 recibos": 95.72248503794604,
}

TASA_FUNCION_DOCENTE = 2.30
TASA_TRANSFORMACION_EDUCATIVA = 1.23
TASA_ZONA = 1.00
TASA_BONIFICACION_DOCENTE_REFERENCIA = 0.2775
TASA_ADICIONAL_JERARQUICO_REFERENCIA = 0.55
MONTO_FOID_CARGO_SIMPLE = 56000.00
MONTO_MATERIAL_DIDACTICO_CARGO_SIMPLE = 71300.00
MONTO_SEGURO_VIDA_OBLIGATORIO = 2750.00
HORAS_CATEDRA_EQUIVALENTES_CARGO_SIMPLE = 19.0
HORAS_CATEDRA_EQUIVALENTES_ASIGNACION = 21.0
TOPE_EQUIVALENTES_NO_REMUNERATIVOS = 2.0

BONIFICACION_DOCENTE_PORCENTAJE_POR_CODIGO_ZONA = {
    ("421", "Tolhuin"): 0.2325,
}

ZONAS_REFERENCIA = {
    "Ushuaia": 1.00,
    "Tolhuin": 1.20,
    "Rio Grande": 1.00,
    "Escuelas Rurales": 1.20,
}

DETALLE_ZONAS_REFERENCIA = {
    "Ushuaia": "Zona 100%",
    "Tolhuin": "Zona 120%",
    "Rio Grande": "Zona 100%",
    "Escuelas Rurales": (
        "Zona 120%: Estancia Sara, Lago Escondido, San Sebastian, "
        "Puerto Almanza y Escuela Antartica Nro. 38"
    ),
}

# Codigos tomados de la planilla "COD. CARGOS Y HORAS QUE LIQUIDAN
# BONIFICACION.xlsx". Se usa lista exacta para no bonificar todo el rango
# 301-499 indiscriminadamente.
BONIFICACION_DOCENTE_CODIGOS = {
    "120",
    "215",
    "301",
    "302",
    "303",
    "310",
    "312",
    "314",
    "315",
    "316",
    "401",
    "402",
    "403",
    "404",
    "405",
    "408",
    "411",
    "415",
    "418",
    "419",
    "420",
    "421",
    "422",
    "451",
    "452",
    "453",
    "455",
    "456",
    "457",
    "816",
    "844",
}

BONIFICACION_DOCENTE_CODIGOS_CONTEXTO = set()
BONIFICACION_DOCENTE_CODIGOS_EXTRA = set()
BONIFICACION_DOCENTE_CODIGOS_EXCLUIR = set()

# Adicional jerarquico: codigos del Anexo I de la Resolucion M.Ed. 2001/16.
ADICIONAL_JERARQUICO_CODIGOS_RESOLUCION_2001_16 = {
    "101",
    "102",
    "103",
    "104",
    "105",
    "106",
    "107",
    "200",
    "201",
    "202",
    "203",
    "204",
    "205",
    "206",
    "207",
    "208",
    "209",
    "210",
    "211",
    "300",
    "301",
    "302",
    "303",
    "400",
    "401",
    "402",
    "403",
    "404",
    "405",
    "406",
    "407",
    "408",
    "500",
    "501",
    "502",
    "511",
    "512",
    "513",
    "600",
    "601",
    "602",
    "700",
    "800",
    "801",
    "802",
    "803",
    "804",
    "805",
    "806",
    "807",
    "808",
    "809",
    "810",
    "811",
    "812",
    "813",
    "814",
    "815",
    "816",
    "817",
    "818",
    "819",
    "820",
    "821",
    "822",
    "823",
    "824",
    "825",
    "826",
    "827",
    "828",
    "837",
    "838",
    "861",
    "862",
    "863",
    "864",
    "900",
    "901",
    "902",
    "905",
    "906",
    "949",
    "950",
    "951",
    "952",
    "953",
    "954",
}
ADICIONAL_JERARQUICO_CODIGOS_EXTRA = set()
ADICIONAL_JERARQUICO_CODIGOS_EXCLUIR = set()

ADICIONAL_JERARQUICO_PORCENTAJE_POR_CODIGO = {}

TASA_JUBILACION = 0.16
TASA_OBRA_SOCIAL = 0.03

INCLUIR_TRANSFORMACION_EN_ZONA = True
INCLUIR_BONIFICACION_DOCENTE_EN_ZONA = True
INCLUIR_ADICIONAL_JERARQUICO_EN_ZONA = True

TABLA_ANTIGUEDAD = [
    {"desde": 0, "hasta": 0, "porcentaje": 0.00},
    {"desde": 1, "hasta": 3, "porcentaje": 0.40},
    {"desde": 4, "hasta": 6, "porcentaje": 0.45},
    {"desde": 7, "hasta": 9, "porcentaje": 0.55},
    {"desde": 10, "hasta": 12, "porcentaje": 0.70},
    {"desde": 13, "hasta": 15, "porcentaje": 0.85},
    {"desde": 16, "hasta": 17, "porcentaje": 0.95},
    {"desde": 18, "hasta": 19, "porcentaje": 1.00},
    {"desde": 20, "hasta": 21, "porcentaje": 1.10},
    {"desde": 22, "hasta": 23, "porcentaje": 1.20},
    {"desde": 24, "hasta": 24, "porcentaje": 1.30},
    {"desde": 25, "hasta": 99, "porcentaje": 1.35},
]
