# Proyecto 7: Regresión sobre el límite de crédito (`LIMIT_BAL`)

Proyecto grupal del bootcamp de Data Analytics de Factoría F5 Madrid.  
**Equipo:** Franco y Olena.

Estimamos el límite de crédito (`LIMIT_BAL`) adecuado para un cliente de tarjeta de crédito a partir de su perfil demográfico y de su historial de facturación y pagos de los últimos 6 meses, con el dataset *Default of Credit Card Clients* (UCI).

---

## 1. Problema y caso de uso

**Caso de uso elegido: revisión del límite de un cliente existente.**  
El banco ya dispone del perfil y del historial reciente del cliente y necesita una referencia objetiva para revisar su línea de crédito. Elegimos `LIMIT_BAL` como variable objetivo frente a otras alternativas del dataset:

- `default.payment.next.month` es binaria (clasificación, no regresión) y corresponde a un evento posterior, por lo que se excluye.
- `BILL_AMT1` ofrece un ajuste artificialmente alto porque prácticamente reproduce la factura del mes anterior.

### Datos de partida (`data/UCI_Credit_Card.csv`)
- **Tamaño:** 30.000 clientes y 25 columnas, sin valores nulos, con importes en dólares taiwaneses (`NT$`) de abril a septiembre de 2005.
- **Target (`LIMIT_BAL`):** entre `10.000` y `1.000.000 NT$` (mediana `140.000 NT$`, media `167.484 NT$`, asimetría `0,99`), distribuido en `81` escalones (casi todos múltiplos de `10.000 NT$`, salvo `16.000` en 2 filas y `327.680` en 1 fila). Conservamos los `167` registros por encima del umbral IQR (`525.000 NT$`) porque representan clientes reales con límites altos.

---

## 2. Decisiones de limpieza, preprocesamiento y control de *data leakage*

Toda la lógica compartida entre el notebook y la aplicación reside en `src/preprocesamiento.py`:

- **Prevención de *data leakage*:**
  - Eliminamos `ID` y `default.payment.next.month` (dato futuro).
  - Prohibimos cualquier variable derivada que utilice `LIMIT_BAL` (como ratios de utilización factura/límite).
  - Eliminamos **93 filas repetidas** en las columnas que ve el modelo antes del split (`29.907` filas restantes) para evitar evaluar en `test` observaciones idénticas a las de `train`.
  - Dividimos `80/20` con `random_state=42` (`23.925` filas de entrenamiento y `5.982` de test) y ajustamos todo el preprocesamiento dentro de un `Pipeline` por cada *fold*.
- **Exclusión de `SEX`:** la retiramos del modelo por criterio ético y regulatorio en concesión de crédito, tras comprobar en validación cruzada que el `R2` de validación se mantiene idéntico (`0,364`) con y sin esta variable.
- **Limpieza de códigos y nombres:**
  - Renombramos `PAY_0` a `PAY_1` para alinear la numeración temporal con `BILL_AMT1` y `PAY_AMT1`.
  - Agrupamos los códigos no documentados en "otros": `EDUCATION` (`0`, `5`, `6` → `4`, en 345 filas) y `MARRIAGE` (`0` → `3`, en 54 filas).
  - Conservamos las facturas negativas en `BILL_AMT1..6` (entre `590` y `688` clientes por mes): corresponden a saldo a favor, no a errores.
- **Transformaciones (`crear_preprocesador()`):**
  - Codificamos `EDUCATION` y `MARRIAGE` con `OneHotEncoder`, aplicamos `StandardScaler` a las variables numéricas y descartamos `SEX` (pasando de `22` columnas de entrada a `26` transformadas).
  - Descartamos la transformación logarítmica en los importes tras medir que empeoraba el modelo lineal en validación cruzada (`R2` de `0,364` sin logaritmo frente a `0,241` con logaritmo).

---

## 3. Comparativa de modelos y ajuste con Optuna

