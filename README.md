# nomenclador-conceptos-luis

Proyecto para mapear codigos y conceptos de distintos sistemas.

Proyecto de data science **notebook-first**, con entorno reproducible, JupyterLab, Jupytext y separacion entre notebooks exploratorias y codigo reutilizable.

## Objetivo

Este template sirve para iniciar proyectos de data science donde se quiere:

- trabajar con notebooks versionables como `.py:percent`
- mantener codigo reutilizable en `src/`
- separar datos, modelos y reportes generados
- usar `uv` para reproducibilidad
- permitir colaboracion con Jupyter cuando haga falta

## Estructura

```text
notebooks/   exploracion, feature engineering, experimentos y evaluacion
src/         paquete Python importable del proyecto
tests/       pruebas automatizadas para codigo reusable
data/        datos locales no versionados
models/      modelos entrenados o serializados no versionados
reports/     figuras, tablas y salidas comunicables
docs/        documentacion libre del proyecto
```

## Setup

```bash
uv sync
```

## Levantar JupyterLab

```bash
uv run jupyter lab . \
  --ip=127.0.0.1 \
  --ServerApp.port=12001 \
  --ServerApp.port_retries=0 \
  --IdentityProvider.token="${JUPYTER_TOKEN:-}"
```

`JUPYTER_TOKEN` es opcional. Si no se configura, el comando funciona sin token.
Para usar un token explícito:

```bash
export JUPYTER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Para permitir acceso desde otra maquina en la misma red:

```bash
uv run jupyter lab . \
  --ip=0.0.0.0 \
  --ServerApp.port=12001 \
  --ServerApp.port_retries=0 \
  --IdentityProvider.token="${JUPYTER_TOKEN:-}"
```

No usar un token vacio en redes compartidas: configurar `JUPYTER_TOKEN` antes de
levantar el servidor. Jupyter permite ejecutar codigo en la maquina host.

## Levantar Jupyter Notebook

```bash
uv run jupyter notebook . \
  --ip=127.0.0.1 \
  --ServerApp.port=12001 \
  --ServerApp.port_retries=0 \
  --IdentityProvider.token="${JUPYTER_TOKEN:-}"
```

Se puede cambiar manualmente entre interfaces:

- `http://127.0.0.1:12001/lab`
- `http://127.0.0.1:12001/tree`

## Flujo recomendado

1. Crear notebooks en `notebooks/` usando Jupytext percent.
2. Mover logica repetida o importante a `src/nomenclador_conceptos_luis/`.
3. Agregar pruebas en `tests/` para funciones reutilizables.
4. Guardar datos locales en `data/raw/` o `data/processed/` sin versionarlos.
5. Guardar resultados comunicables en `reports/`.

## Convencion de notebooks

```text
notebooks/
  01_data_analysis/
  02_feature_engineering/
  03_experiments/
  04_evaluation/
```

Cada notebook debe responder una pregunta o probar una alternativa concreta. Si una notebook queda descartada, eliminarla del repo.

## Codigo reutilizable

El paquete Python vive en:

```text
src/nomenclador_conceptos_luis/
```

El nombre del paquete debe ser importable en Python. Convencion recomendada:

```text
customer-churn-prediction/      # repo en kebab-case
src/customer_churn_prediction/  # paquete en snake_case
```

## Jupytext

La configuracion esta en:

```text
jupytext.toml
```

Con:

```toml
formats = "ipynb,py:percent"
```

Esto permite que notebooks `.ipynb` se sincronicen con scripts `.py` en formato percent. El repositorio ignora `*.ipynb`; se versiona la representacion `.py`.

## Verificaciones

```bash
uv run pytest
uv run ruff check .
```

Este repositorio es un template Copier: el `pyproject.toml` y algunos imports
contienen placeholders Jinja, por lo que el template original no puede ejecutar
`pytest` directamente. La validacion se hace generando primero un proyecto real
con Copier y ejecutando las verificaciones sobre ese proyecto generado.
