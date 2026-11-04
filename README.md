# Empório da Música Agent

Conversational assistant for Empório da Música, a musical instruments store.
The project combines a tool-using agent, semantic retrieval over the store
policy manual, and structured queries for products, promotions, and orders.

## English

### Features

- Streamlit chat frontend.
- FastAPI HTTP API.
- Streaming responses with Server-Sent Events (SSE).
- LangGraph agent with explicit model/tool routing.
- Gemini as the primary LLM provider.
- Ollama with `qwen2.5:1.5b` as a local fallback.
- PostgreSQL and pgvector for relational data and embeddings.
- Docker Compose orchestration.
- Unit tests for provider selection, response normalization, and RAG behavior.

### Conversation examples

The repository includes four screenshots from the running Streamlit frontend in
[`examples/conversations/`](./examples/conversations/):

1. [Product catalog query](./examples/conversations/01-catalogo-violao.png):
   searches available violões up to a price limit and presents product prices.
2. [Store address policy](./examples/conversations/02-politica-endereco.png):
   answers a policy/location question using the store information.
3. [Out-of-scope request](./examples/conversations/03-escopo-clima.png):
   politely refuses a weather question and redirects the user to the store
   scope.
4. [Instrument categories](./examples/conversations/04-categorias-piano.png):
   explains piano categories in a conversational response.

The address example demonstrates a non-trivial policy lookup, while the
catalog example demonstrates a real-time structured database query.

### Architecture

```text
Streamlit (8501)
        |
        v
FastAPI (8000) ----> LangGraph Agent ----> Gemini
        |                    |              |
        |                    +------------> Ollama fallback
        |
        +----> PostgreSQL + pgvector
                    |             |
                    |             +--> relational tables
                    +----------------> policy embeddings
```

### Main components

- `src/ui/app.py`: Streamlit chat interface.
- `src/api/main.py`: FastAPI application and lifecycle.
- `src/api/routes/chat.py`: `POST /chat`.
- `src/agent/graph.py`: LangGraph workflow.
- `src/agent/tools/sql_tools.py`: product and order tools.
- `src/agent/tools/rag_tools.py`: policy-manual retrieval tool.
- `src/database/vector_store.py`: PGVector configuration.
- `src/database/seed.py`: CSV loading and PDF indexing.
- `docker-compose.yml`: PostgreSQL, API, UI, and Ollama services.

### Requirements

- Docker Engine and Docker Compose.
- Git.
- Optionally Python 3.12+ and `uv` for local development.
- A Google AI Studio API key for Gemini.

Docker is the recommended setup because it provides Python dependencies,
PostgreSQL, pgvector, and Ollama as reproducible services.

### Environment configuration

Create `.env` in the project root:

```dotenv
GOOGLE_API_KEY=your_google_ai_studio_key
```

`GOOGLE_API_KEY` is optional. When it is empty, the API selects Ollama. Docker
Compose supplies the development defaults:

```text
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=emporio_db
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:1.5b
API_URL=http://api:8000
```

Use secrets instead of default credentials in production, and never commit
`.env`.

### Running with Docker

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

The first startup downloads the Ollama model and may take several minutes.
Available URLs:

- Frontend: <http://localhost:8501>
- API: <http://localhost:8000>
- Swagger/OpenAPI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/health>

Load relational data and index the policy manual:

```bash
docker compose exec api python -m src.database.seed
```

The seed creates tables, loads CSV files from `data/`, extracts the policy
PDF, splits it into chunks, generates embeddings, and stores them in the
`politicas_loja_docs` pgvector collection.

The `POST /chat` endpoint returns an SSE stream instead of waiting for a
complete response. It emits JSON events with `type` values `token`, `done`, or
`error`, allowing the Streamlit frontend to render the answer progressively.

Useful commands:

```bash
docker compose down
docker compose down -v
docker compose exec ollama ollama list
docker compose exec postgres psql -U postgres -d emporio_db
```

### Local development

```bash
uv sync --dev
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
uv run streamlit run src/ui/app.py --server.port 8501
```

PostgreSQL/pgvector and Ollama must still be available. Set `API_URL` to
`http://localhost:8000` when the browser accesses a locally running API.

### Tests

Inside the API container:

```bash
docker compose exec api sh -lc \
  "PYTHONPATH=/app pytest -q tests"
```

With the local environment:

```bash
uv run --dev pytest -q tests
```

The tests cover Gemini/Ollama selection, LangChain content normalization,
policy retrieval formatting, and empty retrieval results.

