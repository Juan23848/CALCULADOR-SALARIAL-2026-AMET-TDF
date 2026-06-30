import base64
import html
from pathlib import Path

import streamlit as st

from acumulacion import NIVELES_EXCEPCION, evaluar_acumulacion
from cargos import (
    ajustar_bonificacion_docente_por_ubicacion,
    cargar_cargos_desde_xlsx,
    etiqueta_cargo,
)
from configuracion import (
    MONTO_SEGURO_VIDA_OBLIGATORIO,
    VALORES_INDICE_REFERENCIA,
    ZONAS_REFERENCIA,
)
from descuentos import SINDICATOS
from formato import moneda, parse_decimal, porcentaje
from no_remunerativos import calcular_no_remunerativos
from salario import calcular_salario


BASE_DIR = Path(__file__).parent
CARGOS_CACHE_VERSION = "simple-2026-06-25-v2"
LOGO_PRINCIPAL = BASE_DIR / "logo_amet_tdf_transparente.png"


def imagen_data_uri(ruta: Path) -> str:
    if not ruta.exists():
        return ""
    extension = ruta.suffix.lower().lstrip(".")
    mime = "jpeg" if extension in {"jpg", "jpeg"} else extension
    contenido = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{contenido}"


def cargar_estilos():
    st.markdown(
        """
        <style>
        :root {
            --amet-blue: #0000ff;
            --amet-blue-deep: #061064;
            --amet-sky: #05c7c8;
            --amet-green: #12866f;
            --amet-ink: #13213d;
            --amet-muted: #64748b;
            --amet-line: #d8e5fb;
            --amet-soft: #f4f8ff;
            --amet-danger: #f05d6a;
            --amet-orange: #f28c28;
        }

        .stApp {
            background:
                radial-gradient(circle at 16% 0%, rgba(0, 0, 255, 0.10), transparent 28rem),
                linear-gradient(180deg, #edf6ff 0%, #ffffff 34rem),
                #ffffff;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0);
        }

        .block-container {
            max-width: 1320px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        .amet-hero {
            position: relative;
            display: flex;
            align-items: center;
            gap: 1.35rem;
            min-height: 7.4rem;
            padding: 1rem 1.45rem;
            margin: 0 0 1rem 0;
            color: #ffffff;
            overflow: hidden;
            background:
                radial-gradient(circle at 96% 16%, rgba(255, 255, 255, 0.16) 0 1px, transparent 1px) 0 0 / 14px 14px,
                linear-gradient(150deg, #0000ff 0%, #0018c9 46%, #05c7c8 100%);
            border: 0;
            border-radius: 12px;
            box-shadow: 0 14px 32px rgba(0, 82, 180, 0.18);
        }

        .amet-hero::before {
            content: "";
            position: absolute;
            inset: auto -8% -48% 10%;
            height: 82%;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.10);
            transform: rotate(-5deg);
        }

        .amet-hero__logo {
            position: relative;
            z-index: 1;
            flex: 0 0 260px;
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            background: transparent;
            border: 0;
            border-radius: 0;
            overflow: hidden;
        }

        .amet-hero__logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            filter: drop-shadow(0 8px 18px rgba(0, 0, 0, 0.13));
        }

        .amet-hero__divider {
            position: relative;
            z-index: 1;
            width: 1px;
            align-self: stretch;
            min-height: 64px;
            background: rgba(255, 255, 255, 0.44);
        }

        .amet-hero__copy {
            position: relative;
            z-index: 1;
            flex: 1;
            min-width: 0;
        }

        .amet-hero__copy h1 {
            margin: 0;
            font-size: clamp(1.7rem, 2.8vw, 2.45rem);
            line-height: 1.02;
            letter-spacing: 0;
            color: #ffffff;
            text-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
        }

        .amet-hero__copy p {
            margin: 0.46rem 0 0 0;
            max-width: 820px;
            color: rgba(255, 255, 255, 0.90);
            font-size: 0.95rem;
        }

        .amet-hero__tag {
            display: flex;
            align-items: center;
            justify-content: center;
            width: fit-content;
            max-width: 100%;
            margin: 0 auto 0.46rem auto;
            padding: 0.26rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 800;
            line-height: 1.15;
            text-align: center;
            text-transform: uppercase;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.13);
        }

        h1, h2, h3 {
            color: var(--amet-ink);
            letter-spacing: 0;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--amet-line);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.07);
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
            box-shadow: none;
        }

        .section-title {
            display: flex;
            align-items: flex-start;
            gap: 0.72rem;
            margin: 0 0 1.05rem 0;
        }

        .section-title__icon {
            flex: 0 0 2rem;
            width: 2rem;
            height: 2rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: #e8f1ff;
            color: #0759ff;
            font-size: 0.78rem;
            font-weight: 800;
            box-shadow: inset 0 0 0 1px #c7dcff;
        }

        .section-title h2,
        .section-title h3 {
            margin: 0;
            color: #06164a;
            font-size: 1.32rem;
            line-height: 1.18;
        }

        .section-title p {
            margin: 0.18rem 0 0 0;
            color: var(--amet-muted);
            font-size: 0.86rem;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            width: 100%;
            margin-top: 0.85rem;
            padding: 0.72rem 0.85rem;
            border: 1px solid #ccebe5;
            border-radius: 8px;
            background: linear-gradient(90deg, rgba(18, 134, 111, 0.10), rgba(5, 199, 200, 0.08));
            color: #0f6b5b;
            font-weight: 700;
            font-size: 0.88rem;
        }

        .status-dot {
            flex: 0 0 1rem;
            width: 1rem;
            height: 1rem;
            border-radius: 999px;
            background: #65d7c1;
            box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.55);
        }

        .small-note {
            margin-top: 0.75rem;
            padding: 0.65rem 0.8rem;
            border-radius: 8px;
            background: #edf5ff;
            color: #2452a3;
            font-size: 0.86rem;
            font-weight: 600;
        }

        [data-testid="stMetric"] {
            min-height: 6.1rem;
            padding: 0.9rem 0.95rem;
            background: linear-gradient(180deg, #ffffff, #f8fbff);
            border: 1px solid #cfe0ff;
            border-radius: 10px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
            overflow: visible;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] p {
            max-width: 100%;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.15;
        }

        [data-testid="stMetricLabel"] p {
            color: #2452a3;
            font-weight: 800;
            font-size: 0.78rem;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] div {
            color: var(--amet-ink);
            max-width: 100%;
            font-size: clamp(1.35rem, 2vw, 1.72rem) !important;
            line-height: 1.08 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            letter-spacing: 0;
        }

        .mini-stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(7.6rem, 1fr));
            gap: 0.65rem;
            margin: 0.35rem 0 0.85rem 0;
        }

        .mini-stat {
            min-width: 0;
            padding: 0.72rem 0.78rem;
            border: 1px solid #cfe0ff;
            border-radius: 10px;
            background: linear-gradient(180deg, #ffffff, #f8fbff);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        }

        .mini-stat__label {
            margin: 0 0 0.3rem 0;
            color: #2452a3;
            font-size: 0.72rem;
            line-height: 1.15;
            font-weight: 800;
        }

        .mini-stat__value {
            margin: 0;
            color: var(--amet-ink);
            font-size: clamp(1rem, 1.1vw, 1.18rem);
            line-height: 1.08;
            font-weight: 500;
            white-space: normal;
            overflow-wrap: anywhere;
        }

        .compact-metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(8.4rem, 1fr));
            gap: 0.65rem;
            margin: 0.25rem 0 0.85rem 0;
        }

        .compact-metric-grid--two {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .compact-metric {
            min-width: 0;
            padding: 0.78rem 0.86rem;
            border: 1px solid #cfe0ff;
            border-radius: 10px;
            background: linear-gradient(180deg, #ffffff, #f8fbff);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        }

        .compact-metric--wide {
            grid-column: 1 / -1;
        }

        .compact-metric__label {
            margin: 0 0 0.32rem 0;
            color: #2452a3;
            font-size: 0.73rem;
            line-height: 1.15;
            font-weight: 800;
        }

        .compact-metric__value {
            margin: 0;
            color: var(--amet-ink);
            font-size: clamp(1.18rem, 1.55vw, 1.55rem);
            line-height: 1.08;
            font-weight: 650;
            letter-spacing: 0;
            white-space: normal;
            overflow-wrap: anywhere;
        }

        [data-testid="stTooltipIcon"] {
            margin-left: 0.35rem;
            opacity: 0.96;
            transform: translateY(1px);
        }

        [data-testid="stTooltipIcon"] svg {
            width: 1.08rem;
            height: 1.08rem;
            color: #1d4ed8;
        }

        div.stButton > button:first-child {
            border: 0;
            border-radius: 9px;
            min-height: 2.85rem;
            background: linear-gradient(135deg, #0000ff 0%, #05c7c8 100%);
            color: #ffffff;
            font-weight: 800;
            box-shadow: 0 12px 24px rgba(7, 23, 244, 0.22);
        }

        div.stButton > button:first-child:hover {
            color: #ffffff;
            filter: brightness(1.03);
            border: 0;
        }

        [data-testid="stExpander"] {
            border-color: var(--amet-line);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.76);
        }

        .summary-panel {
            margin-top: 1rem;
            padding: 1rem;
            border: 1px solid #9fb9ff;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.10);
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
        }

        .summary-item {
            min-height: 6.8rem;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #e1eaff;
            background: #ffffff;
        }

        .summary-item__label {
            margin: 0 0 0.45rem 0;
            color: var(--amet-muted);
            font-size: 0.82rem;
            font-weight: 800;
        }

        .summary-item__value {
            margin: 0;
            color: var(--amet-ink);
            font-size: clamp(1.25rem, 2.2vw, 1.8rem);
            line-height: 1.08;
            font-weight: 800;
            white-space: nowrap;
        }

        .summary-item__note {
            margin-top: 0.5rem;
            color: var(--amet-muted);
            font-size: 0.75rem;
        }

        .summary-item--blue {
            background: linear-gradient(180deg, #f7fbff, #ffffff);
        }

        .summary-item--pink .summary-item__label {
            color: #e5366b;
        }

        .summary-item--orange .summary-item__label {
            color: var(--amet-orange);
        }

        .summary-item--net {
            border-color: #82d8c4;
            background: linear-gradient(135deg, rgba(18, 134, 111, 0.13), rgba(5, 199, 200, 0.08));
        }

        .summary-item--net .summary-item__label,
        .summary-item--net .summary-item__value {
            color: var(--amet-green);
        }

        .table-caption {
            color: var(--amet-muted);
            font-size: 0.86rem;
            margin: 0.55rem 0;
        }

        .stAlert {
            border-radius: 10px;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .amet-hero {
                display: block;
                padding: 1.15rem;
                min-height: 0;
            }

            .amet-hero__logo {
                width: 100%;
                height: 66px;
                margin-bottom: 0.9rem;
            }

            .amet-hero__divider {
                display: none;
            }

            .amet-hero__copy h1,
            .amet-hero__copy p {
                text-align: center;
            }

            .summary-grid {
                grid-template-columns: 1fr;
            }

            .summary-item__value {
                white-space: normal;
            }

            .mini-stat-grid {
                grid-template-columns: repeat(auto-fit, minmax(6.8rem, 1fr));
                gap: 0.45rem;
            }

            .mini-stat {
                padding: 0.62rem;
            }

            .mini-stat__label {
                font-size: 0.68rem;
            }

            .mini-stat__value {
                font-size: 0.98rem;
            }

            .compact-metric-grid,
            .compact-metric-grid--two {
                grid-template-columns: 1fr;
            }

            .compact-metric__value {
                font-size: 1.18rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_encabezado():
    logo_src = imagen_data_uri(LOGO_PRINCIPAL)
    logo_html = (
        f'<img src="{logo_src}" alt="AMET Tierra del Fuego">'
        if logo_src
        else "<strong>AMET TDF</strong>"
    )
    st.markdown(
        f"""
        <div class="amet-hero">
            <div class="amet-hero__logo">{logo_html}</div>
            <div class="amet-hero__divider"></div>
            <div class="amet-hero__copy">
                <span class="amet-hero__tag">AMET Regional XXIV Tierra del Fuego A.I.A.S.</span>
                <h1>Simulador Salarial Docente</h1>
                <p>Cálculo aproximado para uso gremial, con cargos, zona, adicionales y descuentos del recibo docente.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def titulo_tarjeta(titulo: str, icono: str, subtitulo: str | None = None):
    subtitulo_html = (
        f"<p>{html.escape(subtitulo)}</p>"
        if subtitulo
        else ""
    )
    st.markdown(
        f"""
        <div class="section-title">
            <span class="section-title__icon">{html.escape(icono)}</span>
            <div>
                <h2>{html.escape(titulo)}</h2>
                {subtitulo_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def estado_zona(mensaje: str):
    st.markdown(
        f"""
        <div class="status-badge">
            <span class="status-dot"></span>
            <span>{html.escape(mensaje)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nota_chica(mensaje: str):
    st.markdown(
        f'<div class="small-note">{html.escape(mensaje)}</div>',
        unsafe_allow_html=True,
    )


def mostrar_advertencia_ley_761(control_acumulacion: dict):
    if control_acumulacion["estado"] == "ok":
        st.info(
            "Control Ley 761: con la carga ingresada no aparece una advertencia "
            "básica de exceso. Este control es orientativo y no bloquea el cálculo."
        )
        return

    st.warning(
        "Control Ley 761: la carga ingresada podría no encuadrar en los límites "
        "básicos de acumulación. Revisar la situación particular antes de tomar "
        "este resultado como referencia."
    )


def tarjetas_metricas(items: list[dict], columnas: str = "auto"):
    clase_columnas = f" compact-metric-grid--{columnas}" if columnas != "auto" else ""
    tarjetas = []
    for item in items:
        clase_extra = " compact-metric--wide" if item.get("wide") else ""
        tarjetas.append(
            f'<div class="compact-metric{clase_extra}">'
            f'<p class="compact-metric__label">{html.escape(item["label"])}</p>'
            f'<p class="compact-metric__value">{html.escape(item["value"])}</p>'
            "</div>"
        )
    st.markdown(
        f'<div class="compact-metric-grid{clase_columnas}">{"".join(tarjetas)}</div>',
        unsafe_allow_html=True,
    )


@st.cache_data
def cargar_cargos():
    _ = CARGOS_CACHE_VERSION
    return cargar_cargos_desde_xlsx(BASE_DIR / "cargos_mayo_2025.xlsx")


def mostrar_resumen(resultado: dict):
    no_rem = resultado["noRemunerativos"]
    bruto = resultado["brutoRemunerativo"]
    descuentos = resultado["descuentosTotales"]
    tasa_descuentos = descuentos / bruto if bruto else 0.0
    st.markdown(
        f"""
        <div class="summary-panel">
            <div class="summary-grid">
                <div class="summary-item summary-item--blue">
                    <p class="summary-item__label">Total remunerativo</p>
                    <p class="summary-item__value">{html.escape(moneda(bruto))}</p>
                </div>
                <div class="summary-item summary-item--pink">
                    <p class="summary-item__label">Descuentos</p>
                    <p class="summary-item__value">{html.escape(moneda(descuentos))}</p>
                    <div class="summary-item__note">{html.escape(porcentaje(tasa_descuentos))} del total remunerativo</div>
                </div>
                <div class="summary-item summary-item--orange">
                    <p class="summary-item__label">No remunerativos</p>
                    <p class="summary-item__value">{html.escape(moneda(no_rem))}</p>
                    <div class="summary-item__note">Incluye FOID y material didáctico automático</div>
                </div>
                <div class="summary-item summary-item--net">
                    <p class="summary-item__label">Sueldo neto estimado</p>
                    <p class="summary-item__value">{html.escape(moneda(resultado["netoFinal"]))}</p>
                    <div class="summary-item__note">Valor aproximado</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_detalle(resultado: dict):
    componentes = resultado["componentes"]
    legales = resultado["descuentosLegales"]
    sindicales = resultado.get("descuentosSindicales", {})
    detalle_no_rem = resultado.get("noRemunerativosAutomaticosDetalle", {})
    incluye_no_rem_auto = resultado.get("noRemunerativosAutomaticos", 0.0) > 0
    foid_auto = detalle_no_rem.get("foid", 0.0) if incluye_no_rem_auto else 0.0
    material_auto = (
        detalle_no_rem.get("materialDidactico", 0.0)
        if incluye_no_rem_auto
        else 0.0
    )

    mostrar_resumen(resultado)

    with st.expander("Ver detalle del cálculo", expanded=False):
        filas_detalle = [
            {"Concepto": "Básico", "Monto": moneda(componentes["basico"])},
            {
                "Concepto": f"Antigüedad ({porcentaje(componentes['porcentajeAntiguedad'])})",
                "Monto": moneda(componentes["antiguedad"]),
            },
            {
                "Concepto": "Función Docente (230%)",
                "Monto": moneda(componentes["funcionDocente"]),
            },
            {
                "Concepto": "Bonificación Docente",
                "Monto": moneda(componentes["bonificacionDocente"]),
            },
            {
                "Concepto": "Adicional Jerárquico",
                "Monto": moneda(componentes["adicionalJerarquico"]),
            },
            {
                "Concepto": (
                    f"Zona ({porcentaje(componentes['tasaZona'])} sobre Básico + Antigüedad + Función Docente "
                    "+ Transformación + Bonificación + Jerárquico)"
                ),
                "Monto": moneda(componentes["zona"]),
            },
            {
                "Concepto": "Transformación Educativa (123%)",
                "Monto": moneda(componentes["transformacionEducativa"]),
            },
            {
                "Concepto": "Asignación Hora Cátedra",
                "Monto": moneda(resultado.get("asignacionHoraCatedra", 0.0)),
            },
        ]
        if resultado.get("otrosRemunerativos", 0.0) > 0:
            filas_detalle.append(
                {
                    "Concepto": "Proporcional vacaciones / ajuste remunerativo especial",
                    "Monto": moneda(resultado.get("otrosRemunerativos", 0.0)),
                }
            )
        filas_detalle.extend(
            [
                {
                    "Concepto": "Bruto remunerativo",
                    "Monto": moneda(resultado["brutoRemunerativo"]),
                },
                {"Concepto": "Jubilación (16%)", "Monto": moneda(legales["jubilacion"])},
                {
                    "Concepto": f"Obra social ({porcentaje(legales['tasa_obra_social'])})",
                    "Monto": moneda(legales["obra_social"]),
                },
                {
                    "Concepto": "Seguro de vida obligatorio",
                    "Monto": moneda(legales["seguro_vida"]),
                },
                {
                    "Concepto": "Descuento sindical",
                    "Monto": moneda(sindicales.get("total", 0.0)),
                },
                {
                    "Concepto": "Neto sin no remunerativos",
                    "Monto": moneda(resultado["netoSinNoRemunerativos"]),
                },
                {
                    "Concepto": "FOID automático",
                    "Monto": moneda(foid_auto),
                },
                {
                    "Concepto": "Refuerzo ayuda material didáctico automático",
                    "Monto": moneda(material_auto),
                },
                {
                    "Concepto": "No remunerativos total",
                    "Monto": moneda(resultado["noRemunerativos"]),
                },
                {"Concepto": "Neto final", "Monto": moneda(resultado["netoFinal"])},
            ]
        )
        st.table(filas_detalle)

        st.markdown(
            '<p class="table-caption">Detalle de cargos y horas usados para calcular el básico</p>',
            unsafe_allow_html=True,
        )
        st.table(
            [
                {
                    "Código": item["codigoCargo"],
                    "Descripción": item["descripcion"],
                    "Cantidad": item["cantidad"],
                    "Puntaje unitario": f"{item['puntajeCargo']:.8f}",
                    "Puntaje total": f"{item['puntajeTotal']:.8f}",
                    "Básico": moneda(item["basico"]),
                    "Bonif. docente": moneda(item["bonificacionDocente"]),
                    "Adic. jerárquico": moneda(item["adicionalJerarquico"]),
                }
                for item in componentes["detalle"]
            ]
        )

        if sindicales.get("detalle"):
            st.markdown(
                '<p class="table-caption">Detalle del descuento sindical</p>',
                unsafe_allow_html=True,
            )
            st.table(
                [
                    {
                        "Sindicato": item["sindicato"],
                        "Sobre remunerativo": porcentaje(item["tasa_remunerativo"]),
                        "Monto remunerativo": moneda(item["monto_remunerativo"]),
                        "Sobre FOID": porcentaje(item["tasa_foid"]),
                        "Monto FOID": moneda(item["monto_foid"]),
                        "Total": moneda(item["total"]),
                    }
                    for item in sindicales["detalle"]
                ]
            )


def consolidar_cargos(cargos_seleccionados: list[dict]) -> list[dict]:
    agrupados = {}
    for cargo in cargos_seleccionados:
        clave = (
            cargo["codigoCargo"],
            cargo.get("bonificacionDocentePorcentaje", 0.0),
            cargo.get("bonificacionDocenteMonto", 0.0),
            cargo.get("adicionalJerarquicoPorcentaje", 0.0),
        )
        if clave not in agrupados:
            agrupados[clave] = dict(cargo)
            continue
        agrupados[clave]["cantidad"] += cargo["cantidad"]
    return list(agrupados.values())


st.set_page_config(page_title="Simulador Salarial Docente AMET TDF", layout="wide")
cargar_estilos()
mostrar_encabezado()

try:
    cargos = cargar_cargos()
except Exception as exc:
    st.error(f"No se pudo cargar la tabla de cargos: {exc}")
    st.stop()

valor_indice = VALORES_INDICE_REFERENCIA["Mayo 2026 recibos"]

with st.container(border=True):
    titulo_tarjeta(
        "Ciudad y zona",
        "1",
        "Elija la ciudad o zona para aplicar automáticamente el coeficiente correspondiente.",
    )
    ubicacion_zona = st.selectbox(
        "Ciudad / zona",
        list(ZONAS_REFERENCIA.keys()),
        index=0,
        help="Define el porcentaje del suplemento zona.",
    )
    zona_referencia = ZONAS_REFERENCIA[ubicacion_zona]
    zona_porcentaje_corto = f"{zona_referencia * 100:.0f}%"
    if ubicacion_zona == "Escuelas Rurales":
        estado_zona(
            "Zona aplicada: "
            f"{zona_porcentaje_corto}. Incluye Estancia Sara, Lago Escondido, "
            "San Sebastián, Puerto Almanza y Escuela Antártica Nro. 38."
        )
    else:
        estado_zona(f"Zona aplicada: {zona_porcentaje_corto}.")
    st.caption(
        "Valor índice aplicado: Mayo 2026 recibos "
        f"({str(valor_indice).replace('.', ',')})."
    )

cargos_ubicacion = [
    ajustar_bonificacion_docente_por_ubicacion(cargo, ubicacion_zona)
    for cargo in cargos
]
opciones = [etiqueta_cargo(cargo) for cargo in cargos_ubicacion]
por_etiqueta = dict(zip(opciones, cargos_ubicacion))
indice_212 = next(
    (i for i, cargo in enumerate(cargos_ubicacion) if cargo["codigoCargo"] == "212"),
    0,
)

with st.container(border=True):
    titulo_tarjeta(
        "Cargos u horas cátedra",
        "2",
        "Indique cuántas líneas necesita y cargue cada cargo u hora como aparece en el recibo.",
    )
    cantidad_lineas = st.number_input(
        "Cantidad de cargos u horas cátedra a incorporar",
        min_value=1,
        max_value=6,
        value=1,
        step=1,
        help=(
            "Agrupe por código o tipo de cargo. Si un mismo código tiene una parte "
            "con bonificación por institución y otra parte sin bonificación, cárguelo "
            "en dos líneas."
        ),
    )

    cargos_seleccionados = []
    for indice in range(int(cantidad_lineas)):
        st.markdown(f"**Cargo / hora {indice + 1}**")
        col_cargo, col_cantidad = st.columns([5, 1])
        with col_cargo:
            seleccionado = st.selectbox(
                "Seleccionar cargo u horas cátedra (puede escribir código o descripción)",
                opciones,
                index=indice_212 if indice == 0 else 0,
                key=f"nuevo_cargo_{indice}",
            )
        cargo = dict(por_etiqueta[seleccionado])
        with col_cantidad:
            etiqueta_cantidad = "Horas" if cargo["esHoraCatedra"] else "Cantidad"
            cantidad = st.number_input(
                etiqueta_cantidad,
                min_value=1,
                max_value=60,
                value=1,
                step=1,
                key=f"nuevo_cantidad_{indice}",
            )
        cargo["cantidad"] = int(cantidad)
        cargos_seleccionados.append(cargo)

    nota_chica(
        "Para sumar otra línea, aumente la cantidad de cargos u horas cátedra a incorporar."
    )

cargos_seleccionados = consolidar_cargos(cargos_seleccionados)
control_acumulacion = evaluar_acumulacion(cargos_seleccionados, 0)
resumen_acumulacion = control_acumulacion["resumen"]
detalle_no_remunerativos = calcular_no_remunerativos(cargos_seleccionados)

with st.container(border=True):
    titulo_tarjeta(
        "Antigüedad",
        "3",
        "Ingrese los años de antigüedad reconocidos.",
    )
    anios_antiguedad = st.number_input(
        "Años de antigüedad reconocidos",
        min_value=0,
        max_value=50,
        value=0,
        step=1,
    )

with st.container(border=True):
    titulo_tarjeta(
        "Descuento sindical",
        "4",
        "Único descuento opcional a seleccionar por el docente.",
    )
    sindicatos_seleccionados = st.multiselect(
        "Sindicato(s)",
        list(SINDICATOS.keys()),
        default=[],
        max_selections=3,
        placeholder="Sin descuento sindical",
        help="Seleccione hasta 3 afiliaciones sindicales. Si no corresponde, deje el campo vacío.",
    )
    st.caption(
        "Jubilación, obra social y seguro de vida se calculan automáticamente; "
        "no requieren carga manual."
    )

with st.container(border=True):
    titulo_tarjeta(
        "Resumen de datos cargados",
        "R",
        "Vista general antes de calcular.",
    )
    tarjetas_metricas(
        [
            {"label": "Ciudad / zona", "value": ubicacion_zona},
            {"label": "Zona aplicada", "value": zona_porcentaje_corto},
            {"label": "Antigüedad", "value": f"{int(anios_antiguedad)} años"},
            {"label": "Líneas cargadas", "value": f"{len(cargos_seleccionados):g}"},
            {
                "label": "Horas cátedra",
                "value": f"{resumen_acumulacion['horasCatedra']:g}",
            },
            {
                "label": "Jornada simple",
                "value": f"{resumen_acumulacion['jornadaSimple']:g}",
            },
            {
                "label": "Jornada completa",
                "value": f"{resumen_acumulacion['jornadaCompleta']:g}",
            },
            {
                "label": "Directivos / jerárquicos",
                "value": f"{resumen_acumulacion['directivosJerarquicos']:g}",
            },
            {
                "label": "Descuento sindical",
                "value": ", ".join(sindicatos_seleccionados) if sindicatos_seleccionados else "Sin descuento",
                "wide": True,
            },
        ]
    )
    st.caption(
        "No remunerativos automáticos previstos: FOID "
        f"{moneda(detalle_no_remunerativos['foid'])} y material didáctico "
        f"{moneda(detalle_no_remunerativos['materialDidactico'])}."
    )
    mostrar_advertencia_ley_761(control_acumulacion)

boton_izq, boton_der = st.columns([0.68, 0.32])
with boton_der:
    calcular = st.button("Calcular simulación", type="primary", use_container_width=True)

if calcular:
    try:
        resultado_actual = calcular_salario(
            cargos_seleccionados,
            valor_indice,
            int(anios_antiguedad),
            otros_remunerativos=0.0,
            no_remunerativos=0.0,
            descuento_adicional_porcentaje=0.0,
            descuento_adicional_fijo=0.0,
            incluir_jubilacion=True,
            incluir_obra_social=True,
            tasa_obra_social=0.03,
            tasa_zona=zona_referencia,
            incluir_no_remunerativos_automaticos=True,
            incluir_asignacion_hora_catedra=True,
            sindicatos=sindicatos_seleccionados,
        )

        mostrar_detalle(resultado_actual)
        nota_chica(
            "Este simulador brinda un cálculo aproximado. Los valores definitivos surgen de la liquidación oficial del recibo de sueldo."
        )

    except ValueError as exc:
        st.error(str(exc))

st.stop()
