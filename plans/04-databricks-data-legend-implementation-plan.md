# План реализации Data Legend: Facility Trust Desk

## 1. Результат и границы проекта

### 1.1. Что строим

Строим **Facility Trust Desk** — Databricks App для нетехнического планировщика НКО, который отвечает на узкий, но критичный вопрос: «насколько хорошо данные подтверждают, что учреждение действительно обладает заявленной возможностью?»

Основной пользовательский путь:

1. Планировщик выбирает медицинскую возможность: ICU, maternity, emergency, oncology, trauma или NICU.
2. Выбирает регион: штат, город, район или PIN — в пределах реально доступных полей датасета.
3. Получает ранжированный список учреждений с объяснимой оценкой силы доказательств, уровнем полноты данных и предупреждениями.
4. Открывает учреждение и видит точные цитаты из исходных полей, источник, выявленные противоречия и разложение оценки.
5. Подтверждает или переопределяет машинную оценку, обязательно добавляя заметку.
6. После перезагрузки приложения видит сохранённое решение и историю изменений.

### 1.2. Почему выбран этот трек

PDF требует выбрать **ровно один** mission track и довести его минимальный workflow до конца. Facility Trust Desk выбран как наиболее надёжный вертикальный срез через три обязательных требования:

- Evidence Engine: каждое решение связано с исходным текстом;
- Trust Scorer: ранжирование учитывает подтверждения, противоречия и неопределённость;
- Planner's Workflow: есть понятный интерфейс и персистентное переопределение с заметкой.

Этот трек не требует делать геокодирование, маршрутизацию пациента или статистически корректную оценку регионального покрытия обязательной частью MVP. Это уменьшает риск не успеть за 48 часов и концентрирует работу на 65% оценки за Evidence & Trust и Product Judgment.

### 1.3. Формулировка продукта

> Мы помогаем планировщикам здравоохранения проверять заявления медицинских учреждений с помощью точных цитат, объяснимой силы доказательств и сохраняемых экспертных решений.

### 1.4. Что сознательно не входит в MVP

- все четыре mission track одновременно;
- пациентские или клинические рекомендации;
- утверждение, что `trust_score` доказывает реальную клиническую способность учреждения;
- полноценная карта медицинских пустынь;
- автоматическая калибровка вероятности без размеченной истины;
- обязательная зависимость от Genie, Agent Bricks Supervisor или внешних API;
- сложная авторизация и многотенантность;
- обработка свободного чат-запроса как основной интерфейс.

## 2. Критерии готовности MVP

MVP считается готовым только когда в Databricks Free Edition пройден следующий сценарий:

1. Живое приложение открывается по URL после свежего запуска.
2. Выбор capability и региона возвращает учреждения из 10k-датасета.
3. Результаты ранжируются по объяснимой силе доказательств, а не только по совпадению ключевого слова.
4. Для каждого результата показаны:
   - итоговая оценка и её категория;
   - отдельная полнота данных;
   - положительные сигналы;
   - противоречия и пробелы;
   - точные цитаты, имя исходного поля, идентификатор строки и URL источника, если он есть.
5. Отсутствующее поле не трактуется как доказательство отсутствия capability.
6. Пользователь может сохранить override и непустую заметку.
7. Override сохраняется в Lakebase и виден после новой сессии или redeploy приложения.
8. MLflow trace показывает минимум цепочку `query -> retrieve -> score -> rank`; для пакетного извлечения — `extract -> validate -> persist`.
9. Целевые unit/integration/E2E-тесты проходят, а deploy smoke test выполнен непосредственно в Free Edition.
10. Подготовлены минутный сценарий демо и резервная запись.

## 3. Важные ограничения Databricks Free Edition

Перед началом feature-разработки нужен короткий capability gate в целевом workspace. Документация описывает общие возможности, но конкретная доступность зависит от региона и workspace.

Проверить и записать результат:

| Возможность | Что проверить | Решение при недоступности |
|---|---|---|
| Databricks Apps | skeleton app разворачивается и отвечает на health check | блокер live submission; исправить первым |
| SQL warehouse | доступен единственный serverless warehouse до 2X-Small | минимизировать запросы, заранее прогреть перед демо |
| Foundation Model API | виден хотя бы один pay-per-token endpoint и выполняется тестовый structured-output запрос | использовать детерминированный rule-based extractor для demo slice |
| AI Search | создаётся один standard endpoint и Delta Sync index | SQL-фильтрация и заранее извлечённые синонимы |
| Lakebase | создаётся один project, приложение подключается и выполняет CRUD | временный Delta fallback только для разработки; Lakebase восстановить до submission |
| MLflow 3 | trace появляется в experiment/UC trace tables | ручное instrumentation и сокращённый trace |
| Genie | доступен поверх curated views | оставить stretch goal |
| Agent Bricks | доступны нужные tiles, region и usage policy | не включать в critical path |

Учитываем ограничения:

- только serverless compute и fair-use quotas;
- до трёх Apps, приложение останавливается через 24 часа после start/update/redeploy;
- один Lakebase project;
- один AI Search endpoint и одна search unit; Direct Vector Access в Free Edition не поддерживается;
- AI Search должен использовать Delta Sync index, source Delta table с Change Data Feed и предпочтительно Triggered Sync;
- один SQL warehouse, максимум 2X-Small;
- до пяти одновременно выполняемых job tasks;
- локальная файловая система и память процесса App не являются персистентными;
- provisioned throughput для Foundation Model API недоступен, модель выбирается из реально видимых pay-per-token endpoints;
- Knowledge Assistant в Free Edition не поддерживается;
- runtime-обращения к внешним доменам могут блокироваться egress-политикой.

Практический вывод: все входные данные, производные таблицы, embeddings и demo-сценарии готовятся заранее; пользовательский запрос не запускает тяжёлую пакетную обработку.

## 4. Архитектура

```text
India 10k / Marketplace
        |
        v
Unity Catalog + Delta
raw_facilities -> normalized_facilities -> evidence_spans
                                      \-> facility_assessments
                                      \-> search_chunks (CDF)
                                                |
                                                v
                                   AI Search Delta Sync index
                                                |
Planner -> Databricks App (Streamlit) -> query/rank service
                 |                    -> evidence detail
                 |                    -> MLflow 3 traces
                 v
              Lakebase
      overrides + notes + audit history
```

### 4.1. Технологический выбор

- **UI:** Streamlit внутри Databricks App — минимальный объём кода и быстрый deploy.
- **Аналитическое хранение:** Unity Catalog + Delta tables.
- **Извлечение:** пакетный Python/SQL pipeline с Foundation Model API structured output; rule-based fallback.
- **Поиск:** структурные фильтры SQL обязательны; один AI Search Delta Sync index добавляет semantic/hybrid matching.
- **Оценка:** детерминированный, версионируемый Python scorer поверх извлечённых evidence signals.
- **Пользовательское состояние:** Lakebase/PostgreSQL.
- **Наблюдаемость:** MLflow 3 tracing и агрегированные latency/error/cost metrics.
- **Деплой:** Databricks App, тяжёлая обработка выполняется Jobs/SQL/Model Serving, а не в процессе UI.

### 4.2. Предлагаемая структура репозитория

```text
app.yaml
requirements.txt
README.md
app/
  app.py
  pages/
  components/
src/
  config.py
  data/
    ingest.py
    normalize.py
    profiling.py
  evidence/
    taxonomy.py
    sentence_splitter.py
    extractor.py
    schemas.py
    validator.py
  trust/
    scorer.py
    ranking.py
    explanations.py
  search/
    repository.py
    ai_search.py
  persistence/
    lakebase.py
    models.py
  observability/
    tracing.py
sql/
  001_analytics_tables.sql
  002_lakebase_schema.sql
  003_gold_views.sql
notebooks/
  00_capability_gate.py
  01_ingest_and_profile.py
  02_extract_evidence.py
  03_build_assessments.py
  04_build_search_index.py
tests/
  fixtures/
  unit/
  integration/
  e2e/
docs/
  architecture.md
  scoring.md
  demo.md
  operations.md
```

