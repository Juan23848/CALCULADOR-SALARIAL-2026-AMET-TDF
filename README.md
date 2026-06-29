# Simulador Salarial Docente AMET Tierra del Fuego

Aplicacion Streamlit para estimar salario docente a partir de codigo de cargo,
puntaje, Valor Indice, antiguedad, ubicacion y descuentos basicos.
Por defecto inicia con el Valor Indice inferido de recibos de mayo 2026.
Ese Valor Indice de mayo 2026 es el punto de partida para futuras
modificaciones del decreto; los aumentos no se aplican automaticamente todavia.

La carga de cargos se hace agrupando por tipo/codigo. Por ejemplo: todas las
horas del codigo 852 en una sola linea, todas las del 312 en otra, etc. El
selector permite escribir codigo o descripcion para filtrar opciones.
La ubicacion se elige al inicio porque define el porcentaje de zona y algunos
ajustes puntuales, como el codigo 421 en Tolhuin.

Incluye un control orientativo de acumulacion segun Ley Provincial 761. Este
control advierte posibles excesos, pero no bloquea el calculo porque la ley
preve excepciones y porque el simulador no conoce actos publicos, escuelas ni
superposicion horaria.

## Como ejecutar

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Si no existe el entorno virtual:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Tambien se puede iniciar con:

```powershell
.\run_streamlit.bat
```

## Reglas de calculo aplicadas

- Basico = puntajeCargo x valorIndice.
- El codigo del cargo solo identifica el registro. Nunca se usa como puntaje.
- Antiguedad = Basico x porcentaje segun tabla configurable.
- Funcion Docente = Basico x 230%.
- Transformacion Educativa = Basico x 123%.
- Bonificacion Docente se aplica automaticamente por codigo cuando corresponde,
  segun la planilla de codigos aportada.
- Bonificacion Docente = Basico x 27,75%.
- Excepcion validada con recibo de Tolhuin: codigo 421 en Tolhuin liquida
  Bonificacion Docente al 23,25%.
- Adicional Jerarquico se aplica automaticamente por codigo cuando corresponde.
- Adicional Jerarquico = Basico x 55%.
- Zona = (Basico + Antiguedad + Funcion Docente + Transformacion Educativa + Bonificacion Docente + Adicional Jerarquico) x porcentaje de ubicacion.
- Porcentaje de zona: Ushuaia 100%, Rio Grande 100%, Tolhuin 120% y Escuelas
  Rurales 120%. Escuelas Rurales incluye Estancia Sara, Lago Escondido, San
  Sebastian, Puerto Almanza y Escuela Antartica Nro. 38.
- Asignacion Hora Catedra se calcula automaticamente como item remunerativo.
  Segun el acta paritaria del 30/10/2025, usa el valor remunerativo completo
  de una hora catedra codigo 221 con la antiguedad correspondiente y aplica
  equivalencias: horas catedra / 21, un cargo simple = 1, cargo completo = 2,
  con tope de dos equivalentes por docente. En combinaciones, el cargo consume
  primero su equivalente y las horas catedra completan proporcionalmente hasta
  el tope.
- Bruto remunerativo = Basico + Antiguedad + Funcion Docente + Zona + Transformacion Educativa + Bonificacion Docente + Adicional Jerarquico + Asignacion Hora Catedra.
- Descuentos obligatorios: Jubilacion = Bruto remunerativo x 16%, Obra
  social = Bruto remunerativo x 3%, y Seguro de vida obligatorio = $2.750.
  No son opciones de usuario; si cambian por ley o acuerdo, se actualizan en
  `configuracion.py`.
- Descuento sindical opcional: permite seleccionar hasta 3 sindicatos. AMET
  descuenta 1,5% del bruto remunerativo y 1,5% del FOID; ATE descuenta 2,2%
  del bruto remunerativo; SUTEF descuenta 2% del bruto remunerativo y 2% del
  FOID; UDA descuenta 1,5% del bruto remunerativo y 1,5% del FOID; UDAF
  descuenta 1,3% del bruto remunerativo y 1,3% del FOID; OTROS descuenta 2%
  del bruto remunerativo y 2% del FOID.
- FOID no remunerativo: $56.000 por cargo simple o tiempo simple, con tope
  maximo de dos cargos simples ($112.000). Para horas catedra se calcula
  $56.000 / 19 por hora, con tope de 38 horas si no hay otros cargos.
- Refuerzo Ayuda Material Didactico no remunerativo: $71.300 por cargo simple
  o tiempo simple, con tope maximo de dos cargos simples ($142.600). Para
  horas catedra se calcula $71.300 / 19 por hora, con tope de 38 horas si no
  hay otros cargos.
