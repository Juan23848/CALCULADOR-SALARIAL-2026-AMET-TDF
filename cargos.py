from __future__ import annotations

import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from configuracion import (
    ADICIONAL_JERARQUICO_CODIGOS_EXCLUIR,
    ADICIONAL_JERARQUICO_CODIGOS_EXTRA,
    ADICIONAL_JERARQUICO_CODIGOS_RESOLUCION_2001_16,
    ADICIONAL_JERARQUICO_PORCENTAJE_POR_CODIGO,
    BONIFICACION_DOCENTE_CODIGOS,
    BONIFICACION_DOCENTE_CODIGOS_EXCLUIR,
    BONIFICACION_DOCENTE_CODIGOS_EXTRA,
    BONIFICACION_DOCENTE_PORCENTAJE_POR_CODIGO_ZONA,
    TASA_ADICIONAL_JERARQUICO_REFERENCIA,
    TASA_BONIFICACION_DOCENTE_REFERENCIA,
)
from formato import parse_decimal


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _leer_xml_xlsx(archivo: Path, nombre: str) -> ET.Element:
    with zipfile.ZipFile(archivo) as paquete:
        with paquete.open(nombre) as entrada:
            return ET.fromstring(entrada.read())


def _shared_strings(archivo: Path) -> list[str]:
    try:
        root = _leer_xml_xlsx(archivo, "xl/sharedStrings.xml")
    except KeyError:
        return []

    valores = []
    for item in root.findall("x:si", NS):
        partes = [texto.text or "" for texto in item.findall(".//x:t", NS)]
        valores.append("".join(partes))
    return valores


def _valor_celda(celda: ET.Element, shared: list[str]) -> str:
    valor = celda.find("x:v", NS)
    if valor is None:
        return ""
    texto = valor.text or ""
    if celda.attrib.get("t") == "s" and texto:
        return shared[int(texto)]
    return texto


def cargar_cargos_desde_xlsx(ruta: str | Path = "cargos_mayo_2025.xlsx") -> list[dict]:
    archivo = Path(ruta)
    if not archivo.exists():
        raise FileNotFoundError(f"No se encontro la tabla de cargos: {archivo}")

    shared = _shared_strings(archivo)
    sheet = _leer_xml_xlsx(archivo, "xl/worksheets/sheet1.xml")
    filas = []

    for fila in sheet.findall(".//x:sheetData/x:row", NS):
        valores = {}
        for celda in fila.findall("x:c", NS):
            columna = "".join(filter(str.isalpha, celda.attrib.get("r", ""))).upper()
            valores[columna] = _valor_celda(celda, shared).strip()
        filas.append(valores)

    cargos = []
    for fila in filas[1:]:
        codigo = fila.get("A", "").strip()
        descripcion = fila.get("B", "").strip()
        puntaje_texto = fila.get("C", "").strip()

        if not codigo or not descripcion:
            continue

        try:
            puntaje = parse_decimal(puntaje_texto, f"puntaje del codigo {codigo}")
        except ValueError:
            puntaje = None

        cargos.append(
            {
                "codigoCargo": str(codigo),
                "descripcion": descripcion,
                "puntajeCargo": puntaje,
                "esHoraCatedra": "hora" in descripcion.lower(),
                "bonificacionDocentePorcentaje": bonificacion_docente_porcentaje(codigo),
                "bonificacionDocenteContextual": bonificacion_docente_es_contextual(codigo),
                "adicionalJerarquicoPorcentaje": adicional_jerarquico_porcentaje(
                    codigo,
                    descripcion,
                ),
            }
        )

    return cargos


def buscar_cargo(cargos: list[dict], codigo_cargo: str) -> dict | None:
    codigo = str(codigo_cargo).strip()
    for cargo in cargos:
        if cargo["codigoCargo"] == codigo:
            return cargo
    return None


def ajustar_bonificacion_docente_por_ubicacion(cargo: dict, ubicacion_zona: str) -> dict:
    ajustado = dict(cargo)
    clave = (str(ajustado.get("codigoCargo", "")).strip(), str(ubicacion_zona or "").strip())
    if clave in BONIFICACION_DOCENTE_PORCENTAJE_POR_CODIGO_ZONA:
        ajustado["bonificacionDocentePorcentaje"] = (
            BONIFICACION_DOCENTE_PORCENTAJE_POR_CODIGO_ZONA[clave]
        )
        ajustado["bonificacionDocenteAjusteUbicacion"] = ubicacion_zona
    return ajustado