Имена Databricks-конфигов нужно сверить на первом deploy spike; в репозитории пока нет существующего приложения или соглашений, которые требуется сохранять.

## 5. Контракт данных

### 5.1. Bronze/raw

`raw_facilities`

- полный неизменённый снимок India 10k;
- `facility_id` — стабильный идентификатор из источника либо детерминированный hash устойчивых полей;
- `source_row_id`;
- все 51 исходное поле без потери текста;
- `source_url`;
- `ingested_at`, `dataset_version`, `row_hash`.

Raw-таблица не исправляется вручную. Все нормализации и решения хранятся отдельно.

### 5.2. Silver/normalized

`normalized_facilities`

- нормализованные state/city/district/PIN;
- исходные и нормализованные значения сохраняются рядом;
- приведённые к единому виду текстовые поля;
- вычисленная доступность каждого исходного поля;
- `data_completeness_score` и карта missing fields;
- никаких выводов о capability на этом уровне.

`capability_taxonomy`

- шесть capability MVP;
- синонимы и допустимые сокращения;
- положительные сигналы;
- противоречащие сигналы;
- supportive signals по полям;
- версия таксономии.

Медицинские prerequisite rules нельзя выдавать за клинический стандарт без проверенного источника и экспертной валидации. В MVP они формулируются как **сигналы внутренней согласованности данных**.

### 5.3. Evidence layer

`evidence_spans`

| Поле | Назначение |
|---|---|
| `evidence_id` | стабильный ID evidence |
| `facility_id` | связь с учреждением |
| `capability_code` | к какой capability относится |
| `source_field` | description/capability/procedure/equipment/etc. |
| `source_row_id` | ссылка на исходную строку |
| `exact_quote` | точная цитата |
| `char_start`, `char_end` | позиция цитаты в оригинале |
| `sentence_index` | номер предложения |
| `source_url` | внешний источник, если есть |
| `signal_type` | claim/support/contradiction/gap |
| `extraction_confidence` | уверенность extractor, не клиническая вероятность |
| `extractor_version`, `prompt_version`, `model_name` | воспроизводимость |
| `validated` | прошла ли цитата поствалидацию |

Критический инвариант: `exact_quote` должна быть точной подстрокой исходного поля. Если это не так, evidence запрещено показывать и запись отправляется в quarantine/review queue.

### 5.4. Assessment layer

`facility_assessments`

- `facility_id`, `capability_code`;
- `evidence_strength_score` 0–100;
- `data_completeness_score` 0–100;
- `conservative_score` для ранжирования;
- `confidence_band`: strong / moderate / weak / insufficient-data;
- `positive_signal_count`, `independent_field_count`;
- `contradiction_count`, `unvalidated_evidence_count`;
- `lower_bound`, `upper_bound` из sensitivity analysis;
- JSON breakdown каждого вклада;
- `scorer_version`, `taxonomy_version`, `computed_at`.

### 5.5. Lakebase

`assessment_overrides`

- `override_id`;
- `facility_id`, `capability_code`;
- исходный assessment ID и scorer version;
- решение пользователя: confirmed / needs-review / rejected / overridden;
- необязательное пользовательское значение категории;
- обязательная непустая `note`;
- `actor_id` или стабильный demo user/session ID;
- `created_at`, `updated_at`;
- `supersedes_override_id` для audit trail.

История не перезаписывается: новое решение создаёт новое событие, а current view выбирает последнее. Аналитические facility data в Lakebase не дублируются.

## 6. Evidence Engine

### 6.1. Сначала профиль данных

После получения датасета:

1. Зафиксировать точные имена и типы всех 51 колонок.
2. Проверить уникальность предполагаемого ID.
3. Посчитать фактическую полноту каждого поля и сверить с brief.
4. Исследовать форматы geography и source URL.
5. Выбрать по 10–20 representative rows для каждой capability:
   - сильное подтверждение;
   - только claim;
   - противоречие;
   - мало данных;
   - неоднозначные синонимы.
6. Сохранить обезличенные golden fixtures для тестов и демо.

### 6.2. Пакетное извлечение

Для каждой строки:

1. Разбить каждое текстовое поле на предложения, сохранив offsets.
2. Сначала выполнить дешёвый candidate recall по таксономии и синонимам.
3. Отправлять в model API только релевантные предложения и соседний контекст.
4. Требовать structured JSON по Pydantic/JSON Schema:
   - capability;
   - тип сигнала;
   - exact quote;
   - краткая причина;
   - field name;
   - extraction confidence.
5. Проверить schema, allowed enums и точное присутствие quote в source field.
6. Восстановить offsets детерминированно.
7. Дедуплицировать одинаковые evidence spans.
8. Записать валидные evidence; ошибки и неподтверждённые цитаты — в quarantine.
9. Кэшировать по `row_hash + extractor_version`, чтобы не тратить quota повторно.

На 10k строках сначала обработать demo slice, затем весь датасет. Concurrency ограничить; для 429 применять exponential backoff с jitter. Не фиксировать конкретную модель до capability gate.

### 6.3. Детерминированный fallback

Fallback extractor должен:

- искать только контролируемые синонимы;
- возвращать полное предложение как evidence;
- никогда не создавать текст, которого нет в источнике;
- отмечать результат как `rule_based`;
- поддерживать минимальный live demo при исчерпании model quota.

## 7. Trust Scorer

### 7.1. Что означает score

`evidence_strength_score` — это **сила и согласованность доказательств в датасете**, а не вероятность наличия реальной клинической возможности. Это должно быть явно написано в UI.

Отдельно показываются:

- сила доказательств;
- полнота данных;
- противоречия;
- диапазон неопределённости;
- человеческий override.

### 7.2. Компоненты оценки

Начальная версия весов, которую затем фиксируют тестами и документируют:

| Компонент | Пример вклада |
|---|---:|
| Прямой claim capability | до +20 |
| Подтверждение в narrative description | до +25 |
| Подтверждение в независимом втором/третьем поле | до +20 |
| Supportive equipment/procedure/staff signal | до +20 |
| Проверяемый source URL/происхождение | до +10 |
| Согласованность нескольких независимых сигналов | до +5 |
| Явное противоречие | до −30 |
| Подозрительный/невалидный evidence | до −20 |
| Claim без какого-либо подтверждения | ограничивает верхнюю категорию |

Точные числа — конфигурация `scorer_version`, а не разбросанные по UI константы.

### 7.3. Правила против data-desert bias

- missing `capacity` или `numberDoctors` не даёт отрицательных баллов само по себе;
- отсутствие supportive evidence уменьшает полноту и расширяет диапазон неопределённости;
- только явный противоречащий текст может быть отрицательным доказательством;
- `insufficient-data` — отдельная категория, а не низкий trust;
- UI не использует красный статус «нет capability», если данных недостаточно;
- ранжирование по умолчанию использует conservative lower bound, но пользователь видит и центральную оценку, и полноту.

### 7.4. Диапазон неопределённости

Без ground truth нельзя честно называть score калиброванной вероятностью или prediction interval. Для MVP применяем sensitivity interval:

- lower bound: только подтверждённые, валидированные сигналы;
- point estimate: все валидированные положительные и отрицательные сигналы;
- upper bound: сценарий, где missing supportive fields могли бы дать ограниченный положительный вклад;
- ширина диапазона растёт при низкой полноте и малом числе независимых полей.

В UI это называется «диапазон оценки при неполных данных», а метод подробно описывается в `docs/scoring.md`.

### 7.5. Ранжирование

Порядок сортировки:

1. текущий human override, если пользователь явно включил его в фильтр;
2. `conservative_score` по убыванию;
3. число независимых полей с evidence;
4. меньшее число противоречий;
5. стабильный `facility_id` как tie-breaker.

Это обеспечивает воспроизводимость списка между сессиями.

## 8. Validator и self-correction loop

Это первый stretch goal, потому что напрямую усиливает главный критерий Evidence & Trust.

Первая версия validator выполняет безопасные проверки внутренней согласованности:

- capability claim существует, но нет подтверждения ни в одном другом поле;
- advanced surgery claim без какого-либо staffing/anesthesia signal;
- NICU claim без neonatal/newborn signal вне самого claim;
- equipment/procedure противоречит facility type или narrative;
- exact quote не найдена в исходном тексте;
- один extractor pass не согласуется со вторым детерминированным pass;
- geography/PIN противоречат друг другу;
- source URL отсутствует или дублируется подозрительно часто.

Validator не удаляет исходные claims. Он создаёт отдельные сигналы и влияет на диапазон/категорию assessment. High-leverage review queue можно показать как небольшой бонусный экран после готовности основного workflow.

## 9. Search и serving

### 9.1. Обязательный путь

Facility Trust Desk в первую очередь использует структурные фильтры:

- capability;
- state/city/district/PIN;
- минимальная evidence category;
- наличие/отсутствие противоречий;
- статус human review.

SQL query возвращает заранее рассчитанные assessments и не запускает LLM.

### 9.2. AI Search

Один общий `search_chunks` Delta table содержит evidence sentences и metadata. Включить Change Data Feed, создать один standard Delta Sync index, запускать Triggered Sync после batch pipeline.

AI Search используется для:

- semantic recall синонимов capability;
- поиска похожих доказательств;
- будущего свободного запроса как stretch goal.

Если endpoint холодный или quota исчерпана, приложение автоматически переходит на SQL/taxonomy path и показывает неблокирующее уведомление.

## 10. UX

### 10.1. Основной экран

- крупный вопрос: «Какую возможность и где вы хотите проверить?»;
- два понятных фильтра capability/region;
- кнопка «Показать учреждения»;
- краткая легенда: `Strong evidence`, `Mixed evidence`, `Insufficient data`, `Contradictions`;
- ranked table/cards без технических терминов LLM/vector/embedding.

Каждая карточка показывает:

- название и регион;
- strength band и score range;
- data completeness отдельным индикатором;
- 2–3 главных trust signals;
- количество citations, gaps и contradictions;
- статус человеческой проверки.

### 10.2. Детали учреждения

При раскрытии:

- «Почему эта оценка» — component breakdown;
- точные цитаты с подсветкой capability terms;
- field name и source URL;
- «Что неизвестно»;
- «Что противоречит заявлению»;
- версии extraction/scoring;
- кнопка override.

### 10.3. Override

Форма содержит:

- решение: confirm / needs review / reject / custom category;
- обязательную заметку;
- предупреждение, что исходная машинная оценка не удаляется;
- успешное сохранение;
- историю решений.

### 10.4. Обязательные состояния интерфейса

- загрузка;
- пустой результат;
- недостаточно данных;
- частичный отказ AI Search;
- холодный старт Lakebase с retry;
- истёкшая/ошибочная сессия;
- источник без URL;
- read-only degraded mode без потери просмотра evidence.

## 11. Persistence и безопасность

- Lakebase connection выдаётся App как resource, credentials не коммитятся.
- Используется connection pool и retry первого запроса после scale-to-zero.
- Миграции идемпотентны.
- Notes проходят ограничение длины и parameterized SQL.
- В MLflow не логируются секреты, полные пользовательские notes и потенциальные персональные данные.
- Пользовательский override никогда не меняет raw dataset.
- Все изменения имеют audit trail.
- UI содержит дисклеймер: инструмент оценивает качество доступных данных и не заменяет клиническую верификацию учреждения.

## 12. Наблюдаемость

MLflow 3 spans:

```text
extract_batch
  row_candidate_recall
  model_extract
  citation_validate
  evidence_persist

planner_query
  normalize_filters
  sql_retrieve
  optional_ai_search
  score_load
  rank
  render_payload

save_override
  validate_input
  lakebase_write
  lakebase_readback
```

Теги: `dataset_version`, `extractor_version`, `scorer_version`, capability, region level, degraded-mode flag. Метрики: p50/p95 latency, error rate, 429 count, invalid-citation rate, cache hit rate, model call count/cost, Lakebase write success.

На serverless autologging включается явно. Для демо заранее проверить, что нужные traces видны и не содержат чувствительных данных.

## 13. План реализации на 48 часов

### Этап 0. H0–H3 — снять инфраструктурные риски

- получить доступ к Free Edition, Marketplace dataset, schema и starter materials;
- выполнить capability gate из раздела 3;
- создать минимальный Streamlit App с health check;
- развернуть его в Databricks Apps;
- создать пустую Lakebase schema и выполнить insert/read;
- записать первый MLflow trace;
- зафиксировать доступные model endpoints и ограничения региона.

**Выход:** live skeleton и таблица capability decisions. Не начинать сложный UI, пока deploy не доказан.

### Этап 1. H3–H7 — ingestion и профиль данных

- импортировать/скопировать dataset в контролируемый UC schema;
- определить стабильный `facility_id`;
- создать raw и normalized tables;
- построить data-quality profile;
- выбрать golden/demo rows;
- уточнить geography filters по фактической схеме.

**Выход:** воспроизводимый ingest и demo slice с сильными/слабыми/противоречивыми примерами.

### Этап 2. H7–H15 — Evidence Engine

- реализовать taxonomy и sentence offsets;
- создать structured-output schema;
- обработать demo slice через model и fallback extractor;
- валидировать exact quotes;
- сохранить evidence spans и quarantine;
- затем запустить batch на 10k в пределах quota;
- добавить caching/retry/concurrency guard.

**Выход:** для каждого demo result есть проверенная цитата до исходной строки.

### Этап 3. H15–H21 — Trust Scorer

- реализовать component scoring и versioned config;
- разделить evidence strength и completeness;
- реализовать contradiction rules и sensitivity range;
- построить assessment table;
- написать golden unit tests;
- проверить стабильное ранжирование.

**Выход:** scorer различает claim-only, corroborated, contradictory и insufficient-data случаи.

### Этап 4. H21–H29 — основной UI

- capability/region filters;
- ranked results;
- detail panel с citations, gaps, contradictions и score breakdown;
- понятные тексты неопределённости;
- loading/empty/error/degraded states;
- интеграция SQL fallback и optional AI Search.

**Выход:** полный read-only minimum flow работает в live App.

### Этап 5. H29–H33 — Lakebase workflow

- миграция `assessment_overrides`;
- save/read/history APIs;
- override form с обязательной note;
- audit и readback verification;
- тест между двумя сессиями/redeploy.

**Выход:** точный обязательный workflow PDF завершён end-to-end.

### Этап 6. H33–H37 — tracing и validator

- расставить MLflow spans;
- добавить validator rules;
- показать reasoning trail в UI;
- собрать latency/error/cost metrics;
- при наличии времени — high-leverage review queue.

**Выход:** закрыт Agentic Traceability/self-correction stretch без расширения mission track.

### Этап 7. H37–H43 — тесты и hardening

- unit, integration и E2E;
- performance smoke на 10k;
- quota/429/cold-start/degraded-mode tests;
- fresh deploy из чистой конфигурации;
- прогрев SQL warehouse, AI Search и Lakebase;
- исправление только блокирующих дефектов.

**Выход:** воспроизводимый deploy и доказательства готовности.

### Этап 8. H43–H46 — demo и submission

- подготовить минутный сценарий;
- выбрать три заранее проверенных facility cases;
- сделать простую архитектурную диаграмму;
- записать backup demo;
- оформить README и setup/deploy instructions;
- отправить git repo и live app минимум за час до deadline.

