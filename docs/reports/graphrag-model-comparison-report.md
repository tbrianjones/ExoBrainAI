# GraphRAG Model Comparison Report

**Date:** 2026-01-25
**Corpus:** 3 documents (~75K chars, 55 chunks)
**Current Model:** llama3.1:8b via native Ollama (Mac M-series GPU)

## Executive Summary

This report analyzes the quality, speed, and cost of GraphRAG indexing with the current local Ollama setup versus cloud-based alternatives. Key findings:

| Metric | Local (llama3.1:8b) | Cloud Budget (GPT-4o mini) | Cloud Premium (Claude Sonnet) |
|--------|---------------------|---------------------------|-------------------------------|
| **Indexing Time** | ~62 minutes | ~2-5 minutes | ~3-8 minutes |
| **Cost per Run** | $0 | ~$0.50-2.00 | ~$3-10 |
| **Quality** | Good (some gaps) | Good | Excellent |
| **Throughput** | 30-50 tok/s | 100+ tok/s | 50-90 tok/s |

**Recommendation:** For development and personal use, keep the local Ollama setup. For production or large corpus indexing, consider Groq's Llama 3.1 8B ($0.065/MTok) or GPT-4o mini ($0.375/MTok) for 10-30x faster indexing at minimal cost.

---

## 1. Current Local Model Analysis

### 1.1 Indexing Performance

| Metric | Value |
|--------|-------|
| **Total Time** | 62 minutes |
| **Entity Extraction** | ~25 minutes (55 chunks) |
| **Community Reports** | ~21 minutes (31 reports) |
| **Embeddings** | ~11 seconds |
| **Average per Chunk** | ~27 seconds |
| **Average per Community** | ~40 seconds |

### 1.2 Output Quality

| Artifact | Count | Quality Assessment |
|----------|-------|-------------------|
| **Entities** | 206 | Good variety; 132 concepts, 34 organizations, 6 persons |
| **Relationships** | 219 | Well-connected; avg weight 5.79 |
| **Communities** | 31 | 2 hierarchy levels (0, 1) |
| **Community Reports** | 31 | Avg 2,163 chars; coherent summaries |

### 1.3 Quality Issues Identified

| Issue | Count | Impact |
|-------|-------|--------|
| Entities with empty descriptions | 31 (15%) | Medium ; missing context for queries |
| Entities with no type | 31 (15%) | Low ; defaults to generic type |
| Isolated entities (degree 0) | 21 (10%) | Medium ; not connected to graph |
| Duplicate-ish entities | ~5-10 | Low ; "IDEA SPACE" vs "IDEA SPACES" |

**Quality Score: 7/10**

The local model produces usable results but misses some entity descriptions and creates occasional duplicates. The community reports are coherent and useful for global queries.

### 1.4 Sample Output Quality

**Good Entity Extraction:**
```
IDEA SPACE (CONCEPT, degree=14)
→ "An idea space is a digital platform that enables users to store,
   organize, and share their ideas and knowledge..."
```

**Missing Description (Quality Gap):**
```
EXOBRAIN (, degree=34)
→ "" (empty)
```

**Good Community Report (excerpt):**
```
# IDEA SPACE Community

The IDEA SPACE community revolves around the concept of idea spaces,
which are digital platforms that enable users to store, organize,
and share their ideas and knowledge. The community is comprised of
entities such as IDEA SPACE, HUMANS, BLOG POST, ACCESS CONTROL MODEL...
```

---

## 2. Cloud Model Options

### 2.1 Pricing Comparison (January 2026)

| Model | Input $/MTok | Output $/MTok | Throughput | Quality Tier |
|-------|-------------|---------------|------------|--------------|
| **Groq Llama 3.1 8B** | $0.05 | $0.08 | 1,200 tok/s | Budget |
| **GPT-4o mini** | $0.15 | $0.60 | ~100 tok/s | Budget |
| **Together Llama 8B** | $0.18 | $0.18 | ~80 tok/s | Budget |
| **Claude Haiku 4.5** | $1.00 | $5.00 | ~180 tok/s | Budget+ |
| **GPT-4o** | $2.50 | $10.00 | ~80 tok/s | Balanced |
| **Claude Sonnet 4.5** | $3.00 | $15.00 | ~90 tok/s | Balanced |
| **Claude Opus 4.5** | $5.00 | $25.00 | ~50 tok/s | Premium |