Todos los modelos se evaluaron sobre el conjunto de entrenamiento mediante validación cruzada de 5 *folds* (`KFold(n_splits=5, shuffle=True, random_state=42)`), exigiendo que el *overfitting* relativo (`(RMSE_val - RMSE_train) / RMSE_train * 100`) fuese **inferior al 5%**.

| Modelo | RMSE train | RMSE val. | MAE val. | R² train | R² val. | Overfitting | Cumple < 5% |
|---|---:|---:|---:|---:|---:|---:|:---:|
| Dummy (media) | 130.616 | 130.617 | 105.658 | 0,000 | -0,000 | 0,00% | Sí |
| Regresión lineal | 103.885 | 104.144 | 79.937 | 0,367 | 0,364 | 0,25% | Sí |
| Ridge (`alpha=100`) | 103.895 | 104.149 | 79.952 | 0,367 | 0,364 | 0,24% | Sí |
| Árbol sin límite | 11.494 | 137.018 | 93.941 | 0,992 | -0,101 | 1092,13% | No |
| Árbol (`max_depth=5`) | 101.662 | 103.129 | 76.576 | 0,394 | 0,376 | 1,44% | Sí |
| Random Forest por defecto | 37.216 | 96.107 | 69.519 | 0,919 | 0,458 | 158,24% | No |
| Random Forest regularizado (`min_samples_leaf=50`, `max_features=0.33`) | 92.306 | 96.272 | 70.448 | 0,501 | 0,456 | 4,30% | Sí |
| HistGradientBoosting por defecto | 84.315 | 94.059 | 67.569 | 0,583 | 0,481 | 11,56% | No |
| HistGradientBoosting regularizado | 91.074 | 94.471 | 68.426 | 0,514 | 0,477 | 3,73% | Sí |
| XGBoost por defecto | 64.999 | 96.839 | 69.386 | 0,752 | 0,450 | 48,99% | No |
| XGBoost regularizado (`max_depth=4`)* | 91.057 | 94.574 | 68.418 | 0,514 | 0,475 | 3,86% | Sí |
| HistGradientBoosting + Optuna (40 trials) | 90.287 | 94.437 | 68.258 | 0,522 | 0,477 | 4,60% | Sí |
| **XGBoost + Optuna (40 trials, elegido)** | **90.172** | **94.251** | **67.989** | **0,523** | **0,479** | **4,52%** | **Sí** |

\* *Nota de reproducibilidad: al ejecutar `XGBRegressor` con `n_jobs=-1` en procesadores distintos, las métricas de validación de `XGBoost regularizado (max_depth=4)` oscilan dos milésimas entre la sección 10 (`R² = 0,475`, `RMSE = 94.574`, `overfitting = 3,86%`) y la reevaluación de la sección 11.4 (`R² = 0,477`, `RMSE = 94.438`, `overfitting = 3,76%`).*

En Optuna filtramos los ensayos para elegir el menor RMSE de validación únicamente entre aquellos cuyo *overfitting* fuera inferior al 5% (`9` de `40` en Gradient Boosting; `11` de `40` en XGBoost). La prueba global con menor RMSE (`93.493`) alcanzaba un `14,46%` de *overfitting* y quedó descartada.

---

## 4. Modelo final y evaluación única en `test`

Reentrenamos el pipeline completo con `XGBRegressor` (`max_depth=6`, `learning_rate=0.017`, `n_estimators=415`, `min_child_weight=99`, `subsample=0.69`, `colsample_bytree=0.63`, `reg_lambda=24.6`) sobre todo `train` y lo evaluamos una única vez sobre `test`:

| Conjunto | RMSE (NT$) | MAE (NT$) | R² |
|---|---:|---:|---:|
| Train | 90.486 | 65.288 | 0,520 |
| **Test** | **88.233** | **64.496** | **0,511** |