### Этап 9. H46–H48 — резерв

- только исправление deploy/demo blockers;
- проверить, что App был запущен менее 24 часов назад;
- повторить demo с чистой сессией;
- не добавлять новые крупные функции.

## 14. Тестовый план

### 14.1. Unit

- нормализация capability synonyms;
- geography normalization;
- exact quote offsets;
- JSON schema rejection;
- scorer component weights;
- contradiction penalties;
- missingness не создаёт negative evidence;
- score всегда в 0–100;
- lower bound <= point estimate <= upper bound;
- одинаковый вход и версии дают одинаковый rank;
- override note не может быть пустой.

### 14.2. Golden cases

Минимум четыре фиксированных случая на ключевые capability:

1. claim-only — высокая полнота claim, но слабая corroboration;
2. corroborated — description + equipment + procedure дают strong evidence;
3. contradiction — claim есть, но найден явный конфликт;
4. insufficient-data — мало полей, результат не маркируется как «нет capability».

Для каждого ожидаются band, допустимый score range, обязательные evidence IDs и explanation fragments.

### 14.3. Integration

- ingest -> normalize -> extract -> validate -> assess;
- Delta CDF -> Triggered Sync -> AI Search query;
- SQL fallback при недоступном AI Search;
- App query возвращает citations только из исходной строки;
- Lakebase insert -> read -> superseding override -> current view;
- MLflow trace содержит требуемые spans и version tags.

### 14.4. E2E

Автоматический или пошаговый браузерный сценарий:

1. открыть App;
2. выбрать ICU и регион;
3. дождаться списка;
4. открыть первое учреждение;
5. проверить exact quote и gap;
6. сохранить `needs review` с заметкой;
7. обновить страницу/создать новую сессию;
8. убедиться, что решение и история сохранились.

### 14.5. Нефункциональные цели

- первый полезный экран после прогрева: до 3 секунд;
- фильтрация/ranking без LLM в request path;
- отсутствие 500 при отказе AI Search;
- ни одна показанная цитата не нарушает substring invariant;
- повторный deploy не удаляет overrides;
- setup и migrations можно запустить повторно.

## 15. Приёмка по критериям жюри

| Критерий | Доказательство |
|---|---|
| Evidence and Trust, 35% | exact quotes/offsets/source row, component score, contradiction validator, completeness отдельно от trust, sensitivity interval |
| Product Judgment, 30% | один нечатовый workflow для NGO planner, понятные bands/gaps, override с заметкой |
| Technical Execution, 25% | live Databricks App, serverless SQL, Delta/UC, AI Search Delta Sync, Lakebase, MLflow 3, degraded path |
| Ambition, 10% | agentic traceability + self-correction/high-leverage queue после готовности MVP |

## 16. Риски и меры

| Риск | Вероятность/влияние | Мера |
|---|---|---|
| Нет доступа к dataset/schema | высокое/высокое | решить в H0; временно использовать golden fixtures, но submission требует реальный dataset |
| Функция недоступна в конкретном Free workspace | среднее/высокое | capability gate, feature flags, optional Genie/Agent Bricks |
| Fair-use/model quota | высокое/высокое | offline batch, cache, demo slice, retry, fallback extractor |
| App остановился через 24 часа | высокое/высокое | restart непосредственно перед demo, health check и runbook |
| AI Search недоступен/холодный | среднее/среднее | SQL/taxonomy fallback, заранее Triggered Sync |
| Lakebase cold start | среднее/среднее | pool/retry, прогрев, read-only degraded mode |
| LLM придумал citation | среднее/критичное | exact substring postvalidation, quarantine, rule-based fallback |
| Score воспринимают как clinical truth | среднее/критичное | правильное название, disclaimer, breakdown, human override |
| Missing data выглядит как absence | высокое/критичное | отдельная completeness, `insufficient-data`, sensitivity interval |
| Не успеваем за 48 часов | высокое/высокое | один track, deploy first, E2E always green, stretch только после stop condition |
| Live demo нестабилен | среднее/высокое | seeded cases, warm-up, backup video, no runtime batch |