### 2.2 Token Usage Estimation

GraphRAG has a **~40x token multiplier** from source documents to total processing:

| Your Corpus | Source Tokens | Estimated Total | Ratio |
|-------------|---------------|-----------------|-------|
| 3 documents | ~15,000 | ~600,000 | 40x |
| 50 documents | ~250,000 | ~10,000,000 | 40x |
| 100 documents | ~500,000 | ~20,000,000 | 40x |

*Token split: ~96% input, ~4% output*

### 2.3 Cost Estimates for Current Corpus (3 docs, ~600K tokens)

| Model | Input Cost | Output Cost | **Total** |
|-------|-----------|-------------|-----------|
| **Groq Llama 8B** | $0.03 | $0.002 | **$0.03** |
| **GPT-4o mini** | $0.09 | $0.01 | **$0.10** |
| **Claude Haiku 4.5** | $0.58 | $0.12 | **$0.70** |
| **GPT-4o** | $1.44 | $0.24 | **$1.68** |
| **Claude Sonnet 4.5** | $1.73 | $0.36 | **$2.09** |
| **Claude Opus 4.5** | $2.88 | $0.60 | **$3.48** |

### 2.4 Cost Estimates for Larger Corpus (100 docs, ~20M tokens)

| Model | Estimated Cost | Time Estimate |
|-------|---------------|---------------|
| **Groq Llama 8B** | ~$1.10 | ~5 minutes |
| **GPT-4o mini** | ~$3.30 | ~15 minutes |
| **Claude Haiku 4.5** | ~$23 | ~10 minutes |
| **GPT-4o** | ~$55 | ~25 minutes |
| **Claude Sonnet 4.5** | ~$70 | ~20 minutes |
| **Local Ollama** | $0 | ~35 hours |

---

## 3. Quality Comparison

### 3.1 Expected Quality by Model Tier

| Tier | Models | Entity Extraction | Summarization | Edge Cases |
|------|--------|-------------------|---------------|------------|
| **Budget** | Llama 8B, GPT-4o mini | Good | Good | May miss nuance |
| **Balanced** | GPT-4o, Claude Sonnet | Very Good | Excellent | Handles well |
| **Premium** | Claude Opus | Excellent | Excellent | Best handling |
| **Local** | Ollama llama3.1:8b | Good | Good | Some gaps |

### 3.2 Quality Trade-offs

**Local Ollama (llama3.1:8b)**
- ✅ Free to run
- ✅ Data stays local
- ✅ No rate limits
- ⚠️ 15% entities missing descriptions
- ⚠️ Slower (30-50 tok/s)
- ⚠️ May miss subtle relationships

**Cloud Budget (GPT-4o mini, Groq Llama)**
- ✅ Very fast (100-1200 tok/s)
- ✅ Low cost ($0.03-0.10 per run)
- ✅ Better instruction following
- ⚠️ Data leaves machine
- ⚠️ Rate limits apply
- ⚠️ Similar quality to local

**Cloud Premium (Claude Sonnet/Opus)**
- ✅ Best entity extraction
- ✅ Nuanced relationship detection
- ✅ Better community summaries
- ⚠️ Higher cost ($2-5 per run)
- ⚠️ Data leaves machine
- ⚠️ May be overkill for simple docs

---

## 4. Speed Comparison

| Deployment | Throughput | 3 Doc Index | 100 Doc Index |
|------------|-----------|-------------|---------------|
| **Docker Ollama (CPU)** | 1-2 tok/s | ~20 hours | ~700 hours |
| **Native Ollama (GPU)** | 30-50 tok/s | ~62 min | ~35 hours |
| **Groq Llama 8B** | 1,200 tok/s | ~30 sec | ~5 min |
| **GPT-4o mini** | 100 tok/s | ~5 min | ~15 min |
| **Claude Sonnet** | 90 tok/s | ~6 min | ~20 min |

**Key Insight:** Groq is 24-40x faster than native Ollama, and 600-1200x faster than Docker Ollama.

---

## 5. Recommendations

### 5.1 For Personal/Development Use (Current Setup)

**Keep local Ollama.** The current setup is:
- Free
- Private (data never leaves machine)
- Good enough quality for personal knowledge base
- Acceptable speed for small corpus (<50 docs)

**Optimization:** Run rebuilds overnight or during breaks.

### 5.2 For Faster Indexing (Cost-Conscious)

