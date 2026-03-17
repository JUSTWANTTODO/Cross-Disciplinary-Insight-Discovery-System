# Silo Synapse

Silo Synapse is an agentic AI research assistant that helps generate **non-obvious, testable cross-disciplinary hypotheses** from user input (text or PDF), grounded in live scientific literature.

It combines:
- input cleaning and preprocessing
- live paper retrieval (arXiv + PubMed)
- semantic ranking via embeddings
- hypothesis generation via Gemini on Vertex AI
- heuristic confidence scoring
- iterative refinement workflow in a Streamlit UI

## What This Project Does

1. Accepts research context from the user (text area or uploaded PDF).
2. Cleans and normalizes that text.
3. Rewrites it into a clearer search query.
4. Fetches recent/relevant papers from arXiv and PubMed.
5. Ranks papers by embedding similarity to the user input.
6. Generates structured hypotheses using an LLM.
7. Adds insight badges and confidence labels.
8. Supports iterative follow-up exploration up to multiple rounds.

## Features

- Text input and PDF upload flow
- Live multi-source literature search
- Embedding-based paper ranking
- Structured JSON hypothesis generation
- Insight badges for novelty framing
- Confidence scoring (heuristic)
- Recommended-hypothesis tagging
- Suggested next-focus guidance
- Streamlit session state for iterative exploration
- Dockerized runtime for deployment

## Project Structure

```text
.
|-- app.py
|-- check_models.py
|-- Dockerfile
|-- requirements.txt
|-- agents/
|   |-- __init__.py
|   `-- research_agent.py
|-- landing/
|   `-- index.html
|-- services/
|   |-- __init__.py
|   |-- confidence_service.py
|   |-- embedding_service.py
|   |-- genai_client.py
|   |-- insight_service.py
|   |-- intent_service.py
|   `-- live_search_service.py
`-- utils/
    |-- pdf_parser.py
    `-- text_cleaner.py
```

## Module-by-Module Breakdown

### `app.py`
Main Streamlit application. Handles UI, session state, query flow, paper display, hypothesis rendering, confidence display, and iterative exploration.

### `agents/research_agent.py`
Builds the prompt and calls Gemini (`gemini-2.5-flash-lite`) to generate structured hypothesis output.

### `services/genai_client.py`
Provides cached Vertex AI Gemini client initialization.

### `services/intent_service.py`
Converts raw user input into a clearer academic search query.

### `services/live_search_service.py`
Fetches papers from:
- arXiv API
- PubMed E-utilities API

Parses responses and returns unified paper objects.

### `services/embedding_service.py`
Embeds query and abstract chunks using `text-embedding-004`, computes cosine similarity, and ranks papers.

### `services/insight_service.py`
Generates short novelty/insight badges for each hypothesis and safely extracts JSON output.

### `services/confidence_service.py`
Computes a heuristic confidence score from:
- evidence count
- intent alignment (similarity fallback)
- interdisciplinarity signal

### `utils/pdf_parser.py`
Extracts text from PDFs and removes repeated lines (common header/footer noise).

### `utils/text_cleaner.py`
Removes references, citations, noisy symbols, normalizes whitespace, and truncates text to bounded length.

### `check_models.py`
Standalone utility script to list available Gemini models using `GEMINI_API_KEY`.

### `landing/index.html`
Static landing page (Tailwind + custom styling) that links to deployed app URL.

## Technologies Used

### Language and Framework
- Python 3.11
- Streamlit

### AI / LLM / Embeddings
- Google Gemini models
- Vertex AI integration (`google.genai` via Vertex)
- `gemini-2.5-flash-lite` (generation and intent)
- `text-embedding-004` (embedding similarity)

### Data Sources
- arXiv API (`export.arxiv.org`)
- PubMed E-utilities (`esearch.fcgi`, `efetch.fcgi`)

### Libraries
- `streamlit`
- `python-dotenv`
- `requests`
- `pypdf`
- `numpy` (declared dependency)
- `google-cloud-aiplatform`
- `vertexai`

### Frontend (Landing Page)
- HTML5
- Tailwind CSS (CDN)
- Google Fonts
- Material Symbols

### DevOps / Runtime
- Docker (`python:3.11-slim`)
- Streamlit server on port `8080`

## Environment Variables

Create a `.env` file in the project root.

For the Streamlit app (Vertex AI path):

```env
GCP_PROJECT_ID=your-gcp-project-id
```

For `check_models.py` utility script:

```env
GEMINI_API_KEY=your-gemini-api-key
```

Note: The main app client uses Vertex AI (`GCP_PROJECT_ID`), while `check_models.py` uses API key auth.

## Installation and Run (Local)

1. Create and activate virtual environment.
2. Install dependencies.
3. Add `.env` variables.
4. Run Streamlit app.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Default local app URL is usually:
- `http://localhost:8501`

## Run With Docker

Build image:

```bash
docker build -t silo-synapse .
```

Run container:

```bash
docker run --rm -p 8080:8080 --env-file .env silo-synapse
```

App will be available at:
- `http://localhost:8080`


## Deployment (GCP)

This project is deployed on Google Cloud Run.

### Production URL

- `https://silo-synapse-678541121222.us-central1.run.app/`

### GCP Services Used

- Cloud Run (container hosting)
- Artifact Registry (container image storage, if used in your setup)
- Vertex AI (Gemini + embeddings)

### Deploy to Cloud Run

Example deployment flow:

```bash
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/silo-synapse
gcloud run deploy silo-synapse \
    --image gcr.io/YOUR_GCP_PROJECT_ID/silo-synapse \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars GCP_PROJECT_ID=YOUR_GCP_PROJECT_ID
```

After deployment, Cloud Run provides a service URL you can use publicly.

## High-Level Request Flow

```text
User Input (Text/PDF)
    -> clean_text / extract_text_from_pdf
    -> normalize_intent
    -> unified_search (arXiv + PubMed)
    -> rank_papers_by_similarity (embeddings)
    -> generate_hypotheses (Gemini)
    -> generate_insight_badges
    -> compute_confidence
    -> Streamlit render + optional iterative refinement
```

## Known Constraints

- Confidence is heuristic, not statistical certainty.
- Live search quality depends on external API availability and response quality.
- Model output parsing currently relies on structured text patterns/JSON-like output.
- Evidence and rationale consistency depends on model adherence to prompt format.

## Future Improvements

- Strict schema validation (`json.loads` + Pydantic) for hypothesis output
- Better parser instead of string-splitting blocks in UI
- Add unit tests for services
- Add retry/backoff policies per external API type
- Add caching for search results and embeddings across sessions
- Add observability/logging for failed generations

## Disclaimer

Outputs are exploratory research hypotheses, not validated scientific conclusions. Evidence references may be incomplete or context-dependent. Confidence labels indicate heuristic relevance, not empirical proof.