Streaming is verified with a live `POST /chat` request that returns multiple
`token` events followed by a `done` event.

### Technical decisions

#### FastAPI: asynchronous API and built-in Swagger

FastAPI was chosen because it supports asynchronous request handling, which is
important for an API that coordinates model calls, database access, and
retrieval operations. Its Pydantic integration provides typed request/response
validation, while its automatic OpenAPI generation provides Swagger UI at
`/docs` and ReDoc at `/redoc` without requiring separate documentation work.
This makes the API easier to test, integrate, and evolve for future clients
such as WhatsApp, mobile applications, or a different web frontend.

#### PostgreSQL and pgvector

PostgreSQL combines transactional reliability, concurrency, indexing, backups,
replication, and operational maturity for production. It also lets the
project keep structured catalog/order data and vector embeddings in one
ecosystem. pgvector enables semantic search without introducing a separate
vector database at this scale. At larger scale, PostgreSQL can be replicated,
partitioned, pooled, or complemented by a dedicated search engine.

#### LangGraph

LangGraph was chosen for robustness and reliability through an explicit state
graph. The workflow separates model execution, tool selection, tool execution,
and the final response. This makes state transitions, cycles, checkpoints, and
business rules easier to inspect and test than a single opaque model call.

#### Gemini and local fallback

Gemini is the primary provider because it offers strong Portuguese
conversation quality and tool-calling support. Ollama with `qwen2.5:1.5b`
provides a local fallback when the Google key is absent, Gemini initialization
fails, or Gemini fails during inference, such as a `429 RESOURCE_EXHAUSTED`
quota response. The fallback reduces dependence on external availability,
quota, and network access, although its quality may be lower than Gemini.

#### Prompt strategy

The system prompt defines the store identity, scope, tone, business rules,
tool-use requirements, and a strict prohibition against inventing prices,
stock, policies, delivery times, or order status. The prompt guides behavior;
it is not treated as a source of commercial facts. Facts must come from SQL or
the policy retrieval tool.

#### Streaming responses

The API uses FastAPI `StreamingResponse` with Server-Sent Events. LangGraph's
`astream(..., stream_mode="messages")` exposes model message chunks, which are
sent as `token` events. Tool execution remains inside the graph, and the
frontend receives only text generated by the agent node. A final `done` event
marks completion, while an `error` event communicates failures without
silently returning a successful-looking response.

#### Retrieval/RAG strategy

The policy PDF is loaded, split with overlapping chunks, embedded with
`sentence-transformers/all-MiniLM-L6-v2`, and stored in pgvector. Policy
questions call `consultar_politicas_loja`, which retrieves the four most
similar chunks. Structured catalog and order questions use SQLAlchemy instead
of RAG, improving precision and auditability for prices, inventory, and status.

### Known limitations and future work

- Conversation state uses in-memory `MemorySaver`; it is not shared across
  replicas or persisted after process termination.
- The seed must be run to load the real CSV/PDF data.
- RAG quality depends on PDF extraction, chunking, and embedding quality.
- The local fallback is smaller and may be weaker at Portuguese and tool
  calling.
- No authentication, authorization, rate limiting, or user isolation yet.
- Default Compose credentials are for development only.
- `create_all` is used instead of versioned Alembic migrations.
- Some infrastructure errors may still expose internal details.
- With more time, I would add input/output guardrails, prompt-injection
  defenses, stricter tool-argument validation, final-answer grounding checks,
  authentication, PII masking, and rate limiting.
- I would also add distributed tracing and metrics for request latency, token
  usage, cost, selected model, fallback rate, tool errors, retrieval quality,
  and LangGraph node execution.

### Use of coding assistants

GitHub Copilot in VS Code was used as an AI-assisted development tool for
repository exploration, implementation suggestions, debugging logs, frontend
scaffolding, tests, and review of command results.

All technical and architectural decisions came from me, the developer of this
project. I selected PostgreSQL/pgvector, FastAPI, LangGraph, Gemini, Ollama,
the prompt strategy, the SQL/RAG separation, and the priorities for future
work. Copilot suggestions were reviewed, adapted, and validated with tests,
HTTP calls, logs, and Docker health checks.

## Português (PT-BR)

### Funcionalidades

- Frontend de chat em Streamlit.
- API HTTP em FastAPI.
- Respostas em streaming com Server-Sent Events (SSE).
- Agente LangGraph com roteamento explícito entre modelo e ferramentas.
- Gemini como provedor principal de LLM.
- Ollama com `qwen2.5:1.5b` como fallback local.
- PostgreSQL e pgvector para dados relacionais e embeddings.
- Orquestração com Docker Compose.
- Testes unitários para seleção de provedor, normalização de respostas e RAG.