## 17. Минутный demo flow

1. **0–10 сек:** «Заявление “есть ICU” ещё не означает подтверждённую возможность. Мы показываем доказательства и честно отделяем неизвестность от отсутствия».
2. **10–25 сек:** выбрать ICU и регион, показать ranked facilities и разные trust/completeness статусы.
3. **25–45 сек:** открыть strong или contradictory facility, показать точную цитату, source field, gaps и score breakdown.
4. **45–55 сек:** сохранить `needs review` с заметкой и обновить страницу, доказав persistence.
5. **55–60 сек:** показать MLflow trace/архитектурную схему: extraction -> validation -> scoring -> ranking, Lakebase audit.

## 18. Очерёдность stretch goals после MVP

1. **Self-correction/high-leverage review queue** — усиливает основной трек и главный критерий.
2. **Agentic traceability в UI** — exact sentence + reasoning step + MLflow trace link.
3. **Genie поверх 2–5 curated gold views** — только отдельная аналитическая демонстрация, не backend основного UI.
4. **Map preview** — только если в данных есть надёжные coordinates/PIN и основной flow полностью стабилен.
5. **Другие mission tracks** — не начинать в рамках 48 часов.

## 19. Внешние зависимости и ссылки

Материалы задания:

- PDF: `tracks/pdf/1784382653830-04-Databricks-Data-Legend.docx.pdf`
- английский текст: `tracks/md/04-Databricks-Data-Legend.md`
- русский перевод: `tracks/md-ru/04-Databricks-Data-Legend.md`
- India 10k Marketplace listing: <https://login.databricks.com/signin?intent=SIGN_IN&auto_login=true&destination_url=%2Fmarketplace%2Fconsumer%2Flistings%2F19326b3d-db63-4627-abc0-cf4e8131a305&utm_source=open-in-databricks&utm_medium=marketplace&utm_campaign=dais-devrel-hackathon>
- Virtue Foundation schema: <https://docs.google.com/document/d/1UDkH0WLmm3ppE3OpzSuZQC9_7w3HO1PupDLFVqzS_2g/edit?usp=sharing>
- starter prompts/Pydantic models: <https://drive.google.com/file/d/1CvMTA2DtwZxa9-sBsw57idCkIlnrN32r/view?usp=drive_link>

Официальная документация Databricks, которую следует повторно проверить перед реализацией:

- Free Edition limits: <https://docs.databricks.com/aws/en/getting-started/free-edition-limitations>
- Databricks Apps: <https://docs.databricks.com/aws/en/dev-tools/databricks-apps/>
- Apps key concepts/persistence: <https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts>
- Apps best practices: <https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices>
- Apps + Lakebase: <https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase>
- AI Search/Vector Search: <https://docs.databricks.com/aws/en/vector-search/create-vector-search>
- MLflow 3 tracing: <https://docs.databricks.com/aws/en/mlflow3/genai/tracing/>
- Foundation Model APIs: <https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis>
- Agent Bricks Supervisor: <https://docs.databricks.com/aws/en/agents/agent-bricks/multi-agent-supervisor>
- Genie setup: <https://docs.databricks.com/aws/en/genie-agents/set-up>

## 20. Финальный stop condition

Работа над MVP прекращается и переключается на submission только когда:

- живой Free Edition App выполняет точный Facility Trust Desk workflow;
- каждый ranking result имеет проверяемые citations и объяснение оценки;
- unknown/data desert не представлен как отсутствие capability;
- human override с заметкой переживает новую сессию/redeploy;
- targeted tests и deployment smoke pass;
- demo cases, backup video и минутный pitch готовы;
- не осталось незакрытых блокеров, способных сорвать live demo.

Все дополнительные функции после этого оцениваются по правилу: добавлять только если они заметно усиливают Evidence & Trust и не рискуют стабильностью основного сценария.
