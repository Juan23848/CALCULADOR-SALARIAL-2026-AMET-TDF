# Publicar el simulador en Streamlit Community Cloud

## Archivos necesarios

Subir al repositorio:

- `app.py`
- `requirements.txt`
- `cargos_mayo_2025.xlsx`
- `logo_amet_tdf_transparente.png`
- todos los módulos `.py` del simulador

No subir:

- `.venv/`
- `__pycache__/`
- archivos `.log`
- archivos `.pyc`

## Pasos

1. Crear un repositorio en GitHub, por ejemplo `simulador-salarial-amet-tdf`.
2. Subir los archivos del simulador al repositorio.
3. Entrar a https://share.streamlit.io/.
4. Elegir `Create app`.
5. Seleccionar el repositorio y la rama principal.
6. En `Main file path`, escribir `app.py`.
7. Presionar `Deploy`.

El enlace `localhost:8501` solo funciona en esta computadora. El enlace final de Streamlit Cloud funciona desde cualquier computadora o celular con internet.
