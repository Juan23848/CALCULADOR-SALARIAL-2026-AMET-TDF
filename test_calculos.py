import unittest

from acumulacion import evaluar_acumulacion
from cargos import (
    ajustar_bonificacion_docente_por_ubicacion,
    buscar_cargo,
    cargar_cargos_desde_xlsx,
    filtrar_cargos,
)
from configuracion import VALORES_INDICE_REFERENCIA, ZONAS_REFERENCIA
from descuentos import descuento_sindical
from no_remunerativos import calcular_no_remunerativos
from remunerativos import calcular_asignacion_hora_catedra
from salario import calcular_salario
from simulador import aplicar_aumentos_compuestos, comparar_con_canasta


class CalculosSalarialesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cargos = cargar_cargos_desde_xlsx("cargos_mayo_2025.xlsx")

    def test_codigo_212_usa_puntaje_y_no_codigo(self):
        cargo = buscar_cargo(self.cargos, "212")
        self.assertIsNotNone(cargo)
        self.assertAlmostEqual(cargo["puntajeCargo"], 1432.8223159690799)

        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=89.36003862,
            anios_antiguedad=0,
        )
        basico_esperado = cargo["puntajeCargo"] * 89.36003862
        self.assertAlmostEqual(resultado["componentes"]["basico"], basico_esperado, places=2)
        self.assertNotAlmostEqual(resultado["componentes"]["basico"], 212 * 89.36003862)

    def test_zona_incluye_transformacion_segun_recibo_real(self):
        cargo = buscar_cargo(self.cargos, "212")
        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=89.36003862,
            anios_antiguedad=0,
        )
        componentes = resultado["componentes"]
        zona_esperada = (
            componentes["basico"]
            + componentes["antiguedad"]
            + componentes["funcionDocente"]
            + componentes["transformacionEducativa"]
        )
        self.assertAlmostEqual(componentes["zona"], zona_esperada)

    def test_zona_tolhuin_calcula_120_por_ciento(self):
        cargo = buscar_cargo(self.cargos, "212")
        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=100,
            anios_antiguedad=0,
            tasa_zona=1.20,
        )
        componentes = resultado["componentes"]
        self.assertAlmostEqual(componentes["tasaZona"], 1.20)
        self.assertAlmostEqual(componentes["zona"], round(componentes["baseZona"] * 1.20, 2))

    def test_zonas_referencia_provinciales(self):
        self.assertEqual(ZONAS_REFERENCIA["Ushuaia"], 1.00)
        self.assertEqual(ZONAS_REFERENCIA["Rio Grande"], 1.00)
        self.assertEqual(ZONAS_REFERENCIA["Tolhuin"], 1.20)
        self.assertEqual(ZONAS_REFERENCIA["Escuelas Rurales"], 1.20)

    def test_valor_indice_base_es_mayo_2026(self):
        self.assertEqual(list(VALORES_INDICE_REFERENCIA), ["Mayo 2026 recibos"])
        self.assertAlmostEqual(
            VALORES_INDICE_REFERENCIA["Mayo 2026 recibos"],
            95.72248503794604,
        )

    def test_descuentos_obligatorios_por_defecto(self):
        cargo = buscar_cargo(self.cargos, "212")
        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=89.36003862,
            anios_antiguedad=0,
        )
        bruto = resultado["brutoRemunerativo"]
        self.assertAlmostEqual(resultado["descuentosLegales"]["jubilacion"], bruto * 0.16)
        self.assertAlmostEqual(resultado["descuentosLegales"]["obra_social"], bruto * 0.03)
        self.assertAlmostEqual(resultado["descuentosLegales"]["seguro_vida"], 2750.00)
        self.assertAlmostEqual(resultado["descuentosTotales"], bruto * 0.19 + 2750.00)

    def test_descuentos_permiten_obra_social_35_por_ciento(self):
        cargo = buscar_cargo(self.cargos, "212")
        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=89.36003862,
            anios_antiguedad=0,
            tasa_obra_social=0.035,
        )
        bruto = resultado["brutoRemunerativo"]
        self.assertAlmostEqual(resultado["descuentosTotales"], bruto * 0.195 + 2750.00)

    def test_descuento_sindical_calcula_remunerativo_y_foid(self):
        detalle = descuento_sindical(
            bruto_remunerativo=1_000_000.00,
            monto_foid=100_000.00,
            sindicatos=["AMET", "ATE", "OTROS"],
        )

        self.assertEqual(detalle["sindicatos"], ["AMET", "ATE", "OTROS"])
        self.assertAlmostEqual(detalle["monto_remunerativo"], 57000.00)
        self.assertAlmostEqual(detalle["monto_foid"], 3500.00)
        self.assertAlmostEqual(detalle["total"], 60500.00)

    def test_salario_descuenta_sindicatos_sobre_bruto_y_foid(self):
        cargo = buscar_cargo(self.cargos, "212")
        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=95.72248503794604,
            anios_antiguedad=14,
            incluir_no_remunerativos_automaticos=True,
            sindicatos=["AMET"],
        )

        esperado = (
            resultado["brutoRemunerativo"] * 0.015
            + resultado["noRemunerativosAutomaticosDetalle"]["foid"] * 0.015
        )
        self.assertAlmostEqual(resultado["descuentosSindicales"]["total"], esperado)
        self.assertAlmostEqual(
            resultado["descuentosTotales"],
            resultado["descuentosLegales"]["total"]
            + resultado["descuentosSindicales"]["total"]
            + resultado["descuentosAdicionales"]["total"],
        )

    def test_no_remunerativos_un_cargo_simple(self):
        detalle = calcular_no_remunerativos(
            [
                {
                    "codigoCargo": "212",
                    "descripcion": "Mtro. Nivel EGB - T.S.",
                    "cantidad": 1,
                    "esHoraCatedra": False,
                }
            ]
        )

        self.assertAlmostEqual(detalle["equivalenteTotal"], 1.0)
        self.assertAlmostEqual(detalle["foid"], 56000.00)
        self.assertAlmostEqual(detalle["materialDidactico"], 71300.00)
        self.assertAlmostEqual(detalle["total"], 127300.00)

    def test_no_remunerativos_horas_catedra_topan_en_38(self):
        detalle = calcular_no_remunerativos(
            [
                {
                    "codigoCargo": "852",
                    "descripcion": "Horas Catedra Nivel Medio",
                    "cantidad": 40,
                    "esHoraCatedra": True,
                }
            ]
        )

        self.assertAlmostEqual(detalle["horasCatedraComputadas"], 38.0)
        self.assertAlmostEqual(detalle["equivalenteTotal"], 2.0)
        self.assertAlmostEqual(detalle["foid"], 112000.00)
        self.assertAlmostEqual(detalle["materialDidactico"], 142600.00)
        self.assertAlmostEqual(detalle["total"], 254600.00)

    def test_no_remunerativos_un_simple_y_horas_usa_hasta_19_horas(self):
        detalle = calcular_no_remunerativos(
            [
                {
                    "codigoCargo": "212",
                    "descripcion": "Mtro. Nivel EGB - T.S.",
                    "cantidad": 1,
                    "esHoraCatedra": False,
                },
                {
                    "codigoCargo": "852",
                    "descripcion": "Horas Catedra Nivel Medio",
                    "cantidad": 23,
                    "esHoraCatedra": True,
                },
            ]
        )

        self.assertAlmostEqual(detalle["equivalenteCargosSimplesComputados"], 1.0)
        self.assertAlmostEqual(detalle["horasCatedraComputadas"], 19.0)
        self.assertAlmostEqual(detalle["equivalenteTotal"], 2.0)
        self.assertAlmostEqual(detalle["total"], 254600.00)

    def test_no_remunerativos_dos_simples_o_tc_saturan_el_tope(self):
        dos_simples = calcular_no_remunerativos(
            [
                {
                    "codigoCargo": "212",
                    "descripcion": "Mtro. Nivel EGB - T.S.",
                    "cantidad": 2,
                    "esHoraCatedra": False,
                },
                {
                    "codigoCargo": "852",
                    "descripcion": "Horas Catedra Nivel Medio",
                    "cantidad": 10,
                    "esHoraCatedra": True,
                },
            ]
        )
        cargo_completo = calcular_no_remunerativos(
            [
                {
                    "codigoCargo": "214",
                    "descripcion": "Mtro. Nivel EGB - T.C.",
                    "cantidad": 1,
                    "esHoraCatedra": False,
                },
                {
                    "codigoCargo": "852",
                    "descripcion": "Horas Catedra Nivel Medio",
                    "cantidad": 10,
                    "esHoraCatedra": True,
                },
            ]
        )

        self.assertAlmostEqual(dos_simples["horasCatedraComputadas"], 0.0)
        self.assertAlmostEqual(dos_simples["total"], 254600.00)
        self.assertAlmostEqual(cargo_completo["horasCatedraComputadas"], 0.0)
        self.assertAlmostEqual(cargo_completo["total"], 254600.00)

    def test_no_remunerativos_no_integran_base_de_descuentos(self):
        cargo = buscar_cargo(self.cargos, "212")
        base = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=95.72248503794604,
            anios_antiguedad=14,
            no_remunerativos=0.0,
            incluir_no_remunerativos_automaticos=False,
        )
        con_no_remunerativos = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=95.72248503794604,
            anios_antiguedad=14,
            no_remunerativos=100000.0,
            incluir_no_remunerativos_automaticos=True,
        )

        self.assertAlmostEqual(
            con_no_remunerativos["brutoRemunerativo"],
            base["brutoRemunerativo"],
        )
        self.assertAlmostEqual(
            con_no_remunerativos["descuentosTotales"],
            base["descuentosTotales"],
        )
        diferencia_neto = (
            con_no_remunerativos["netoFinal"]
            - base["netoFinal"]
        )
        self.assertAlmostEqual(diferencia_neto, 227300.00)

    def test_asignacion_hora_catedra_automatica_horas(self):
        valor_indice = 95.72248503794604
        cargos = [
            {**buscar_cargo(self.cargos, "852"), "cantidad": 27},
            {**buscar_cargo(self.cargos, "312"), "cantidad": 10},
            {**buscar_cargo(self.cargos, "421"), "cantidad": 2},
        ]
        detalle = calcular_asignacion_hora_catedra(
            cargos,
            valor_indice,
            anios_antiguedad=14,
        )

        self.assertAlmostEqual(detalle["horasCatedraComputadas"], 39.0)
        self.assertAlmostEqual(detalle["equivalenteTotal"], 39 / 21)
        self.assertAlmostEqual(detalle["asignacionHoraCatedra"], 130515.26, delta=0.05)

    def test_asignacion_hora_catedra_automatica_cargos(self):
        valor_indice = 95.72248503794604
        un_cargo = calcular_asignacion_hora_catedra(
            [{**buscar_cargo(self.cargos, "819"), "cantidad": 1}],
            valor_indice,
            anios_antiguedad=9,
        )
        dos_cargos = calcular_asignacion_hora_catedra(
            [{**buscar_cargo(self.cargos, "842"), "cantidad": 2}],
            valor_indice,
            anios_antiguedad=13,
        )

        self.assertAlmostEqual(un_cargo["equivalenteTotal"], 1.0)
        self.assertAlmostEqual(un_cargo["asignacionHoraCatedra"], 66358.62, delta=0.05)
        self.assertAlmostEqual(dos_cargos["equivalenteTotal"], 2.0)
        self.assertAlmostEqual(dos_cargos["asignacionHoraCatedra"], 140554.88, delta=0.05)

    def test_asignacion_hora_catedra_acta_30_10_25_combinaciones(self):
        valor_indice = 95.72248503794604
        cargo_simple = buscar_cargo(self.cargos, "819")
        hora_catedra = buscar_cargo(self.cargos, "852")

        simple_y_5_horas = calcular_asignacion_hora_catedra(
            [
                {**cargo_simple, "cantidad": 1},
                {**hora_catedra, "cantidad": 5},
            ],
            valor_indice,
            anios_antiguedad=14,
        )
        simple_y_14_horas = calcular_asignacion_hora_catedra(
            [
                {**cargo_simple, "cantidad": 1},
                {**hora_catedra, "cantidad": 14},
            ],
            valor_indice,
            anios_antiguedad=14,
        )
        completo_y_horas = calcular_asignacion_hora_catedra(
            [
                {
                    "descripcion": "Mtro. Nivel EGB - T.C.",
                    "cantidad": 1,
                    "esHoraCatedra": False,
                },
                {**hora_catedra, "cantidad": 14},
            ],
            valor_indice,
            anios_antiguedad=14,
        )

        self.assertAlmostEqual(simple_y_5_horas["equivalenteTotal"], 1 + 5 / 21)
        self.assertAlmostEqual(simple_y_14_horas["equivalenteTotal"], 1 + 14 / 21)
        self.assertAlmostEqual(completo_y_horas["equivalenteTotal"], 2.0)
        self.assertAlmostEqual(completo_y_horas["horasCatedraComputadas"], 0.0)

    def test_recibo_mayo_2026(self):
        valor_indice = 95.72248503794604
        cargos = [
            {**buscar_cargo(self.cargos, "852"), "cantidad": 3},
            {**buscar_cargo(self.cargos, "312"), "cantidad": 10},
            {**buscar_cargo(self.cargos, "852"), "cantidad": 7},
            {**buscar_cargo(self.cargos, "852"), "cantidad": 14},
            {**buscar_cargo(self.cargos, "421"), "cantidad": 2},
            {**buscar_cargo(self.cargos, "852"), "cantidad": 3},
        ]

        resultado = calcular_salario(
            cargos,
            valor_indice=valor_indice,
            anios_antiguedad=14,
            otros_remunerativos=0.0,
            no_remunerativos=0.0,
            descuento_adicional_fijo=42240.02,
            tasa_obra_social=0.03,
            incluir_no_remunerativos_automaticos=True,
            incluir_asignacion_hora_catedra=True,
        )

        self.assertAlmostEqual(resultado["componentes"]["basico"], 254723.04, delta=0.25)
        self.assertAlmostEqual(resultado["asignacionHoraCatedra"], 130515.26, delta=0.05)
        self.assertAlmostEqual(resultado["noRemunerativosAutomaticos"], 254600.00, delta=0.01)
        self.assertAlmostEqual(
            resultado["componentes"]["bonificacionDocente"],
            21749.42,
            delta=0.25,
        )
        self.assertAlmostEqual(resultado["componentes"]["zona"], 1392159.46, delta=0.25)
        self.assertAlmostEqual(resultado["brutoRemunerativo"], 2914834.18, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["jubilacion"], 466373.47, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["obra_social"], 87445.03, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["seguro_vida"], 2750.00, delta=0.01)
        self.assertAlmostEqual(resultado["descuentosTotales"], 598808.51, delta=0.50)
        self.assertAlmostEqual(resultado["netoFinal"], 2570625.67, delta=0.75)

    def test_recibo_febrero_2026_con_proporcional_vacaciones(self):
        valor_indice = 95.72248503794604
        cargos = [
            {**buscar_cargo(self.cargos, "852"), "cantidad": 10},
            {**buscar_cargo(self.cargos, "843"), "cantidad": 1},
            {**buscar_cargo(self.cargos, "910"), "cantidad": 4},
        ]

        sin_item_215 = calcular_salario(
            cargos,
            valor_indice=valor_indice,
            anios_antiguedad=10,
            incluir_asignacion_hora_catedra=True,
        )
        con_item_215 = calcular_salario(
            cargos,
            valor_indice=valor_indice,
            anios_antiguedad=10,
            otros_remunerativos=202437.39,
            incluir_asignacion_hora_catedra=True,
        )

        self.assertAlmostEqual(sin_item_215["brutoRemunerativo"], 3570335.97, delta=0.75)
        self.assertAlmostEqual(con_item_215["otrosRemunerativos"], 202437.39, delta=0.01)
        self.assertAlmostEqual(con_item_215["brutoRemunerativo"], 3772773.36, delta=0.75)

    def test_recibo_paredes_mayo_2026(self):
        cargo = buscar_cargo(self.cargos, "819")
        valor_indice = 182871.06 / cargo["puntajeCargo"]

        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=valor_indice,
            anios_antiguedad=9,
            otros_remunerativos=0.0,
            no_remunerativos=0.0,
            descuento_adicional_fijo=32722.30,
            tasa_obra_social=0.03,
            incluir_no_remunerativos_automaticos=True,
            incluir_asignacion_hora_catedra=True,
        )

        componentes = resultado["componentes"]
        self.assertAlmostEqual(componentes["basico"], 182871.06, delta=0.25)
        self.assertAlmostEqual(resultado["asignacionHoraCatedra"], 66358.62, delta=0.05)
        self.assertAlmostEqual(resultado["noRemunerativosAutomaticos"], 127300.00, delta=0.01)
        self.assertAlmostEqual(componentes["antiguedad"], 100579.08, delta=0.25)
        self.assertAlmostEqual(componentes["funcionDocente"], 420603.44, delta=0.25)
        self.assertAlmostEqual(
            componentes["transformacionEducativa"],
            224931.40,
            delta=0.25,
        )
        self.assertAlmostEqual(componentes["adicionalJerarquico"], 100579.08, delta=0.25)
        self.assertAlmostEqual(componentes["zona"], 1029564.06, delta=0.50)
        self.assertAlmostEqual(resultado["brutoRemunerativo"], 2125486.74, delta=0.75)
        self.assertAlmostEqual(resultado["descuentosLegales"]["jubilacion"], 340077.88, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["obra_social"], 63764.60, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["seguro_vida"], 2750.00, delta=0.01)
        self.assertAlmostEqual(resultado["descuentosTotales"], 439314.78, delta=0.75)
        self.assertAlmostEqual(resultado["netoFinal"], 1813471.96, delta=0.75)

    def test_recibo_penedo_mayo_2026(self):
        cargo = buscar_cargo(self.cargos, "842")
        valor_indice = 124097.15 / cargo["puntajeCargo"]

        resultado = calcular_salario(
            [{**cargo, "cantidad": 2}],
            valor_indice=valor_indice,
            anios_antiguedad=13,
            otros_remunerativos=0.0,
            no_remunerativos=15495.84,
            descuento_adicional_porcentaje=0.02,
            descuento_adicional_fijo=43846.88,
            tasa_obra_social=0.03,
            incluir_no_remunerativos_automaticos=True,
            incluir_asignacion_hora_catedra=True,
        )

        componentes = resultado["componentes"]
        self.assertAlmostEqual(componentes["basico"], 248194.30, delta=0.25)
        self.assertAlmostEqual(resultado["asignacionHoraCatedra"], 140554.88, delta=0.05)
        self.assertAlmostEqual(resultado["noRemunerativosAutomaticos"], 254600.00, delta=0.01)
        self.assertAlmostEqual(resultado["otrosNoRemunerativos"], 15495.84, delta=0.01)
        self.assertAlmostEqual(resultado["noRemunerativos"], 270095.84, delta=0.01)
        self.assertAlmostEqual(componentes["antiguedad"], 210965.16, delta=0.25)
        self.assertAlmostEqual(componentes["funcionDocente"], 570846.90, delta=0.25)
        self.assertAlmostEqual(componentes["transformacionEducativa"], 305278.98, delta=0.25)
        self.assertAlmostEqual(componentes["bonificacionDocente"], 0.0, delta=0.01)
        self.assertAlmostEqual(componentes["adicionalJerarquico"], 0.0, delta=0.01)
        self.assertAlmostEqual(componentes["zona"], 1335285.34, delta=0.50)
        self.assertAlmostEqual(resultado["brutoRemunerativo"], 2811125.56, delta=0.75)
        self.assertAlmostEqual(resultado["descuentosLegales"]["jubilacion"], 449780.09, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["obra_social"], 84333.77, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["seguro_vida"], 2750.00, delta=0.01)
        self.assertAlmostEqual(resultado["descuentosAdicionales"]["monto_porcentual"], 56222.51, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosAdicionales"]["monto_fijo"], 43846.88, delta=0.01)
        self.assertAlmostEqual(resultado["descuentosTotales"], 636933.25, delta=0.75)
        self.assertAlmostEqual(resultado["netoFinal"], 2444288.15, delta=0.75)

    def test_aumentos_sucesivos_son_compuestos(self):
        valor = aplicar_aumentos_compuestos(86.75732, [0.035, 0.04])
        self.assertAlmostEqual(valor, 86.75732 * 1.035 * 1.04)
        self.assertNotAlmostEqual(valor, 86.75732 * 1.075)

    def test_canasta_basica(self):
        comparacion = comparar_con_canasta(neto=800000, canasta_basica=1000000)
        self.assertEqual(comparacion["montoFaltante"], 200000)
        self.assertAlmostEqual(comparacion["cobertura"], 0.8)

    def test_busqueda_filtra_por_codigo_descripcion_y_alias(self):
        por_codigo = filtrar_cargos(self.cargos, "852")
        self.assertEqual(por_codigo[0]["codigoCargo"], "852")

        por_horas = filtrar_cargos(self.cargos, "horas catedras")
        self.assertTrue(any(cargo["codigoCargo"] == "852" for cargo in por_horas))

        por_maestra = filtrar_cargos(self.cargos, "maestra")
        self.assertTrue(any("Mtro" in cargo["descripcion"] for cargo in por_maestra))

    def test_bonificacion_docente_automatica_por_codigo(self):
        self.assertEqual(buscar_cargo(self.cargos, "215")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "312")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "314")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "421")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "455")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "457")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "816")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "844")["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(buscar_cargo(self.cargos, "304")["bonificacionDocentePorcentaje"], 0.0)
        self.assertEqual(buscar_cargo(self.cargos, "412")["bonificacionDocentePorcentaje"], 0.0)
        self.assertEqual(buscar_cargo(self.cargos, "852")["bonificacionDocentePorcentaje"], 0.0)
        self.assertFalse(buscar_cargo(self.cargos, "852")["bonificacionDocenteContextual"])

    def test_bonificacion_docente_421_tolhuin_usa_porcentaje_especial(self):
        cargo_421 = buscar_cargo(self.cargos, "421")
        ushuaia = ajustar_bonificacion_docente_por_ubicacion(cargo_421, "Ushuaia")
        tolhuin = ajustar_bonificacion_docente_por_ubicacion(cargo_421, "Tolhuin")

        self.assertEqual(ushuaia["bonificacionDocentePorcentaje"], 0.2775)
        self.assertEqual(tolhuin["bonificacionDocentePorcentaje"], 0.2325)

    def test_recibo_conti_tolhuin_mayo_2026(self):
        valor_indice = 95.72248503794604
        cargo_421 = ajustar_bonificacion_docente_por_ubicacion(
            buscar_cargo(self.cargos, "421"),
            "Tolhuin",
        )
        cargo_474 = buscar_cargo(self.cargos, "474")

        resultado = calcular_salario(
            [
                {**cargo_421, "cantidad": 12},
                {**cargo_474, "cantidad": 18},
            ],
            valor_indice=valor_indice,
            anios_antiguedad=8,
            otros_remunerativos=0.0,
            no_remunerativos=224578.90,
            descuento_adicional_fijo=36550.83,
            tasa_obra_social=0.03,
            tasa_zona=1.20,
            incluir_asignacion_hora_catedra=True,
        )

        componentes = resultado["componentes"]
        self.assertAlmostEqual(componentes["basico"], 195940.80, delta=0.25)
        self.assertAlmostEqual(resultado["asignacionHoraCatedra"], 94798.00, delta=0.05)
        self.assertAlmostEqual(componentes["antiguedad"], 107767.44, delta=0.25)
        self.assertAlmostEqual(componentes["funcionDocente"], 450663.90, delta=0.25)
        self.assertAlmostEqual(componentes["transformacionEducativa"], 241007.18, delta=0.25)
        self.assertAlmostEqual(componentes["bonificacionDocente"], 18222.49, delta=0.25)
        self.assertAlmostEqual(componentes["zona"], 1216322.17, delta=0.50)
        self.assertAlmostEqual(resultado["brutoRemunerativo"], 2324721.98, delta=0.75)
        self.assertAlmostEqual(resultado["descuentosLegales"]["jubilacion"], 371955.51, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["obra_social"], 69741.66, delta=0.50)
        self.assertAlmostEqual(resultado["descuentosLegales"]["seguro_vida"], 2750.00, delta=0.01)
        self.assertAlmostEqual(resultado["descuentosTotales"], 480998.00, delta=0.75)
        self.assertAlmostEqual(resultado["netoFinal"], 2068302.88, delta=0.75)

    def test_recibo_coman_mayo_2026_jerarquico_821(self):
        valor_indice = 95.72248503794604
        cargos = [
            {**buscar_cargo(self.cargos, "852"), "cantidad": 10},
            {**buscar_cargo(self.cargos, "821"), "cantidad": 1},
            {**buscar_cargo(self.cargos, "421"), "cantidad": 8},
        ]

        resultado = calcular_salario(
            cargos,
            valor_indice=valor_indice,
            anios_antiguedad=14,
            incluir_no_remunerativos_automaticos=True,
            incluir_asignacion_hora_catedra=True,
            sindicatos=["SUTEF", "AMET"],
        )

        componentes = resultado["componentes"]
        self.assertAlmostEqual(componentes["basico"], 369704.88, delta=0.25)
        self.assertAlmostEqual(componentes["adicionalJerarquico"], 138677.22, delta=0.25)
        self.assertAlmostEqual(componentes["bonificacionDocente"], 14499.62, delta=0.25)
        self.assertAlmostEqual(componentes["zona"], 2142189.29, delta=0.75)
        self.assertAlmostEqual(resultado["asignacionHoraCatedra"], 140554.88, delta=0.05)
        self.assertAlmostEqual(resultado["brutoRemunerativo"], 4424933.40, delta=1.00)

    def test_adicional_jerarquico_automatico_por_codigo_y_descripcion(self):
        self.assertEqual(buscar_cargo(self.cargos, "401")["adicionalJerarquicoPorcentaje"], 0.55)
        self.assertEqual(buscar_cargo(self.cargos, "103")["adicionalJerarquicoPorcentaje"], 0.55)
        self.assertEqual(buscar_cargo(self.cargos, "826")["adicionalJerarquicoPorcentaje"], 0.55)
        self.assertEqual(buscar_cargo(self.cargos, "954")["adicionalJerarquicoPorcentaje"], 0.55)
        self.assertEqual(buscar_cargo(self.cargos, "819")["adicionalJerarquicoPorcentaje"], 0.55)
        self.assertEqual(buscar_cargo(self.cargos, "821")["adicionalJerarquicoPorcentaje"], 0.55)
        self.assertEqual(buscar_cargo(self.cargos, "314")["adicionalJerarquicoPorcentaje"], 0.0)
        self.assertEqual(buscar_cargo(self.cargos, "852")["adicionalJerarquicoPorcentaje"], 0.0)

    def test_adicional_jerarquico_calcula_55_por_ciento_del_basico(self):
        cargo = buscar_cargo(self.cargos, "401")
        resultado = calcular_salario(
            [{**cargo, "cantidad": 1}],
            valor_indice=100,
            anios_antiguedad=0,
        )
        componentes = resultado["componentes"]
        self.assertAlmostEqual(
            componentes["adicionalJerarquico"],
            round(componentes["basico"] * 0.55, 2),
        )

    def test_ley_761_horas_solas_hasta_42(self):
        control = evaluar_acumulacion(
            [{"descripcion": "Hora Catedra Nivel Medio", "cantidad": 39, "esHoraCatedra": True}],
            0,
        )
        self.assertEqual(control["estado"], "ok")

        exceso = evaluar_acumulacion(
            [{"descripcion": "Hora Catedra Nivel Medio", "cantidad": 45, "esHoraCatedra": True}],
            0,
        )
        self.assertEqual(exceso["estado"], "advertencia")

        excepcion = evaluar_acumulacion(
            [{"descripcion": "Hora Catedra Nivel Medio", "cantidad": 45, "esHoraCatedra": True}],
            1,
        )
        self.assertEqual(excepcion["maxHorasPermitidas"], 48)

    def test_ley_761_un_simple_y_horas(self):
        cargos = [
            {"descripcion": "Mtro. Nivel EGB - T.S.", "cantidad": 1, "esHoraCatedra": False},
            {"descripcion": "Hora Catedra Nivel Medio", "cantidad": 23, "esHoraCatedra": True},
        ]
        control = evaluar_acumulacion(cargos, 0)
        self.assertEqual(control["estado"], "advertencia")
        self.assertEqual(control["maxHorasPermitidas"], 22)

        excepcion = evaluar_acumulacion(cargos, 1)
        self.assertEqual(excepcion["maxHorasPermitidas"], 28)

    def test_ley_761_directivos_incompatibles_entre_si(self):
        control = evaluar_acumulacion(
            [
                {"descripcion": "Dir. Nivel Inicial - T.C.", "cantidad": 1, "esHoraCatedra": False},
                {"descripcion": "Regente 1a Ens. Tecnica", "cantidad": 1, "esHoraCatedra": False},
            ],
            0,
        )
        self.assertEqual(control["estado"], "advertencia")
        self.assertIn("Art. 4", control["articulos"])


if __name__ == "__main__":
    unittest.main()
