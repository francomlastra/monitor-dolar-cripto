# Decisiones de diseño

Notas sobre por qué el proyecto está armado así, y qué mejoraría en una
segunda iteración.

## Almacenamiento: SQLite versionado en el repo

- **¿Por qué SQLite y no CSV?** El requisito es una serie temporal append-only
  consultable. SQLite da esquema tipado, índices y SQL real sin ningún servidor,
  y viaja como un archivo. Los CSV siguen existiendo, pero como *export* de
  conveniencia (`data/exports/`), no como fuente de verdad — así no hay dos
  versiones de los datos que puedan divergir.
- **¿Por qué commitear la base al repo?** Con 30 filas por día, la base crece
  ~1 MB por año: trivial para git. A cambio, el repo es 100% autocontenido
  (datos + código + historia en un solo lugar) y cualquiera que lo clone tiene
  el dataset completo. El histórico de commits además documenta cada corrida.
- **¿Cuándo dejaría de funcionar?** Si la frecuencia subiera a minutos o se
  agregaran muchas fuentes, git empezaría a sufrir (la base es binaria, cada
  commit guarda una copia). Ahí migraría a un Postgres gratuito (Supabase/Neon)
  o a archivos Parquet particionados por mes.

## Esquema: formato largo, append-only

- Una fila por (corrida, tipo de dólar) y por (corrida, moneda), en vez de una
  columna por tipo. Agregar un tipo de dólar nuevo no cambia el esquema.
- `timestamp_utc` es el momento de la corrida y es el mismo para todas las
  tablas de esa corrida: cruzar dólar y cripto es un join exacto, sin ventanas.
- Se guarda también `fecha_fuente` (cuándo actualizó DolarAPI su valor): si el
  pipeline corre un domingo, el dato del oficial puede ser del viernes — esa
  diferencia es visible en los datos en vez de estar oculta.
- Timestamps siempre en UTC en la base; la conversión a hora argentina es
  responsabilidad del análisis. Evita toda ambigüedad de zonas horarias.

## Extracción: fallas aisladas por fuente

- Cada fuente tiene su función de extracción y de guardado, y el pipeline las
  recorre desde un registro (`FUENTES`). **Agregar riesgo país o inflación es:
  una función en `extract.py`, una tabla + insert en `db.py`, una línea en
  `FUENTES`.** Nada más que tocar.
- Los reintentos (3, con backoff 5/10/20 s) viven en un solo lugar
  (`_get_json`). Ante un 429 de rate limit o un timeout puntual, la corrida se
  salva sola; si la API está realmente caída, la excepción sube y el pipeline
  la registra y sigue con la fuente siguiente.
- El pipeline devuelve exit code 1 solo si **ninguna** fuente respondió, así el
  workflow marca la corrida en rojo cuando de verdad no hubo datos.

## Rate limits de CoinGecko

Según su documentación, el acceso sin key tiene límite por IP (compartida —
en GitHub Actions la IP del runner se comparte con otros proyectos) y el plan
Demo gratuito con key da un margen holgado con 10.000 llamadas/mes. Este
proyecto hace **3 llamadas por día (~90/mes)**: órdenes de magnitud abajo de
cualquier límite. El único riesgo real es que la IP compartida del runner
esté saturada por *otros* usuarios; lo mitigan los reintentos con backoff y,
si se volviera recurrente, `extract.py` ya soporta una key Demo opcional vía
la variable de entorno `COINGECKO_API_KEY` (sin tocar código).

## GitHub Actions

- Cron en UTC: `0 12,16,21 * * *` = 9:00, 13:00 y 18:00 en Argentina (UTC-3,
  sin horario de verano desde 2009). Mañana, mediodía y después del cierre
  del mercado cambiario.
- Los crons de GitHub pueden ejecutarse con minutos de demora; para esta
  frecuencia es irrelevante.
- GitHub desactiva los workflows programados tras 60 días sin actividad en el
  repo — como este workflow commitea datos tres veces por día, se mantiene
  vivo solo.
- `permissions: contents: write` es el permiso mínimo necesario para pushear.

## Mejoras para una segunda iteración

1. **Tests automatizados**: `pytest` con la librería `responses` para mockear
   las APIs (respuestas válidas, timeouts, JSON malformado) y una base SQLite
   en memoria para probar los inserts y el export. Correrlos en el propio
   workflow antes del pipeline.
2. **Fuentes nuevas**: riesgo país e inflación (ArgentinaDatos API expone
   ambos sin key), y tasas de plazo fijo para comparar rendimientos en pesos
   contra la evolución del dólar.
3. **Validación de datos**: chequeos de sanidad antes de insertar (precios > 0,
   brecha dentro de rangos plausibles, timestamp de la fuente no más viejo que
   N días) con una tabla de anomalías en vez de descartar silenciosamente.
4. **Dashboard**: una página estática (GitHub Pages) o Streamlit Cloud que lea
   los CSV del repo y muestre las brechas actualizadas, para que el proyecto
   tenga una cara visible sin clonar nada.
5. **Alertas**: un paso opcional del workflow que avise (Telegram/Discord)
   cuando la brecha blue-oficial cruce un umbral — convierte el dataset en
   una herramienta.