- **Overfitting (RMSE test frente a train):** **`-2,49%`** (cumple el límite del 5%).
- **Importancia por permutación en `test`:** el bloque con mayor peso es el **Perfil** (`AGE`, `EDUCATION`, `MARRIAGE`: `0,144`), seguido de **Facturas** (`0,093`), **Pagos** (`0,087`) y **Estado de pago** (`0,045`). Las tres variables individuales más influyentes son `AGE`, `BILL_AMT1` y `EDUCATION`.
- **Análisis de residuos:** media de `-3.445 NT$` y mediana del error absoluto de `46.781 NT$`; un `62,9%` de las predicciones queda por encima del valor real y en límites muy altos el modelo tiende a quedarse corto.
- **Limitaciones:** un `R²` de `0,511` refleja que casi la mitad de la variabilidad del límite depende de información externa a este dataset (ingresos declarados, antigüedad laboral u otros productos financieros). Los datos proceden de un banco de Taiwán en 2005 y el modelo solo aplica a revisión de clientes existentes con historial.
- El pipeline completo queda guardado en `models/modelo_final.joblib` (`1.017 KB`).

---

## 5. Aplicación en Streamlit (`app/app.py`)

La aplicación web integra el análisis exploratorio y la inferencia sobre el modelo final en tres vistas:

1. **Inicio:** resumen del problema, tamaño de la muestra y accesos directos.
2. **Dashboard:** filtros interactivos por educación, estado civil, edad, límite y estado de pago (`PAY_0`), distribución de `LIMIT_BAL`, comparativas por perfil e historial de pago, correlaciones con `LIMIT_BAL` y métricas de evaluación en `test` del modelo final.
3. **Predicción y feedback:** formulario con perfil del cliente y bloque plegable para los 6 meses de historial (inicializado con las medianas del dataset). Devuelve el límite recomendado redondeado al múltiplo de `10.000 NT$` más cercano (mínimo `10.000 NT$`), muestra el margen de error típico (`MAE` de test) y permite registrar la valoración del usuario y el límite real en `data/feedback.csv`.

---

## 6. Estructura del repositorio

```text
app/
  app.py                     Punto de entrada y navegación de Streamlit
  datos.py                   Carga en caché y agregaciones para el dashboard
  modelo.py                  Carga de models/modelo_final.joblib, predicción y feedback
  tema.py                    Estilos y componentes visuales
  app_pages/                 Vistas Inicio, Dashboard y Predicción
data/
  UCI_Credit_Card.csv        Dataset original (30.000 filas, 25 columnas)
docs/
  PLAN.md                    Plan técnico y criterios de validación
  TAREAS.md                  Reparto de tareas, ramas y estado
models/
  modelo_final.joblib        Pipeline entrenado (preprocesamiento + XGBoost)
notebooks/
  proyecto_regresion.ipynb   Notebook completo del proyecto (secciones 0 a 12)
src/
  preprocesamiento.py        Transformadores propios y creación del pipeline
tests/
  test_preprocesamiento.py   Pruebas unitarias de limpieza y pipeline
  test_modelo.py             Pruebas de carga, redondeo y registro de feedback
OBSERVACIONES.md             Registro de decisiones y comunicación del equipo
requirements.txt             Dependencias fijadas del proyecto
```

---

## 7. Instalación, ejecución y tests

### Requisitos e instalación
En Windows, si `python` apunta al alias de Microsoft Store, sustitúyelo por `py`:

```powershell
git clone https://github.com/Bootcamp-DA-P3/ML_project_UCI_Credit_Card_data.git
cd ML_project_UCI_Credit_Card_data
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ejecutar la aplicación de Streamlit
Desde la raíz del repositorio (con el entorno activado):

```powershell
streamlit run app/app.py
```

### Ejecutar los tests unitarios
Desde la raíz del repositorio (`14` pruebas sobre `src/preprocesamiento.py` y `app/modelo.py`):

```powershell
python -m pytest tests
```

---

## 8. Flujo de trabajo del equipo

Trabajamos con ramas por tarea (`nombre/descripcion`) e integración en `main` mediante *pull request*. El notebook único (`notebooks/proyecto_regresion.ipynb`) se trabajó por turnos coordinados en `docs/TAREAS.md` y `OBSERVACIONES.md`.