**Use Groq Llama 3.1 8B:**
- Cost: ~$0.03 per 3-doc run, ~$1.10 per 100-doc run
- Speed: 30-40x faster than local
- Quality: Comparable to local Ollama
- Setup: Change `api_base` to Groq endpoint, add API key

### 5.3 For Better Quality (Production)

**Use Claude Haiku 4.5 or GPT-4o mini:**
- Cost: $0.10-0.70 per 3-doc run
- Speed: 10-20x faster than local
- Quality: Better entity descriptions, fewer gaps
- Batch API: 50% discount for non-urgent indexing

### 5.4 For Best Quality (Research/High-Stakes)

**Use Claude Sonnet 4.5:**
- Cost: ~$2 per 3-doc run
- Quality: Excellent entity extraction and summarization
- Best for: Documents where accuracy matters

---

## 6. Configuration Changes for Cloud Models

### 6.1 Switching to OpenAI/Groq

Edit `engine/src/graphrag/config.py`:

```python
"default_chat_model": {
    "model_provider": "openai",  # or "groq"
    "api_key": "${OPENAI_API_KEY}",  # or GROQ_API_KEY
    "api_base": "https://api.openai.com/v1",  # or https://api.groq.com/openai/v1
    "model": "gpt-4o-mini",  # or "llama-3.1-8b-instant"
    "model_supports_json": True,  # Cloud models handle JSON well
    "request_timeout": 120.0,  # Faster timeout for cloud
    "concurrent_requests": 4,  # Can parallelize with cloud
}
```

### 6.2 Switching to Claude

GraphRAG supports Anthropic natively:

```python
"default_chat_model": {
    "model_provider": "anthropic",
    "api_key": "${ANTHROPIC_API_KEY}",
    "model": "claude-3-5-haiku-20241022",
    "model_supports_json": True,
    "concurrent_requests": 4,
}
```

### 6.3 Environment Variables

Add to `.env`:
```bash
# For OpenAI
OPENAI_API_KEY=sk-...

# For Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# For Groq
GROQ_API_KEY=gsk_...
```

---

## 7. Summary Table

| Factor | Local Ollama | Groq Llama 8B | GPT-4o mini | Claude Sonnet |
|--------|-------------|---------------|-------------|---------------|
| **Cost/Run (3 docs)** | $0 | $0.03 | $0.10 | $2.09 |
| **Cost/Run (100 docs)** | $0 | $1.10 | $3.30 | $70 |
| **Time (3 docs)** | 62 min | 30 sec | 5 min | 6 min |
| **Time (100 docs)** | 35 hrs | 5 min | 15 min | 20 min |
| **Quality** | 7/10 | 7/10 | 8/10 | 9/10 |
| **Privacy** | ✅ Local | ❌ Cloud | ❌ Cloud | ❌ Cloud |
| **Setup Effort** | Done | Medium | Medium | Medium |

---

## 8. Conclusion

The current local Ollama setup is **appropriate for personal use** with a small corpus. The 62-minute indexing time is acceptable for occasional rebuilds, and the quality is sufficient for personal knowledge management.

For users who need:
- **Faster iteration:** Switch to Groq (~$1/rebuild for 100 docs, 5 min)
- **Better quality:** Switch to Claude Haiku 4.5 (~$23/rebuild for 100 docs)
- **Best quality:** Switch to Claude Sonnet (~$70/rebuild for 100 docs)

The system is already architected to support cloud models; only configuration changes are needed.

---

## Appendix: Raw Metrics

### Current Index Statistics
- Documents: 3
- Text chunks: 55
- Entities: 206 (132 concepts, 34 orgs, 6 persons, 31 untyped)
- Relationships: 219
- Communities: 31 (16 at level 1, 15 at level 0)
- Community reports: 31 (avg 2,163 chars)

### Timing Breakdown
- Start: 2026-01-25 17:49:13
- End: 2026-01-25 18:51:39
- Total: 62 minutes 26 seconds
- Entity extraction: ~25 min
- Community reports (level 1): 10 min 40 sec (16 reports)
- Community reports (level 0): 9 min 59 sec (15 reports)
- Embeddings: 11 seconds

### Quality Metrics
- Entities with descriptions: 175/206 (85%)
- Entities with type: 175/206 (85%)
- Connected entities: 185/206 (90%)
- Average entity degree: 2.06
- Max entity degree: 34 (EXOBRAIN)
- Average relationship weight: 5.79
