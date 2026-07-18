# План реализации: ElevenLabs The Negotiator

## 1. Результат и границы MVP

### 1.1. Что строим

Строим end-to-end сервис для поиска и переговоров с перевозчиками при переезде:

1. **Agent 1 — Estimator** проводит голосовое интервью, эквивалентно эти данные можно получить из загруженного документа, формирует единую спецификацию переезда и просит пользователя подтвердить её.
2. В самом конце Agent 1 отдельно получает явное согласие на обзвон и допустимые часы контакта.
3. **Orchestrator/MCP Server** сохраняет заказ, получает ценовой ориентир, находит и проверяет перевозчиков, рассчитывает безопасное расписание по часовым поясам и создаёт задания на звонки.
4. **Agent 2 — Caller/Closer** получает неизменяемый snapshot заказа, ценовой диапазон и одного перевозчика, выясняет детализированную цену и честно торгуется.
5. После завершения всех заданий orchestrator нормализует и ранжирует результаты, а web UI показывает итоговую таблицу с ценами, изменением после переговоров, комиссиями, рисками, транскриптами и записями.

Это замыкает обязательный поток `intake -> calls -> negotiation -> ranked recommendation` из задания (`tracks/md/01-ElevenLabs-The-Negotiator.md:38-48`, `tracks/md/01-ElevenLabs-The-Negotiator.md:135-145`).

### 1.2. Почему нужны именно два режима звонка

ElevenLabs React SDK/widget создаёт браузерную сессию `browser <-> agent`, а настоящий outbound API звонит на номер Twilio/SIP. Поэтому «исходящий звонок в fake widget» нельзя выдавать за PSTN-звонок.

MVP поддерживает два адаптера с одним и тем же Agent 2:

- **Demo carrier console — обязательный путь:** отдельная страница имитирует входящий звонок, оператор нажимает `Answer`, после чего React SDK открывает защищённую голосовую сессию с Agent 2. Оператор играет перевозчика по одной из трёх скрытых карточек поведения.
- **Twilio/SIP outbound — feature-flag/stretch:** orchestrator вызывает официальный outbound endpoint ElevenLabs для реального или тестового телефонного номера.

Agent transfer не используется: он передаёт текущий разговор другому агенту, но не запускает независимый исходящий звонок. Новый звонок создаёт внешний orchestrator после подтверждения заказа и согласия пользователя.