- Un cargo de tiempo completo o jornada completa computa como dos cargos
  simples y satura ambos no remunerativos.
- Si se carga un cargo simple y horas catedra, se liquida un cargo simple mas
  horas hasta completar 19 horas. Si se cargan dos cargos simples y horas, las
  horas no suman FOID ni material porque el tope ya esta saturado.
- El campo "Otros no remunerativos (sin FOID/material)" queda solo para importes
  excepcionales o diferencias del recibo que no sean FOID/material automatico.
  Si el recibo solo tiene FOID y Refuerzo Ayuda Material Didactico, debe quedar
  en cero porque esos dos conceptos ya se calculan automaticamente.
- El campo opcional "Proporcional vacaciones / ajuste remunerativo especial"
  queda para items remunerativos excepcionales del recibo, por ejemplo el item
  215. Suma al bruto remunerativo y por lo tanto integra la base de descuentos.
- Neto final = Bruto remunerativo - descuentos + no remunerativos automaticos + otros no remunerativos.
- El calculo redondea cada concepto a centavos para aproximarse al criterio del recibo oficial.
- Punto de partida para aumentos futuros: Valor Indice mayo 2026, sin aplicar
  todavia las modificaciones del Decreto Provincial 1059/26.

## Control Ley Provincial 761

Reglas orientativas incorporadas:

- Solo horas catedra: hasta 42 horas en regimen comun.
- Un cargo de jornada simple: hasta 22 horas catedra.
- Dos cargos de jornada simple: hasta 6 horas catedra.
- Un cargo de jornada completa: hasta 16 horas catedra.
- Primera excepcion Art. 7: eleva los topes a 48 horas, 28 horas con un simple,
  12 horas con dos simples y 22 horas con un completo.
- Segunda excepcion Art. 7: eleva los topes a 54 horas, 34 horas con un simple,
  18 horas con dos simples y 28 horas con un completo.
- Cargos directivos o jerarquicos entre si generan advertencia de incompatibilidad.
- Directivo/jerarquico combinado con otros cargos u horas genera advertencia para
  revisar establecimiento, horarios y declaracion jurada.

## Verificacion

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_calculos.py
```

Pruebas incluidas:

- El codigo 212 usa su puntaje real y no el numero 212 como puntaje.
- Zona incluye Transformacion Educativa segun recibo real de mayo 2026.
- Zona permite seleccionar ubicacion y calcula Tolhuin al 120%.
- Descuentos obligatorios por defecto: jubilacion 16%, obra social 3% y seguro
  de vida obligatorio de $2.750.
- Descuento sindical opcional: AMET, ATE, SUTEF, UDA, UDAF y OTROS, con bases
  diferenciadas para bruto remunerativo y FOID.
- Recibos reales de mayo 2026 reproducidos con tolerancia menor a $1.
- Recibo de febrero 2026 con item 215 validado: el proporcional vacaciones se
  carga como ajuste remunerativo especial para reproducir el bruto del recibo.
- Busqueda por codigo, descripcion y alias comunes como "horas catedras" o
  "maestra".
- Bonificacion Docente automatica: codigos exactos de la planilla
  "COD. CARGOS Y HORAS QUE LIQUIDAN BONIFICACION.xlsx", configurable desde
  `configuracion.py`. El codigo 852 no se bonifica por contexto; EDEI se carga
  con su codigo especifico 312, que ya liquida la bonificacion.
- Asignacion Hora Catedra automatica: reproduce los importes de recibos reales
  para horas catedra, cargos simples, cargos jerarquicos y combinaciones al
  sumar el item 412 al bruto remunerativo antes de descuentos. Incluye pruebas
  del criterio del acta 30/10/2025: cargo simple + horas proporcionales sobre
  21, y cargo completo saturando el tope de dos equivalentes.
- Adicional Jerarquico automatico: 88 codigos del Anexo I de la Resolucion
  M.Ed. 2001/16. Se puede ajustar desde `configuracion.py` con agregados o
  exclusiones puntuales. La regla general vigente del simulador es el 55% del
  basico para los cargos jerarquicos.
- No remunerativos automaticos: FOID y Refuerzo Ayuda Material Didactico se
  calculan por equivalentes de cargo simple, con topes para horas, cargos
  simples, combinaciones y tiempo completo.
- Control Ley 761: horas solas, un cargo simple con horas, excepciones Art. 7
  y directivos incompatibles.
