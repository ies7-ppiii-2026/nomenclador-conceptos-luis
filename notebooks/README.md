# Notebooks

Las notebooks se organizan por etapa del trabajo. Cada notebook debe responder una pregunta o probar una alternativa concreta.

## Estructura

```text
01_data_analysis/        analisis inicial, calidad de datos e hipotesis
02_feature_engineering/  preparacion de datos y alternativas de features
03_experiments/          experimentos de modelado
04_evaluation/           comparacion, metricas y lectura de negocio
```

## Convencion

- Usar formato Jupytext `py:percent`.
- Mantener nombres descriptivos y ordenados con prefijos numericos.
- Si una notebook queda descartada, eliminarla del repo.
- Si una funcion se repite o se vuelve importante, moverla a `src/project_name/`.
