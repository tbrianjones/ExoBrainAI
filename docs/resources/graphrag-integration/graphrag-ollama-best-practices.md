# GraphRAG + Ollama Best Practices

> Generated from expert analysis of ExoBrain v2 implementation on 2026-01-24

## Executive Summary

Running GraphRAG with local Ollama models requires careful configuration to avoid timeouts and memory issues. The key constraints are:

1. **Context length must match prompt size**: GraphRAG community_reports prompts can reach 10,000+ tokens
2. **Local models are 10-100x slower than cloud APIs**: Timeouts need to reflect this
3. **Model size matters**: Below 8B parameters, models struggle with JSON formatting and complex prompts
4. **Chunk size affects entity extraction**: Smaller chunks = better entity linking = faster reports

## Configuration Requirements

### Minimum Model Requirements

| Model Type | Minimum Size | Recommended | Notes |
|------------|--------------|-------------|-------|
| Chat/LLM | 7B | 8B (llama3.1:8b) | 3B models struggle with JSON output |
| Embeddings | 137M | nomic-embed-text | Smaller is fine here |

### Context Length

```yaml
# In docker-compose.yml (Ollama environment)
OLLAMA_CONTEXT_LENGTH: 8192   # Minimum 4096, prefer 8192 or 12288
```

**Why**: GraphRAG's community_reports phase sends prompts with:
- System prompt: ~500 tokens
- Community entities: ~2,000-4,000 tokens
- Relationships: ~1,000-2,000 tokens
- Instructions: ~500 tokens
- Expected output: ~2,000 tokens

Total: 6,000-9,000 tokens. A 2048 context truncates 70%+ of the input.

### Timeout Configuration

```yaml
# In settings.yaml
models:
  default_chat_model:
    request_timeout: 1200.0   # 20 minutes minimum for local LLMs
    max_retries: 2            # Don't waste time on retries
```

**Why**: Community reports take 120-180 seconds *each* on local hardware. With 20-40 communities, total time = 40-120 minutes. Set timeouts accordingly.

### Chunk Size

```yaml
chunks:
  size: 300           # NOT 800+; smaller chunks = better entity extraction
  overlap: 50         # 50-100 is sufficient
```

**Why**: Large chunks cause:
- Fewer entity-relationship links across chunk boundaries
- Sparse communities that need more LLM work to summarize
- Clustering algorithm failures in "fast" mode

### JSON Mode

```yaml
models:
  default_chat_model:
    model_supports_json: false   # CRITICAL: Local models don't guarantee JSON
```

**Why**: When set to `true`, GraphRAG expects valid JSON responses. Llama models often:
- Generate trailing text after JSON
- Omit closing brackets
- Use single quotes instead of double quotes

This causes silent failures in entity extraction.

## Docker Configuration

### Docker Desktop Memory Requirements

**CRITICAL**: Docker Desktop must have sufficient memory allocated.

| Model | Minimum RAM | Recommended RAM |
|-------|-------------|-----------------|
| llama3.2:3b | 6GB | 8GB |
| llama3.1:8b | 10GB | 12-16GB |

To configure on Mac/Windows:
1. Open Docker Desktop → Settings → Resources
2. Set Memory to 12GB or higher
3. Apply & Restart Docker Desktop

Without sufficient memory, Ollama will load the model but the runner process will be killed during inference with "signal: killed".

### Health Check

```yaml
# Check model is loaded, not just Ollama running
healthcheck:
  test: ["CMD", "ollama", "show", "llama3.1:8b"]
  interval: 30s
  timeout: 30s
  retries: 3
  start_period: 60s      # Model loading takes time
```

### Network Configuration

```yaml
networks:
  exobrain-net:
    driver: bridge

services:
  exobrain:
    networks:
      - exobrain-net
  ollama:
    networks:
      - exobrain-net
```

## GraphRAG-Specific Settings

### Entity Extraction

```yaml
extract_graph:
  model_id: default_chat_model
  entity_types:
    - person
    - organization
    - project            # Domain-specific is better than generic
    - technology
    - idea
  max_gleanings: 0       # Reduce LLM calls
  temperature: 0.0       # Deterministic extraction
```

### Community Reports

```yaml
community_reports:
  model_id: default_chat_model
  max_length: 1500       # Reduced from 2000
  max_input_length: 4000 # Reduced from 8000; must fit in context
  strategy: top_down     # Faster than bottom_up
  temperature: 0.0       # Deterministic reports
```

### Disabled Features (for performance)

```yaml
embed_graph:
  enabled: false         # Requires many embedding calls
umap:
  enabled: false         # Visualization only
snapshots:
  graphml: false
  embeddings: false
extract_claims:
  enabled: false         # Expensive LLM calls
```

## Testing Strategy

### Phase 1: Validate Pipeline (Fast Mode)

```bash
# Start fresh
docker compose down -v
docker compose up -d
docker compose exec exobrain exobrain init

# Create test document
echo "Test content about AI and machine learning" | docker compose exec -T exobrain exobrain capture

# Stage and index with NLP (no LLM)
docker compose exec exobrain exobrain stage --all
docker compose exec exobrain exobrain index --fast --no-incremental

# Verify artifacts exist
docker compose exec exobrain ls -la /cache/graphrag/output/
```

### Phase 2: Validate LLM Mode

```bash
# Clear and rebuild with LLM
docker compose exec exobrain exobrain rebuild

# Monitor progress
docker compose logs -f exobrain

# Test query (requires community_reports.parquet)
docker compose exec exobrain exobrain query "What themes emerge?"
```

## Troubleshooting

### Timeout on community_reports

**Symptoms**: entities.parquet exists, community_reports.parquet missing

**Causes**:
1. Context length too small (most common)
2. Request timeout too short
3. Model too small

**Fix**: Check context length first:
```bash
docker compose exec ollama ollama show llama3.1:8b --modelfile | grep -i context
```

### Empty or Generic Responses

**Symptoms**: Query returns but results are generic/wrong

**Causes**:
1. Truncated prompts due to small context
2. `model_supports_json: true` causing parse failures

**Fix**: Set `model_supports_json: false` and increase context

### NLP Mode Freezes System

**Symptoms**: CPU spikes to 100%, system becomes unresponsive

**Causes**:
1. Chunk size too large for spaCy
2. No resource limits on Docker container

**Fix**: Reduce chunk size to 300, add Docker memory limits

## Performance Expectations

| Documents | LLM Mode | Fast Mode | Notes |
|-----------|----------|-----------|-------|
| 5-10 | 30-60 min | 2-5 min | Community reports dominate |
| 10-50 | 2-4 hours | 10-20 min | Consider cloud API |
| 50-100 | 4-8 hours | 30-60 min | Definitely use cloud API |
| 100+ | Days | 1-2 hours | Cloud API required |

For large document sets, add cloud model fallback:

```yaml
models:
  cloud_fallback:
    type: chat
    model_provider: anthropic
    model: claude-3-haiku-20240307
    api_key: ${ANTHROPIC_API_KEY}
    request_timeout: 120.0
```

## Sources

- [GraphRAG Detailed Configuration](https://microsoft.github.io/graphrag/config/yaml/)
- [GraphRAG Local Setup via Ollama: Pitfalls Prevention Guide](https://chishengliu.com/posts/graphrag-local-ollama/)
- [graphrag-local-ollama Repository](https://github.com/TheAiSingularity/graphrag-local-ollama)
- [GitHub Issue #940: community_reports.parquet not generated](https://github.com/microsoft/graphrag/issues/940)
- [GitHub Issue #345: Ollama Community Support](https://github.com/microsoft/graphrag/issues/345)