Официальные ограничения: [Agent transfer](https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/agent-transfer), [React SDK](https://elevenlabs.io/docs/eleven-agents/libraries/react), [Twilio outbound](https://elevenlabs.io/docs/api-reference/twilio/outbound-call/), [SIP outbound](https://elevenlabs.io/docs/eleven-agents/api-reference/sip-trunk/outbound-call).

### 1.3. Что обязательно входит в MVP

- два настроенных ElevenLabs voice agents;
- один control-plane процесс: orchestrator, публичный MCP endpoint, REST API, ElevenLabs webhooks и scheduler/worker;
- voice interview со всеми полями переезда;
- загрузка минимум одного типа документа — machine-readable PDF инвентаря или существующей сметы — с приведением к той же схеме заказа;
- подтверждение пользователем полной спецификации до звонков;
- отдельное версионируемое согласие на обзвон;
- локальный demo dataset перевозчиков как детерминированный основной источник;
- Exa Search как опциональный discovery fallback;
- FMCSA-поля/fixture для проверки перевозчика;
- версионированный benchmark moveBuddha с provenance, без предположения о несуществующем публичном API;
- минимум три live demo-сессии с разными стилями контрагента;
- хотя бы одно измеримое улучшение цены или условий благодаря реальному рычагу;
- итоговый web dashboard и evidence-backed recommendation.

Голосовой и документный intake обязаны давать один и тот же подтверждённый JSON (`tracks/md/01-ElevenLabs-The-Negotiator.md:56-60`). Минимум три стиля переговоров и itemized quotes обязательны (`tracks/md/01-ElevenLabs-The-Negotiator.md:62-78`).

### 1.4. Что не входит в critical path

- звонки реальным компаниям без отдельной юридической и продуктовой проверки;
- автоматический booking или оплата перевозчика;
- массовый scraping moveBuddha;
- multi-tenant billing и полноценная production-аутентификация;
- мобильное приложение;
- полностью автономный голосовой counterparty agent — он превратил бы систему в три voice agents и усложнил доказательство живых переговоров;
- универсализация на другие verticals, кроме вынесения moving taxonomy и negotiation rules в конфигурацию.

## 2. Критерии готовности MVP

MVP готов, когда на чистом локальном запуске с публичным HTTPS tunnel/deployment для ElevenLabs callbacks пройден сценарий:

1. Пользователь запускает разговор с Agent 1 в web UI и сообщает:
   - адрес отправления и назначения;
   - временное окно/дату переезда;
   - минимальный и максимальный бюджет;
   - тип сервиса/транспорта;
   - нужны ли грузчики и сколько;
   - комнаты, крупные предметы, объём/инвентарь;
   - этажи, лестницы, лифты, long-carry/parking и другие access constraints.
2. Пользователь загружает поддерживаемый machine-readable inventory PDF; ожидаемые поля из golden fixture попадают в тот же `MoveSpec` с provenance, а конфликтующие значения Agent 1 уточняет голосом. Scanned/пустой/повреждённый PDF даёт явный `document_needs_manual_input`, а не выдуманные поля.
3. Agent 1 показывает/озвучивает финальную спецификацию; пользователь явно подтверждает её.
4. Система не создаёт ни одного `CallJob`, пока нет отдельного `OutreachConsent` с timestamp, scope и допустимым окном звонков.
5. Orchestrator находит минимум трёх перевозчиков, сохраняет источник и проверку, получает benchmark и создаёт для каждого индивидуальное расписание внутри часов работы перевозчика.
6. Demo carrier console проводит минимум три живых сессии с Agent 2: tough negotiator, hidden-fee lowballer, hard-sell/stonewaller.
7. Во всех звонках Agent 2 использует один и тот же immutable `MoveSpecVersion` и не раскрывает верхнюю границу бюджета без явно заданной стратегии.
8. Каждый звонок завершается ровно одним terminal outcome: `itemized_quote`, `callback_commitment`, `documented_decline`, `no_answer` или `technical_failure`.
9. Для каждого quote сохранены исходная и финальная цена, itemized fees, включённые/исключённые услуги, binding status, deposit/cancellation terms, validity и transcript evidence.
10. Минимум в одной сессии `final_total < initial_total` либо улучшены измеримые условия, а `leverage_source` ссылается на реальный benchmark или ранее сохранённый quote.
11. Quote на 30% или более ниже нижней границы benchmark помечается как red flag, а не автоматически побеждает.
12. После terminal state всех заданий web UI автоматически показывает ранжированную таблицу, рекомендацию, объяснение и ссылки на transcript/recording.
13. Перезапуск orchestrator не дублирует звонки и результаты; webhook replay не создаёт второй quote.
14. Unit, contract/integration, golden-call и Playwright E2E проверки проходят.

Стоп-условие реализации: все 14 критериев выполнены, demo flow воспроизводится без ручного редактирования БД, а реальные PSTN-звонки остаются выключены по умолчанию.

## 3. Архитектура

```text
User browser
  |
  +-- Agent 1 React voice session ----------------------+
  |                                                     |
  +-- document upload / order progress / final table    |
                                                        v
                                              ElevenLabs Agents
                                               | Agent 1 tools
                                               | Agent 2 tools
                                               v
Carrier console <--- SSE incoming job --- Control Plane / MCP Server
  | React SDK answers Agent 2              | Streamable HTTP /mcp
  +---------------------------------------->| REST /api
                                            | /webhooks/elevenlabs
                                            | scheduler + call dispatcher
                                            | ranking + recommendation
                                            v
                                      SQLite (MVP) + artifacts
                                            |
                    +-----------------------+-----------------------+
                    |                       |                       |
             local carrier dataset     Exa adapter           benchmark adapter
                    |                       |                       |
                  FMCSA fixture      public web results       moveBuddha fixture

Optional: Control Plane -> ElevenLabs Twilio/SIP outbound -> phone number
```

### 3.1. Технологический выбор

- **Monorepo:** TypeScript + pnpm workspaces; один язык для web, MCP, SDK contracts и тестов.
- **Web:** Next.js/React; `@elevenlabs/react` для Agent 1 и carrier console; SSE для статусов кампании.
- **Control plane:** Fastify + официальный TypeScript MCP SDK, Streamable HTTP endpoint `/mcp`, REST и webhook routes в одном процессе.
- **Схемы:** Zod; один пакет contracts используется MCP tools, REST, prompts и UI.
- **Хранилище:** SQLite + Drizzle для воспроизводимого hackathon MVP; repository interface оставляет миграцию на PostgreSQL без изменения доменных сервисов.
- **Очередь:** таблица `call_jobs` + lease/heartbeat worker, без Redis; `FOR UPDATE`-эквивалент/atomic update не допускает двойную обработку.
- **Артефакты:** локальная директория в dev, интерфейс object storage для production.
- **Публичный ingress:** HTTPS deployment либо Cloudflare Tunnel/ngrok для локального demo; ElevenLabs cloud не может вызвать `localhost` MCP/webhook routes.
- **Тесты:** Vitest, MCP/HTTP integration tests, Playwright и golden conversation evals.

Репозиторий сейчас содержит только briefs, wiki и один план; существующих app/runtime conventions нет. Поэтому этот стек создаётся с нуля, а не объявляется продолжением существующего приложения.

### 3.2. Предлагаемая структура репозитория

```text
package.json
pnpm-workspace.yaml
.env.example
apps/
  web/
    app/
      page.tsx
      intake/page.tsx
      moves/[moveId]/page.tsx
      carrier-console/page.tsx
    components/
      IntakeVoicePanel.tsx
      MoveSpecReview.tsx
      ConsentCard.tsx
      CampaignProgress.tsx
      QuoteComparisonTable.tsx
      TranscriptEvidence.tsx
  control-plane/
    src/
      server.ts
      config.ts
      mcp/server.ts
      mcp/tools/
      api/routes/
      webhooks/elevenlabs.ts
      orchestration/state-machine.ts
      orchestration/scheduler.ts
      orchestration/dispatcher.ts
      orchestration/reconciler.ts
      ranking/rank-quotes.ts
      persistence/
packages/
  contracts/
    src/move-spec.ts
    src/carrier.ts
    src/benchmark.ts
    src/call.ts
    src/quote.ts
  agent-config/
    estimator.prompt.md
    negotiator.prompt.md
    moving.config.ts
    analysis-fields.ts
  datasources/
    src/carriers/local-dataset.ts
    src/carriers/exa.ts
    src/carriers/fmcsa.ts
    src/benchmarks/movebuddha.ts
  document-intake/
    src/pdf-text.ts
    src/inventory-parser.ts
  timezones/
    src/address-resolver.ts
    src/timezone-resolver.ts
data/
  carriers.demo.json
  benchmarks.demo.json
  negotiation-personas.demo.json
drizzle/
tests/
  unit/
  integration/
  e2e/
  golden/
docs/
  architecture.md
  mcp-contracts.md
  agent-prompts.md
  demo.md
  privacy-and-consent.md
```

## 4. Доменные контракты и инварианты

### 4.1. `MoveSpec`

```ts
type MoveSpec = {
  moveId: string;
  origin: NormalizedAddress & { timezone: string };
  destination: NormalizedAddress & { timezone: string };
  moveWindow: { earliest: string; latest: string };
  budget: { min?: number; max?: number; currency: "USD" };
  serviceType: "labor_only" | "truck_and_movers" | "full_service";
  vehiclePreference?: "van" | "box_truck" | "unspecified";
  loaders: { required: boolean; count?: number };
  home: { bedrooms?: number; rooms?: number };
  inventory: Array<{ name: string; quantity: number; large: boolean }>;
  access: {
    originFloor?: number; destinationFloor?: number;
    originStairs?: boolean; destinationStairs?: boolean;
    originElevator?: boolean; destinationElevator?: boolean;
    longCarry?: boolean; parkingConstraints?: string;
  };
  notes?: string;
};
```

Инварианты:

- адреса нормализованы, но оригинальный пользовательский текст сохранён;
- `MoveSpecVersion` после подтверждения immutable и передаётся каждому звонку целиком;
- document intake и voice intake пишут в одну схему с `fieldProvenance`;
- конфликт документа и голоса нельзя молча разрешить — требуется подтверждение пользователя;
- budget не является разрешением на покупку и не должен автоматически раскрываться перевозчику.

### 4.2. Согласие и временные зоны

`OutreachConsent` хранит `move_id`, `spec_version`, `granted_at`, разрешённые каналы, максимальное число компаний, user call window и отозванность. Согласие нельзя выводить из общего подтверждения заказа.

Address/timezone pipeline имеет два режима:

- demo resolver сопоставляет поддерживаемые address fixtures с нормализованным адресом, координатами и IANA timezone и сохраняет `timezone_source=fixture`;
- production adapter геокодирует адрес, затем определяет IANA timezone по координатам и сохраняет provider, source id, confidence и timestamp. Неуверенный результат требует подтверждения пользователя.

Discovery ищет перевозчиков около origin и destination и оставляет только компании, чья service area совместима с маршрутом. User call window хранится с reference timezone (по умолчанию origin, явно показано пользователю). Move window интерпретируется отдельно в origin и destination timezone, чтобы не потерять дату при пересечении зон.

Для каждого перевозчика scheduler:

1. берёт IANA timezone офиса перевозчика из source provenance либо вычисляет её из подтверждённых координат;
2. парсит `opening_hours` источника;
3. пересекает business hours с user-approved window, переведённым из его reference timezone, и внутренним compliance window;
4. переводит интервал в UTC и сохраняет исходные local representations;
5. не dispatch-ит job при неизвестной timezone или часах без ручного demo override с audit note;
6. при отзыве согласия отменяет все `queued/scheduled` jobs.

Batch Calling имеет timezone и schedule на уровне batch, а не отдельного recipient. Поэтому разные local windows обслуживаются индивидуальными jobs либо отдельными batch groups. Для MVP используется индивидуальная очередь.

### 4.3. Перевозчики и источники

`Carrier` содержит source/source_id, company name, phone, address, timezone, opening hours, service area, rating/review count, website, USDOT и validation status.

Приоритет discovery:

1. `carriers.demo.json` — воспроизводимый набор с тремя стилями и полными полями;
2. FMCSA fixture/adapter — legal/status validation, но не источник цен (`wiki/elevenlabs-datasource.md:50-59`);
3. Exa `POST /search`, `category: "company"` — fallback при недостатке результатов;
4. будущий Places/OSM adapter — источники, рекомендованные wiki (`wiki/elevenlabs-datasource.md:23-48`).

Exa возвращает web pages, а не гарантированно проверенный справочник. Извлечённые phone/hours требуют source URL, validation status и дедупликацию; записи без надёжного контакта не ставятся в автоматический обзвон. Официальный контракт: [Exa Search API](https://exa.ai/docs/reference/search), [content retrieval](https://exa.ai/docs/reference/contents-retrieval).

### 4.4. Benchmark

`Benchmark` хранит source, route inputs, home size, service type, low/high/median, currency, collected_at, source URL и provenance.

У moveBuddha нет заявленного публичного bulk API (`wiki/elevenlabs-datasource.md:63-71`, `wiki/elevenlabs-datasource.md:173-186`). Поэтому MVP использует заранее сохранённые и датированные fixtures, подготовленные вручную через публичный calculator/methodology. Adapter возвращает `unavailable`, если нет подходящего диапазона; он не делает скрытый scraping.

### 4.5. Звонок и quote

```ts
type CallOutcome =
  | "itemized_quote"
  | "callback_commitment"
  | "documented_decline"
  | "no_answer"
  | "technical_failure";

type Quote = {
  callId: string;
  initialTotal?: number;
  finalTotal?: number;
  currency: "USD";
  fees: Array<{
    kind: "labor" | "truck" | "travel" | "fuel" | "stairs" |
          "long_carry" | "packing" | "valuation" | "tax" | "other";
    amount?: number;
    unit?: string;
    evidenceSpanId?: string;
  }>;
  includedServices: string[];
  excludedServices: string[];
  binding: "binding" | "non_binding" | "unknown";
  deposit?: number;
  cancellationTerms?: string;
  validUntil?: string;
  availabilityConfirmed: boolean;
  leverage: Array<{ type: "benchmark" | "verified_quote"; refId: string }>;
  redFlags: string[];
};
```

Golden-call dataset дополнительно сохраняет запись, транскрипт, initial/final terms, leverage, outcome и honesty/extraction scores (`wiki/elevenlabs-datasource.md:126-149`).

## 5. MCP API двух агентов

Один публичный Streamable HTTP MCP server регистрируется в ElevenLabs дважды: отдельное подключение для Agent 1 и отдельное для Agent 2. У регистраций разные scoped credentials и разные tool allowlists. MCP требует серверной валидации, auth и корреляции; secrets передаются в headers, а не в prompt. Интерактивное tool approval непригодно для автономного Agent 2, поэтому write tools получают fine-grained/no-approval только после строгой server-side авторизации.

На запуск каждой conversation control plane выпускает короткоживущий подписанный capability с `agent_role`, `session_id`, а для Agent 2 также с `move_id`, `spec_version`, `call_id`, `carrier_id` и `consent_id`. Capability передаётся только как secret header dynamic variable. MCP server выводит scope из проверенного credential/capability и не доверяет идентификаторам, которые LLM прислал в tool arguments. Agent 1 capability ограничен одной intake session/move; Agent 2 capability — одним call attempt. `tools/list` и вызовы вне role allowlist отклоняются на сервере.

Документация: [ElevenLabs MCP](https://elevenlabs.io/docs/eleven-agents/customization/tools/mcp/), [MCP security](https://elevenlabs.io/docs/eleven-agents/customization/tools/mcp/security), [dynamic variables](https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables).

### 5.1. Tools Agent 1

| Tool | Назначение | Основные проверки |
|---|---|---|
| `save_intake_draft` | upsert незавершённой спецификации | schema, ownership, optimistic version |
| `get_document_intake` | получить распознанные поля и конфликты | document принадлежит move/session |
| `finalize_move_spec` | создать immutable version после голосового подтверждения | completeness + explicit confirmation phrase |
| `grant_outreach_consent` | отдельно сохранить разрешение и ограничения обзвона | final spec exists, max carriers, window, timestamp |
| `get_campaign_status` | озвучить пользователю следующий этап | read-only scoped result |

`grant_outreach_consent` возвращает событие, после которого orchestrator, а не LLM, запускает discovery и scheduling.

### 5.2. Tools Agent 2

| Tool | Назначение | Основные проверки |
|---|---|---|
| `get_call_context` | получить approved snapshot, carrier и benchmark | call lease + immutable spec version |
| `record_call_started` | связать ElevenLabs conversation с job | idempotency by conversation id |
| `save_quote_progress` | сохранить initial quote/fees в ходе разговора | amounts, currency, evidence turn ids |
| `save_negotiation_result` | записать terminal structured outcome | enum, required fields per outcome, real leverage refs |
| `mark_call_failure` | busy/no-answer/technical failure | controlled reason enum, retry policy |

Agent 2 не может через MCP изменять заказ, согласие, benchmark или чужой call result: эти ограничения обеспечиваются role allowlist и signed call capability, а не только prompt-инструкцией.

### 5.3. Internal orchestrator services

Discovery, benchmark lookup, job creation, dispatch, webhook reconciliation и ranking являются серверными командами, а не свободными LLM tools. Это сокращает prompt injection surface и не позволяет агенту самовольно расширить scope обзвона.

## 6. State machine и жизненный цикл

### 6.1. Move campaign

```text
draft
  -> awaiting_confirmation
  -> confirmed
  -> awaiting_consent
  -> discovering
  -> scheduled
  -> calling
  -> aggregating
  -> completed

terminal side states: cancelled | blocked
```

Переходы `confirmed -> discovering` запрещены без active consent. `completed` возможен только когда все jobs terminal и reconciliation закончен.

### 6.2. Call job

```text
queued -> scheduled -> offered_to_widget -> in_progress -> processing -> completed
                     \-> expired/no_answer
              any recoverable -> retry_wait -> scheduled
              any terminal -> declined | failed | cancelled
```

Ключи идемпотентности:

- dispatch: `call_job_id + attempt_no`;
- ElevenLabs conversation: unique `conversation_id`;
- webhook: `event_type + conversation_id`;
- quote terminal write: one active terminal result per call attempt.

## 7. Дизайн разговоров

### 7.1. Agent 1 — Estimator

Prompt реализует не анкету по порядку, а coverage checklist:

1. кратко объяснить цель и что данные будут использованы для сравнения предложений;
2. собрать route и даты;
3. собрать home/inventory/access constraints;
4. собрать service/vehicle/loaders;
5. спросить budget как ориентир, не обещая раскрывать максимум перевозчику;
6. проверить document-derived поля и проговорить конфликты;
7. озвучить компактное summary и получить явное подтверждение;
8. отдельной репликой спросить разрешение на обзвон, количество компаний и допустимое окно;
9. объяснить, что время будет рассчитано по часам работы и timezone перевозчика;
10. сообщить следующий шаг, но не обещать цену до фактических звонков.

Если обязательное поле не получено, `finalize_move_spec` отклоняет запрос с machine-readable missing fields, и Agent 1 задаёт уточнение.

### 7.2. Agent 2 — Caller/Closer

Agent 2 получает через runtime dynamic variables только identifiers и безопасный стартовый контекст; authoritative details читает через `get_call_context`. Полный prompt не override-ится на каждый звонок.

Разговор:

1. представиться AI-ассистентом, звонящим от имени клиента, и назвать цель;
2. проверить, обслуживает ли компания маршрут и дату;
3. дословно описать подтверждённый scope;
4. получить initial total и добиться itemization;
5. спросить hourly/minimum/travel/fuel/stairs/long-carry/packing/valuation/tax/other fees;
6. уточнить availability, binding/non-binding status, deposit, cancellation и validity;
7. применить только разрешённые negotiation levers;
8. повторить финальные цифры и получить устное подтверждение;
9. сохранить terminal result до завершения разговора.

Honesty policy из задания (`tracks/md/01-ElevenLabs-The-Negotiator.md:82-91`):

- нельзя придумывать inventory, обстоятельства, urgency или competing bid;
- benchmark называется рыночным ориентиром, а не якобы полученным binding quote;
- competing bid можно назвать только при существующем `verified_quote` reference;
- Agent 2 не принимает юридически обязывающую сделку и не вносит депозит;
- при отказе, callback или hang-up сохраняется структурированный outcome;
- barge-in, evasive answers и «вы робот?» покрываются отдельными prompt examples/evals.

### 7.3. Порядок звонков и честный leverage

Для demo jobs выполняются последовательно (`concurrency = 1`). Первый перевозчик торгуется от benchmark и fee-removal levers; следующие могут использовать уже сохранённый реальный лучший quote. Это позволяет честно показать изменение цены без выдуманного предложения.

Parallel/batch режим остаётся конфигурацией для price gathering, но для использования competing bids потребуется отдельная callback negotiation phase. В MVP он не включён, чтобы не разрушить причинность leverage.

## 8. Fake carrier console

Carrier console не является третьим агентом. Это React-страница для человека, играющего перевозчика:

- получает по SSE событие `incoming_call` с carrier/persona id;
- показывает «ringing», `Answer` и `Decline`;
- после `Answer` атомарно переводит attempt `offered_to_widget -> claimed`, получает signed URL/token и вызывает `startSession` Agent 2;
- получает только те dynamic variables, которые нужны Agent 2;
- показывает оператору приватную persona card: initial price, hidden fees, допустимый floor, objections и условие уступки;
- не подсказывает Agent 2 и не передаёт ему floor;
- поддерживает три distinct styles и свободную живую речь, а не заранее записанный диалог;
- после разговора отображает conversation id и состояние post-call processing.

ElevenLabs API key никогда не попадает в browser. Signed URL выдаётся server-side, действует ограниченное время и создаётся отдельно на сессию, но сам по себе не гарантирует одноразовое использование. Поэтому backend также создаёт одноразовый nonce, хранит его hash на attempt, разрешает ровно один CAS claim/start и отклоняет повторную выдачу или повторный `conversation_id`: [authentication](https://elevenlabs.io/docs/eleven-agents/customization/authentication).

## 9. Web UI

### 9.1. Пользовательский flow

1. Landing: короткое объяснение и `Start interview`.
2. Intake: voice panel Agent 1, live status обязательных полей, document upload.
3. Review: read-only confirmed spec, provenance полей и отдельная consent card.
4. Campaign: найденные компании, источник, timezone, planned local/UTC time, call state.
5. Results: summary table и recommendation detail.

### 9.2. Итоговая таблица

| Поле | Почему нужно |
|---|---|
| Carrier + verification | идентичность, источник, USDOT/status |
| Outcome | quote/callback/decline/failure |
| Initial -> final total | измеримый результат переговоров |
| Negotiated delta | абсолютная и процентная экономия |
| Itemized fees | сопоставимость предложений |
| Included/excluded | защита от ложного сравнения |
| Binding/deposit/validity | качество и риск quote |
| Benchmark position | market sanity check |
| Red flags | lowball, hidden fee, non-binding, missing fields |
| Transcript evidence | ссылка на точные turns для цифр/условий |
| Recording | воспроизводимость demo |

Ranking rule детерминирован:

1. declines/callbacks/failures не участвуют в ценовом ranking, но остаются в таблице;
2. критически неполный или неподтверждённый quote получает `manual_review`;
3. цена на 30%+ ниже benchmark low помечается `suspicious_lowball`;
4. recommendation выбирается среди validated carriers с сопоставимым scope, полным fee breakdown и без critical flags;
5. среди них сортировка идёт по final total, затем binding quality, cancellation/deposit risk и completeness;
6. plain-language rationale строится из сохранённых полей и evidence refs, а не из неподтверждённой генерации.

## 10. ElevenLabs integration и reconciliation

### 10.1. Конфигурация агентов

- Agent 1 и Agent 2 — private/authenticated agents;
- MCP подключён к обоим одним server URL, но двумя registrations с отдельными role credentials/tool allowlists и per-session signed capabilities;
- runtime personalization — dynamic variables, а не полный prompt override;
- обязательные ids: `move_id`, `spec_version`, `call_id`, `carrier_id`, `consent_id`;
- budget maximum не передаётся в first message и не логируется без необходимости;
- Agent 2 analysis fields: outcome, initial/final totals, fee completeness, availability, binding, callback, negotiation delta;
- success evaluations: complete quote, consent/scope respected, honest leverage, measurable improvement.

### 10.2. Webhooks и источник истины

Agent 2 сохраняет результат через MCP во время разговора. `post_call_transcription` затем становится authoritative audit/reconciliation artifact, но не единственным способом закрыть job.

Webhook handler:

1. читает raw body и проверяет `ElevenLabs-Signature`;
2. отвечает `2xx` после durable/idempotent enqueue;
3. сохраняет transcript, metadata, analysis и initiation data;
4. сопоставляет их с `conversation_id/call_id`;
5. дополняет evidence spans, не перезаписывая подтверждённые MCP-поля без conflict record;
6. post-call audio сохраняет отдельно;
7. failure event переводит attempt в структурированный failure/retry state.

Включить webhook retries. Из-за ограниченной retry queue и возможности auto-disable добавить reconciliation poller по conversation API и health alert. Официальные контракты: [post-call webhooks](https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks), [conversation details](https://elevenlabs.io/docs/api-reference/conversations/get/), [conversation audio](https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-audio).

## 11. Этапы реализации

### Этап 0. Capability spikes и фиксация demo-контракта

1. Поднять публичный HTTPS deployment либо tunnel к control plane; проверить внешний health endpoint.
2. Создать два private ElevenLabs agents и две MCP registrations с разными role credentials/tool allowlists.
3. Зарегистрировать публичные MCP и webhook URLs в ElevenLabs.
4. Проверить один Agent 2 conversation через carrier console, secret session capability и передачу dynamic variables.
5. Получить реальный cloud-to-local/cloud webhook, проверить raw-body signature validation и MCP tool call.
6. Зафиксировать demo mode как browser session, а не PSTN outbound.
7. Подготовить `.env.example` без секретов и документировать обновление tunnel URL.

Выход: записанные agent ids/config steps, публичные HTTPS URLs, один conversation id, один проверенный облачный MCP call, один валидный webhook и подтверждённая интеграционная схема.

### Этап 1. Contracts, DB и state machines

1. Поднять workspace, packages и control-plane skeleton.
2. Реализовать Zod schemas для MoveSpec, consent, carrier, benchmark, call и quote.
3. Создать migrations для:
   - `moves`, `move_spec_versions`, `field_provenance`;
   - `outreach_consents`;
   - `carriers`, `carrier_sources`;
   - `benchmarks`;
   - `campaigns`, `call_jobs`, `call_attempts`;
   - `quotes`, `quote_fees`, `negotiation_events`;
   - `conversation_artifacts`, `webhook_events`, `audit_events`.
4. Реализовать campaign/call transition guards и idempotency constraints.

Выход: migrations применяются с нуля; invalid transitions и duplicate events отклоняются тестами.

### Этап 2. MCP server и Agent 1

1. Поднять `/mcp` с двумя role credentials, per-session signed capabilities, role-aware `tools/list`, request correlation и structured logs.
2. Реализовать Agent 1 tools и contract tests.
3. Создать Estimator prompt/coverage checklist.
4. Реализовать upload `application/pdf` с size/page limits, извлечение текста через `pdfjs-dist`, детерминированный parser inventory/rooms/large items/stairs/access, field provenance и состояния `unsupported_scan`, `empty`, `parse_failed`, `needs_manual_input`.
5. Реализовать review/confirm/consent UI.
6. Подключить Agent 1 через React SDK с backend-issued token.

Выход: golden machine-readable inventory PDF даёт ожидаемый partial `MoveSpec`; voice merge создаёт один confirmed version; конфликт требует подтверждения; scanned/invalid fixture безопасно уходит в manual input; без отдельного consent campaign не стартует.

### Этап 3. Discovery, benchmark и timezone scheduler

1. Создать demo carrier dataset с телефонами/часами/timezones/USDOT-like fields и тремя persona ids.
2. Реализовать adapter interfaces, local provider и FMCSA validation fixture.
3. Реализовать Exa provider с `category: company`, provenance, dedupe, timeout/rate-limit и local fallback.
4. Реализовать moveBuddha fixture adapter с matching и `unavailable` state.
5. Реализовать demo address resolver для golden route и production adapter interface `address -> coordinates -> IANA timezone` с provenance/confidence.
6. Искать/фильтровать carriers по origin, destination и service area; реализовать timezone/opening-hours/user-window intersection и per-carrier scheduling.
7. После consent создавать campaign и jobs идемпотентно.

Выход: один confirmed move детерминированно создаёт 3 scheduled jobs с объяснимым UTC/local временем и benchmark.

### Этап 4. Agent 2 и carrier console

1. Реализовать Agent 2 MCP tools.
2. Создать Negotiator prompt, honesty rules и negotiation config.
3. Реализовать dispatcher demo adapter: SSE ring -> Answer -> signed Agent 2 session.
4. Создать три operator persona cards с floor/objections/hidden fees.
5. Сохранять quote progress и terminal result во время разговора.
6. Добавить feature-flagged Twilio/SIP adapter, только если demo path уже стабилен.

Выход: три живые сессии дают три structured outcomes; минимум одна цена/условие меняется благодаря benchmark/verified quote.

### Этап 5. Webhooks, evidence и ranking

1. Реализовать signature validation, durable event record и idempotent processing.
2. Сохранять transcript/audio metadata и evidence spans.
3. Добавить conversation reconciliation poller.
4. Реализовать fee normalization, red flags и deterministic ranking.
5. Генерировать recommendation rationale только из сохранённых фактов.

Выход: webhook replay безопасен; таблица ссылается на конкретные transcript turns и показывает initial -> final delta.

### Этап 6. UI, evals и demo hardening

1. Завершить campaign progress и final comparison screens.
2. Добавить Golden calls/evals для трёх стилей.
3. Пройти полный E2E с рестартом control plane и webhook replay.
4. Подготовить demo seed/reset command, минутный сценарий и резервную запись.
5. Провести privacy/consent review; оставить PSTN feature flag выключенным.

Выход: judge-facing сценарий запускается одной командой и удовлетворяет всем критериям раздела 2.

## 12. План тестирования

### 12.1. Unit

- MoveSpec completeness и document/voice conflict resolution;
- machine-readable PDF golden extraction, field provenance и scanned/empty/corrupt error states;
- immutable spec version;
- consent transition guards и revocation;
- demo address resolution, IANA timezone provenance и low-confidence confirmation;
- origin/destination/carrier timezone/opening-hours conversion, включая DST и overnight hours;
- carrier dedupe и validation states;
- benchmark matching/unavailable;
- fee normalization;
- 30%-below-market red flag boundary;
- ranking/recommendation determinism;
- real leverage reference validation;
- state machine invalid transitions.

### 12.2. MCP/API contract

- role credentials возвращают разные `tools/list`, и оба агента видят только разрешённые tools;
- expired/wrong-role/wrong-call signed capability отклоняется, а scope ids берутся не из LLM arguments;
- invalid schema/auth/correlation отклоняются;
- Agent 2 не изменяет MoveSpec/consent/benchmark;
- repeated tool calls идемпотентны;
- terminal outcomes требуют разные обязательные поля;
- signed session URL не содержит API key и истекает; CAS/nonce не допускает второй claim/start;
- Exa timeout/rate-limit возвращает local fallback.

### 12.3. Integration

- confirm without consent -> zero jobs;
- consent -> discovery -> benchmark -> 3 scheduled jobs;
- unknown timezone/opening hours -> blocked/manual override, не автозвонок;
- SSE Answer создаёт ровно одну conversation attempt;
- MCP mid-call write + post-call webhook reconcile в один quote;
- duplicate/out-of-order webhook безопасен;
- failed webhook восстанавливается poller;
- restart продолжает leased jobs без дублей.

### 12.4. Golden conversation evals

Для каждой persona проверять:

- AI disclosure и представление интересов клиента;
- полное и одинаковое описание MoveSpec;
- извлечение каждого fee;
- обработку interruption/evasion/robot question;
- отсутствие fabricated bid/inventory;
- корректное различение benchmark и verified competitor quote;
- terminal outcome;
- измеримый negotiated delta там, где persona допускает уступку.

### 12.5. E2E

Playwright + mockable ElevenLabs adapter:

1. voice/text fixture + document upload;
2. review и confirmation;
3. отдельный consent;
4. три scheduled carrier sessions;
5. quote/callback/decline либо три quotes для основного demo fixture;
6. все jobs terminal;
7. final table, recommendation, transcript evidence;
8. page reload сохраняет результат.

Live smoke отдельно проходит с настоящими Agent 1/Agent 2 React sessions и одним signed webhook flow.

### 12.6. Нефункциональные проверки

- p95 MCP tool response без внешнего discovery < 500 ms локально;
- scheduler не создаёт dispatch вне рассчитанного local window;
- API keys отсутствуют в browser bundle/log snapshots;
- every write имеет move/call correlation и actor;
- restart recovery < 30 s;
- UI показывает `processing`, а не преждевременное `completed`, пока webhook/reconciliation не завершены.

## 13. Риски и снижения

| Риск | Последствие | Снижение |
|---|---|---|
| Widget ошибочно называется outbound telephony | недостоверная demo-архитектура | явно маркировать demo carrier console; PSTN только через отдельный Twilio/SIP adapter |
| Нет публичного moveBuddha API | блокировка или нарушение ToS | датированные fixtures + provenance; no scraping; `unavailable` state |
| Exa возвращает непроверенные phone/hours | звонок не тому контрагенту/не вовремя | validation status, source URL, dedupe, local dataset fallback |
| Пропущенное согласие | privacy/compliance риск | отдельная сущность и hard transition guard до job creation |
| Ошибка timezone/DST | звонок вне рабочих часов | IANA zones, tested interval intersection, no-call on unknown data |
| LLM выдумывает leverage | потеря доверия и нарушение задания | tool-provided refs, server validation, prompt rules, golden eval |
| Webhook потерян/повторён | stuck/duplicate quote | HMAC, retries, idempotency, reconciliation poller |
| Параллельные звонки лишают Agent 2 реальных bids | нечестный negotiation claim | sequential MVP; two-phase callbacks только после MVP |
| Оператор следует сценарию слишком буквально | demo выглядит canned | persona задаёт policy/floor, но не реплики; свободный live dialogue |
| Неполный intake даёт несопоставимые quotes | плохая рекомендация | schema completeness gate, document merge, exact spec snapshot |
| Recordings/transcripts содержат PII | утечка данных | consent notice, access control, retention config, redacted logs |
| Реальный звонок создаёт юридические обязательства | нежелательная сделка | Agent 2 не принимает сделку/депозит; PSTN off by default |

## 14. Demo-сценарий

1. Пользователь голосом описывает переезд и загружает небольшой inventory PDF/image.
2. Agent 1 находит недостающее поле, уточняет его и озвучивает итоговый MoveSpec.
3. Пользователь подтверждает spec, затем отдельно разрешает обзвон трёх компаний.
4. UI показывает discovery, moveBuddha range и рассчитанные local call windows.
5. В carrier console оператор по очереди принимает три «звонка» с разными persona cards.
6. Agent 2 у первого перевозчика выявляет hidden fee; у второго получает clean quote; у третьего использует реальный сохранённый quote и добивается снижения цены/улучшения условий.
7. Dashboard показывает все outcomes, initial/final totals, fees, red flags и evidence.
8. Открывается transcript turn, подтверждающий исходную цену, рычаг и финальную уступку.
9. Демонстрируется, что suspicious 30%-below-market lowball не становится рекомендацией.

## 15. Переменные окружения

```text
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_ESTIMATOR_ID=
ELEVENLABS_AGENT_NEGOTIATOR_ID=
ELEVENLABS_MCP_ESTIMATOR_TOKEN=
ELEVENLABS_MCP_NEGOTIATOR_TOKEN=
SESSION_CAPABILITY_SIGNING_KEY=
ELEVENLABS_WEBHOOK_SECRET=
ELEVENLABS_PHONE_NUMBER_ID=
EXA_API_KEY=
DATABASE_URL=file:./data/negotiator.db
ARTIFACTS_DIR=./data/artifacts
PUBLIC_WEB_URL=http://localhost:3000
CONTROL_PLANE_URL=http://localhost:3001
PUBLIC_CONTROL_PLANE_URL=https://negotiator-demo.example-tunnel.dev
ELEVENLABS_MCP_URL=https://negotiator-demo.example-tunnel.dev/mcp
ELEVENLABS_WEBHOOK_URL=https://negotiator-demo.example-tunnel.dev/webhooks/elevenlabs
CALL_TRANSPORT=widget
ENABLE_REAL_OUTBOUND=false
```

`ELEVENLABS_API_KEY`, MCP role tokens, capability signing key и webhook secret остаются только на server side. `PUBLIC_CONTROL_PLANE_URL` обязан быть HTTPS и доступен из ElevenLabs cloud; `localhost` используется только браузером и локальными тестами.

## 16. Источники и трассировка требований

### Локальные

- Общий challenge и три обязательных модуля: `tracks/md/01-ElevenLabs-The-Negotiator.md:38-78`.
- Conversation/honesty requirements: `tracks/md/01-ElevenLabs-The-Negotiator.md:82-91`.
- ElevenLabs/MCP/telephony и data-source hints: `tracks/md/01-ElevenLabs-The-Negotiator.md:95-120`.
- Полные success criteria: `tracks/md/01-ElevenLabs-The-Negotiator.md:135-145`.
- Discovery providers и ограничения: `wiki/elevenlabs-datasource.md:21-71`.
- Golden calls: `wiki/elevenlabs-datasource.md:126-149`.
- Рекомендуемый moving MVP stack: `wiki/elevenlabs-datasource.md:151-171`.
- Матрица доступности: `wiki/elevenlabs-datasource.md:173-186`.
- Исходный PDF: `tracks/pdf/1784382172163-01-ElevenLabs-The-Negotiator.docx.pdf`, страницы 3–6.

### Официальная документация

- [ElevenLabs MCP](https://elevenlabs.io/docs/eleven-agents/customization/tools/mcp/)
- [ElevenLabs MCP security](https://elevenlabs.io/docs/eleven-agents/customization/tools/mcp/security)
- [Dynamic variables](https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables)
- [React SDK](https://elevenlabs.io/docs/eleven-agents/libraries/react)
- [Widget](https://elevenlabs.io/docs/eleven-agents/customization/widget)
- [Authentication / signed URLs](https://elevenlabs.io/docs/eleven-agents/customization/authentication)
- [Twilio outbound call](https://elevenlabs.io/docs/api-reference/twilio/outbound-call/)
- [SIP outbound call](https://elevenlabs.io/docs/eleven-agents/api-reference/sip-trunk/outbound-call)
- [Batch calling](https://elevenlabs.io/docs/eleven-agents/phone-numbers/batch-calls)
- [Post-call webhooks](https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks)
- [Conversation API](https://elevenlabs.io/docs/api-reference/conversations/get/)
- [Exa Search API](https://exa.ai/docs/reference/search)

## 17. Порядок приоритетов при нехватке времени

1. Не сокращать: confirmation, отдельное consent, три distinct live calls, structured outcomes, honesty, price/term delta, transcript evidence и final table.
2. Сократить первым: реальный Twilio/SIP adapter, live Exa, автоматический document OCR — оставить интерфейс + deterministic fixture/parser.
3. Затем сократить: аудиоархив в object storage — оставить conversation/audio reference.
4. Не подменять: живые переговоры canned dialogue, реальные quotes генерацией, moveBuddha несуществующим API или browser widget настоящим outbound-звонком.