### Exemplos de interação

O repositório inclui quatro prints do frontend Streamlit em execução na pasta
[`examples/conversations/`](./examples/conversations/):

1. [Consulta ao catálogo](./examples/conversations/01-catalogo-violao.png):
   busca violões disponíveis até um limite de preço e apresenta os valores.
2. [Política/endereço da loja](./examples/conversations/02-politica-endereco.png):
   responde uma pergunta de política/localização usando os dados da loja.
3. [Pergunta fora do escopo](./examples/conversations/03-escopo-clima.png):
   recusa educadamente uma pergunta sobre clima e redireciona para o escopo
   da loja.
4. [Categorias de instrumentos](./examples/conversations/04-categorias-piano.png):
   explica categorias de pianos em uma resposta conversacional.

O exemplo de endereço demonstra uma consulta não trivial às informações de
políticas, enquanto o exemplo do catálogo demonstra uma consulta em tempo real
aos dados estruturados do banco.

### Requisitos

- Docker Engine e Docker Compose.
- Git.
- Opcionalmente Python 3.12+ e `uv` para desenvolvimento local.
- Uma chave do Google AI Studio para usar o Gemini.

O Docker é o caminho recomendado porque fornece as dependências Python,
PostgreSQL, pgvector e Ollama de forma reproduzível.

### Configuração do ambiente

Crie o arquivo `.env` na raiz:

```dotenv
GOOGLE_API_KEY=sua_chave_do_google_ai_studio
```

`GOOGLE_API_KEY` é opcional. Se estiver vazia, a API seleciona o Ollama. Os
valores de desenvolvimento definidos pelo Docker Compose são:

```text
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=emporio_db
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:1.5b
API_URL=http://api:8000
```

Em produção, use secrets em vez das credenciais padrão e nunca versione o
`.env`.

### Como executar com Docker

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

Na primeira inicialização, o modelo do Ollama será baixado e o processo pode
demorar alguns minutos.

Endereços disponíveis:

- Frontend: <http://localhost:8501>
- API: <http://localhost:8000>
- Swagger/OpenAPI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Healthcheck: <http://localhost:8000/health>

Para carregar os dados relacionais e indexar o manual:

```bash
docker compose exec api python -m src.database.seed
```

O seed cria as tabelas, carrega os CSVs de `data/`, extrai o PDF de políticas,
divide o conteúdo, gera embeddings e grava os vetores na coleção
`politicas_loja_docs` do pgvector.

O endpoint `POST /chat` retorna um fluxo SSE em vez de aguardar a resposta
completa. Ele emite eventos JSON com `type` igual a `token`, `done` ou `error`,
permitindo que o Streamlit renderize a resposta progressivamente.

Comandos úteis:

```bash
docker compose down
docker compose down -v
docker compose exec ollama ollama list
docker compose exec postgres psql -U postgres -d emporio_db
```

### Desenvolvimento local

```bash
uv sync --dev
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
uv run streamlit run src/ui/app.py --server.port 8501
```

O PostgreSQL/pgvector e o Ollama ainda precisam estar disponíveis. Quando a
API estiver rodando localmente, use `API_URL=http://localhost:8000`.

### Testes unitários

Dentro do container da API:

```bash
docker compose exec api sh -lc \
  "PYTHONPATH=/app pytest -q tests"
```

Com o ambiente local:

```bash
uv run --dev pytest -q tests
```

Os testes cobrem seleção do Gemini/Ollama, normalização de conteúdo do
LangChain, formatação da recuperação de políticas e busca sem resultados.

O streaming também foi verificado com uma chamada real ao `POST /chat`, que
retorna múltiplos eventos `token` seguidos por um evento `done`.

### Decisões técnicas

#### FastAPI: API assíncrona e Swagger integrado

Escolhi o FastAPI por oferecer suporte a tratamento assíncrono de requisições,
importante para uma API que coordena chamadas ao LLM, banco de dados e
retrieval. A integração com Pydantic fornece validação tipada de entrada e
saída. Além disso, o FastAPI já gera automaticamente a especificação OpenAPI,
disponibilizando Swagger UI em `/docs` e ReDoc em `/redoc`, sem exigir uma
implementação separada de documentação. Isso facilita testes, integração e
evolução da API para futuros clientes, como WhatsApp, aplicativos mobile ou
outro frontend web.

