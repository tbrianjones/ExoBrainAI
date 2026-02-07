# SP-API Pipeline Expansion Planning Session
- person: TBJ
- ai: Claude Opus 4.5 (Claude Code)
- emotional analysis: engaged, methodical, strategically focused; excitement about moving from prototype to production architecture
- source thread: e2ed097c-1fa9-45fc-a8c2-d545b4ad6c16
- raw transcript: `~/.claude/projects/-Users-tbj-projects-inventory-manager/e2ed097c-1fa9-45fc-a8c2-d545b4ad6c16.jsonl`

## Ideas & Themes

- **Parallel Agent Research Pattern**: TBJ directed Claude to spin up multiple subagents in parallel to analyze different aspects of the problem (existing plans, gap analysis, current pipeline code, sample data loading, LocalStack S3 configuration). This demonstrates a sophisticated orchestration approach where the main context remains clean while subagents gather and synthesize information.

- **Development Crutch Awareness**: The conversation surfaced a key architectural debt; sample data currently loads from local files, bypassing the S3 flow entirely. TBJ articulated this as a "development crutch" that needs resolution before the pipeline can work as it would in production.

- **Rate Limits Are Per-Seller (Discovery)**: A significant architectural finding emerged from research; SP-API rate limits apply per application-seller pair, not globally per application. This means 100 organizations can sync in parallel without competing for rate limit quota; a fundamental shift in how to think about the sync architecture.

- **Reports API Async Complexity**: The Reports API introduces a fundamentally different workflow; request a report, poll for completion, download and decompress. This async pattern requires new infrastructure (Notifications API subscriptions, SQS handlers, workflow tracking tables) beyond what exists for the current real-time API endpoints.

- **Data Kiosk Deferral Decision**: Research revealed that Amazon's Data Kiosk (the next-generation GraphQL reporting API) lacks the datasets needed for inventory, listings, and fee reports. The decision to defer Data Kiosk and build on Reports API now was grounded in practical availability rather than theoretical preference.

- **Phased Development Structure**: The final plan emerged as an 8-phase approach starting with foundation fixes (wiring existing S3 flow), through Reports API infrastructure, database schema, fetchers, transformers, production sync architecture, synthetic sample data, and finally frontend updates. Each phase has clear dependencies and verification criteria.

- **Idempotency as Core Requirement**: Throughout the discussion, idempotency surfaced repeatedly; the need for re-runnable syncs that produce zero duplicates. This drove decisions about row hashing, unique constraints, and UPSERT patterns at multiple layers of the architecture.

## Transcript Summary

### Opening Problem Statement

TBJ set the context: "We have an actual authorized seller account. I want to start building out the proper data pipeline now that we'll read files from S3, run them through the pipeline, and then populate our databases." The key insight was recognizing this as a major architectural evolution, not just adding endpoints. TBJ explicitly requested a high-level plan before diving into implementation details.

### Research Phase Strategy

TBJ directed the research approach: "Spin up any sub-agents you need to review them and to review the repo. Don't do it in main context. Get them to summarize everything and let you know what's going on." This established a pattern where the main conversation stayed focused on synthesis while parallel agents handled deep dives into specific areas.

### Existing Infrastructure Assessment

The subagent research revealed the current state:
- OAuth flow works; credentials are encrypted in the database
- FBA Inventory and Orders endpoints fetch data to S3
- Pipeline exists but the S3 to database ingestion path is not fully wired
- Sample data loads from local `sample_data/` folder via `warmup_local.py`, bypassing the S3 flow entirely
- LocalStack is configured and running for local S3 emulation
- `data_amazon_api_log` tracks API calls but lacks support for async report workflows

### Gap Analysis Integration

The existing Seller API Data Gap Analysis document identified the scope expansion needed: from 2 endpoints (Orders, FBA Inventory) to approximately 15 endpoints including Catalog Items, Listings Items, various Reports (Fee Estimates, Inventory Health, Storage Fees), Finances API, and Product Pricing API. Each endpoint category maps to specific business requirements: catalog completeness, profitability analysis, aged inventory fee avoidance, and competitive positioning.

### Rate Limit Architecture Discovery

Research into SP-API rate limiting produced a key finding: "Rate limits apply per application-seller pair, NOT globally per application. Each authorized seller has their own quota bucket." This fundamentally changed the sync architecture discussion; rather than serializing all syncs to avoid global rate limit competition, the system can sync organizations in parallel since each seller's credentials have independent rate limit buckets.