def etiqueta_cargo(cargo: dict) -> str:
    puntaje = cargo.get("puntajeCargo")
    puntaje_txt = "sin puntaje" if puntaje is None else f"{puntaje:.6f} pts"
    descripcion = cargo["descripcion"]
    ayudas = []
    descripcion_normalizada = normalizar_busqueda(descripcion)

    if "hora catedra" in descripcion_normalizada:
        ayudas.append("Horas Catedras")
    if "mtro" in descripcion_normalizada or "mtra" in descripcion_normalizada:
        ayudas.append("Maestro/a")
    if "dir" in descripcion_normalizada:
        ayudas.append("Director/a")
    if "vicedir" in descripcion_normalizada:
        ayudas.append("Vicedirector/a")
    if "sec" in descripcion_normalizada:
        ayudas.append("Secretario/a")
    if cargo.get("bonificacionDocentePorcentaje", 0.0) > 0:
        ayudas.append("Bonif. Docente 27,75%")
    adicional_jerarquico = cargo.get("adicionalJerarquicoPorcentaje", 0.0)
    if adicional_jerarquico > 0:
        ayudas.append(f"Adic. Jerarquico {adicional_jerarquico * 100:g}%")

    ayuda_txt = f" - {' / '.join(ayudas)}" if ayudas else ""
    return f'{cargo["codigoCargo"]} - {descripcion}{ayuda_txt} ({puntaje_txt})'


def bonificacion_docente_porcentaje(codigo_cargo: str) -> float:
    codigo = str(codigo_cargo).strip()
    if codigo in BONIFICACION_DOCENTE_CODIGOS_EXCLUIR:
        return 0.0
    if codigo in BONIFICACION_DOCENTE_CODIGOS or codigo in BONIFICACION_DOCENTE_CODIGOS_EXTRA:
        return TASA_BONIFICACION_DOCENTE_REFERENCIA
    return 0.0


def bonificacion_docente_es_contextual(codigo_cargo: str) -> bool:
    return False


def adicional_jerarquico_porcentaje(codigo_cargo: str, descripcion: str) -> float:
    codigo = str(codigo_cargo).strip()
    if codigo in ADICIONAL_JERARQUICO_CODIGOS_EXCLUIR:
        return 0.0
    if (
        codigo in ADICIONAL_JERARQUICO_CODIGOS_RESOLUCION_2001_16
        or codigo in ADICIONAL_JERARQUICO_CODIGOS_EXTRA
    ):
        if codigo in ADICIONAL_JERARQUICO_PORCENTAJE_POR_CODIGO:
            return ADICIONAL_JERARQUICO_PORCENTAJE_POR_CODIGO[codigo]
        return TASA_ADICIONAL_JERARQUICO_REFERENCIA

    return 0.0


def normalizar_busqueda(texto: str) -> str:
    texto = str(texto or "").lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    return " ".join(texto.replace("-", " ").replace(".", " ").split())


def _alternativas_termino(termino: str) -> set[str]:
    alternativas = {termino}
    if len(termino) > 3 and termino.endswith("s"):
        alternativas.add(termino[:-1])

    alias = {
        "horas": {"hora"},
        "catedras": {"catedra"},
        "maestra": {"maestro", "mtro", "mtra"},
        "maestras": {"maestro", "mtro", "mtra"},
        "maestro": {"maestra", "mtro", "mtra"},
        "maestros": {"maestra", "mtro", "mtra"},
        "profesor": {"prof", "profesora"},
        "profesora": {"prof", "profesor"},
        "profesores": {"prof", "profesor"},
        "profesoras": {"prof", "profesora"},
        "director": {"dir", "directora"},
        "directora": {"dir", "director"},
        "secretario": {"sec", "secretaria"},
        "secretaria": {"sec", "secretario"},
    }
    alternativas.update(alias.get(termino, set()))
    return alternativas


def filtrar_cargos(cargos: list[dict], busqueda: str, limite: int = 60) -> list[dict]:
    texto = normalizar_busqueda(busqueda)
    if not texto:
        return cargos[:limite]

    terminos = [_alternativas_termino(termino) for termino in texto.split()]
    encontrados = []
    for cargo in cargos:
        base = normalizar_busqueda(
            f'{cargo["codigoCargo"]} {cargo["descripcion"]}'
        )
        if all(any(alternativa in base for alternativa in alternativas) for alternativas in terminos):
            encontrados.append(cargo)

    return encontrados[:limite]