#### PostgreSQL e pgvector

O PostgreSQL foi escolhido por oferecer transações, concorrência, índices,
backup, replicação e maturidade operacional para produção. Ele permite manter
catálogo, pedidos e embeddings no mesmo ecossistema. O pgvector fornece busca
semântica sem introduzir um banco vetorial separado neste estágio. Em maior
escala, a solução pode usar replicação, particionamento, pooling ou um
mecanismo de busca dedicado.

#### LangGraph

O LangGraph foi escolhido pela robustez e confiabilidade de um grafo de estado
explícito. O fluxo separa execução do modelo, seleção de ferramenta, execução
da ferramenta e resposta final. Isso facilita inspecionar, testar e evoluir
estados, ciclos, checkpoints e regras de negócio.

#### Gemini e fallback local

O Gemini é o provedor principal pela qualidade de conversação em português e
suporte a tool calling. O Ollama com `qwen2.5:1.5b` funciona como fallback
local quando a chave Google não está disponível, a inicialização do Gemini
falha ou o Gemini falha durante a inferência, como em uma resposta
`429 RESOURCE_EXHAUSTED` por cota excedida. Isso reduz a dependência de
disponibilidade, quota e rede externa, embora o modelo local possa ter
qualidade inferior.

#### Estratégia de prompt

O prompt de sistema define identidade, escopo, tom, regras de negócio,
ferramentas obrigatórias e a proibição de inventar preços, estoque, políticas,
prazos ou status. O prompt orienta o comportamento, mas não é usado como fonte
de fatos comerciais. Os fatos devem vir do SQL ou da ferramenta de retrieval.

#### Respostas em streaming

A API usa `StreamingResponse` do FastAPI com Server-Sent Events. O método
`astream(..., stream_mode="messages")` do LangGraph expõe os chunks produzidos
pelo modelo, que são enviados como eventos `token`. A execução das ferramentas
continua dentro do grafo, e o frontend recebe apenas o texto produzido pelo nó
do agente. O evento final `done` indica conclusão; o evento `error` comunica
falhas sem retornar silenciosamente uma resposta com aparência de sucesso.

#### Estratégia de retrieval/RAG

O PDF de políticas é carregado, dividido em trechos sobrepostos, convertido em
embeddings com `sentence-transformers/all-MiniLM-L6-v2` e armazenado no
pgvector. Perguntas sobre políticas chamam `consultar_politicas_loja`, que
recupera os quatro trechos mais semelhantes. Perguntas estruturadas sobre
catálogo e pedidos usam SQLAlchemy em vez de RAG, melhorando precisão e
auditabilidade para preços, estoque e status.

### Limitações conhecidas e evolução futura

- O `MemorySaver` mantém a conversa em memória e não compartilha estado entre
  réplicas nem persiste após o processo terminar.
- O seed precisa ser executado para carregar os CSVs e indexar o PDF.
- A qualidade do RAG depende da extração do PDF, segmentação e embeddings.
- O fallback local é menor e pode ser inferior em português e tool calling.
- Ainda não há autenticação, autorização, rate limiting ou isolamento de
  usuários.
- As credenciais padrão do Compose servem apenas para desenvolvimento.
- O projeto usa `create_all` em vez de migrações versionadas com Alembic.
- Alguns erros de infraestrutura ainda podem expor detalhes internos.
- Com mais tempo, eu adicionaria guardrails de entrada e saída, proteção
  contra prompt injection, validação rígida dos argumentos das ferramentas,
  verificação de groundedness da resposta, autenticação, mascaramento de PII e
  rate limiting.
- Também adicionaria tracing distribuído e métricas de latência, tokens,
  custo, modelo escolhido, taxa de fallback, erros de ferramentas, qualidade
  do retrieval e execução de cada nó do LangGraph.

### Uso de assistentes de código

Usei o GitHub Copilot no VS Code como ferramenta de desenvolvimento assistido
por IA para explorar o repositório, sugerir implementações, analisar logs,
criar o frontend, apoiar os testes e revisar resultados de comandos.

Todas as decisões técnicas e arquiteturais partiram de mim, desenvolvedora do
projeto. Eu escolhi PostgreSQL/pgvector, FastAPI, LangGraph, Gemini, Ollama, a
estratégia de prompt, a separação entre SQL e RAG e as prioridades de evolução.
As sugestões do Copilot foram analisadas, adaptadas e validadas por mim com
testes, chamadas HTTP, logs e healthchecks Docker.