### Reports API Infrastructure

The Reports API workflow emerged as the most complex new infrastructure need. Unlike real-time APIs that return data immediately, Reports API requires: requesting report generation, polling for completion (or subscribing to Notifications API), and downloading/decompressing the result. Research into `python-amazon-sp-api` confirmed the library provides convenience methods but the polling/notification workflow would need custom orchestration.

### Database Schema Expansion

The plan specified 8 new tables with detailed schemas:
- `product_financial_events` for actual per-order fees from Finances API
- `product_pricing_snapshots` for historical competitive pricing
- `product_inventory_health_snapshots` for age bucket tracking (critical for "never pay aged inventory fees" goal)
- `product_fee_estimates` for per-ASIN fee breakdown
- `product_storage_fees` for actual monthly storage costs
- `product_listing_current` for current listing state (SCD Type 1)
- `product_pricing_current` for current competitive position
- `product_profitability_summary` for pre-computed profitability metrics

### Logging Infrastructure Enhancement

Three logging improvements were specified:
1. Extend existing `data_amazon_api_log` with workflow type, parent sync ID, and pipeline processed timestamp
2. New `data_amazon_report_workflow` table to track async report lifecycle from request through download
3. New `data_pipeline_file_ingestion` table to track S3 files through the pipeline for full traceability

### Production Sync Architecture

The discussion addressed scale concerns for approximately 100 organizations. Key decisions:
- Initial sync (OAuth completion): trigger full 30-day backfill
- Nightly sync: parallel-by-org execution starting at 2 AM UTC
- Per-seller rate tracking (since rate limits are per-seller)
- Retry logic with max 3 attempts for failed syncs
- PII anonymization scheduling to maintain 30-day compliance

The analysis concluded that sequential processing would work for 100 organizations given the per-seller rate limit architecture, with a migration path to SQS/Lambda if needed at larger scale.

### Synthetic Sample Data Strategy

TBJ specified the end goal: "Create sample data that will mimic real customer data in S3 in our local environment that will mimic files so that we don't actually have to pull files to do local testing. We can rebuild the database many times for testing our data pipelines." This drives Phase 6 of the plan; generating synthetic SP-API responses that flow through LocalStack S3 into the pipeline, replacing the current local-file-based approach.

### Decision to Defer Data Kiosk

Research into Amazon's Data Kiosk API revealed it is now generally available but currently offers limited datasets (Seller Sales and Traffic, Seller Economics, Cross-Domain Vendor Analytics). The specific inventory, listings, and fee reports needed are still in the traditional Reports API. The recommendation: build on Reports API now with awareness that migration to Data Kiosk will be needed when Amazon deprecates the relevant report types.

### SP-API Subscription Fees Context

Research surfaced the upcoming fee structure: starting January 31, 2026, a $1,400 annual subscription fee for third-party developers, with usage-based fees beginning April 30, 2026. The Basic tier includes 2.5 million GET calls monthly. This context influenced recommendations around optimizing API call patterns and preferring bulk reports over repeated individual GET requests.

### Port/Adapter Pattern Decision

The plan specifies a port/adapter pattern for the SP-API client layer, making the underlying `python-amazon-sp-api` library swappable without rewriting business logic. Structure: abstract port interfaces in `ports/` subdirectory, implementation adapters in `adapters/saleweaver/`, with resilience patterns (backoff, circuit breaker) centralized in `resilience.py`.

### Final Plan Structure

The conversation concluded with an 8-phase implementation plan:
- Phase 0: Foundation and critical fixes (2-3 days)
- Phase 1: Reports API infrastructure (3-4 days)
- Phase 2: Database schema for all tables (2-3 days)
- Phase 3: Expand fetchers for all endpoints (5-7 days)
- Phase 4: Pipeline transformers (4-5 days)
- Phase 5: Production sync architecture (3-4 days)
- Phase 6: Synthetic sample data (2-3 days)
- Phase 7: Frontend updates (5-7 days; separate track)
- Phase 8: Testing and verification (integrated throughout)

Each phase has explicit tasks, testing requirements, and acceptance criteria documented in the resulting plan file at `docs/active/20260203-sp-api-data-pipeline-expansion-plan-claude.md`.
