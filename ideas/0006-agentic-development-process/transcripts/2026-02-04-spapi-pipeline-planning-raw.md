# Full Transcript: SP-API Pipeline Planning
- person: TBJ
- ai: Claude (Claude Code)
- date: 2026-02-04
- source thread: e2ed097c-1fa9-45fc-a8c2-d545b4ad6c16
- raw transcript: `~/.claude/projects/-Users-tbj-projects-inventory-manager/e2ed097c-1fa9-45fc-a8c2-d545b4ad6c16.jsonl`

---

**TBJ:** Okay, we have an actual authorized seller account. I want to start building out the proper data pipeline now that we'll read files from S3, run them through the pipeline, and then populate our databases. There are a lot of steps to this, so we need to do some serious planning here. First, the local environment is up and running with that local seller account authorized. We have run the standard sync all from the Amazon Admin panel, which has pulled down S3 files for the two endpoints that we hit: the FBA inventory and the orders file folder. What I want to do is plan out development here. I think first we should get the pipeline working for those files in S3 as they would work in production, working here locally in our development environment. I then want you to look at the archived SP API integration comprehensive plan file, which outlined the initial integration with the Amazon seller SP API. I don't think we ever really finished doing that for how the app currently works. Use that for context for what has been built and what exists in our system, and then scan our actual repo to see what's currently built for how this functions and what gets triggered when we do syncs. Data goes to S3, but we don't run that data through the pipeline currently. We have a development crutch where we have sample data in a root folder in this system, and that data gets loaded in the local environment through the pipeline properly, but it's not sitting in S3 or not in the local stack as three I then want you to look at the ActiveDoc Seller API Data Gap Analysis. What we ultimately want to do here is these things. I want to get local S3, local stack working, running S3 files through the pipeline on the two endpoints that we hit. Then I want to expand our API calls out to all the endpoints of value that are specified in the Seller API data gap analysis. That will involve integrating a bunch of new endpoint calls and pulling that data down into S3. After that, we're going to need to re-evaluate what the local database looks like to store all of that data. Once we have that all pulled down and available to us, we will create sample data that will mimic real customer data in S3 in our local environment that will mimic Files so that we don't actually have to pull files to do local testing. We can rebuild the database many times for testing our data pipelines. And then we'll eventually rebuild the front end to use the new database structures based on all the new data that we're pulling in. That rebuilding the front end is kind of the full loop of this. This is a tremendous amount of updating, so I want you to look at all those files. I want you to spin up any sub-agents you need to review them and to review the repo. Don't do it in main context. Get them to summarize everything and let you know what's going on. Then I want you to ask me any questions you need to answer and propose an initial plan, really high-level plan, for putting this together and starting development on this. Keep the initial plan high-level so we can evaluate it and review it and iterate it before we go into too much detail.

---

**Claude:** I'll spin up multiple agents to gather context from the documents and codebase. Let me find those planning documents and explore the current pipeline implementation.

[Claude spins up multiple subagents to analyze: the SP-API comprehensive plan, the gap analysis, current pipeline implementation, sample data loading, and LocalStack S3 configuration]

---

**Claude:** Excellent. All agents have returned with comprehensive analysis. Let me synthesize the findings.

## Current State Summary

### What's Built and Working
| Component | Status |
|-----------|--------|
| OAuth flow | ✅ Complete |
| SP-API credentials encryption (Fernet) | ✅ Working |
| FBA Inventory fetcher → S3 | ✅ Working |
| Orders fetcher → S3 | ✅ Working |
| LocalStack S3 configuration | ✅ Working |
| S3 path conventions (`amazon/{org_id}/{endpoint}/{date}/...`) | ✅ Implemented |
| `S3Source` class for reading S3 | ✅ Exists |
| `ingest_amazon_orders.py` transformer | ✅ Exists |
| Pipeline stages (aggregate, KPI, stockout) | ✅ Working |
| Sample data loading via `warmup_local.py` | ✅ Working |

### The Gap
**Data flows to S3 but doesn't flow through the pipeline from S3.**

- `run_amazon_orders_ingest()` exists in code but is **NOT wired into PipelineController**
- No route to trigger S3-based pipeline ingestion
- LocalStack S3 starts empty (no seeded test data)
- Sample data uses `ingest_local.py` (TSV files from disk), completely separate from S3 flow

### Endpoint Coverage
- **Currently integrated**: 2 endpoints (FBA Inventory, Orders)
- **Gap analysis identified**: ~13 additional valuable endpoints across 4 priority tiers
- **Key missing data**: Product catalog, listing status, fees, pricing, inventory health/aging

## Questions Before Planning

**Local data:** For local development testing, do you want to keep the sample_data/ folder approach alongside S3, or fully migrate to S3-based sample data in LocalStack?

**Endpoint order:** For the new endpoints, should we follow the gap analysis priority tiers exactly (Catalog/Listings first, then Fees/Pricing, then Supply Chain)?

**Reports API:** The Reports API (for bulk historical data) requires an async poll-and-wait pattern different from real-time APIs. How should we handle this complexity?

**KMS encryption:** KMS encryption layer is flagged as required before production. Should this be part of this pipeline work or a separate track?

---

**TBJ:** I want to do step one, the dual approach. For right now, the current sample data loads and tests all of our frontend aggregated analysis. After we do all this migration, I want to load that raw data to check that migrations have worked.

Eventually, what we want to do is generate, instead of using a local folder, sample data that's just files sitting there that we read. We'll want the sample data to be mimicked off of all of these endpoints. We'll want to generate fake sample data so we're not storing actual seller-authorized data into files. When we do warmup, it can move from that local folder in GitHub over to S3 so that the sample data can load properly when we spin up our local development environment through S3, through our data pipeline.

As opposed to right now, where we bypass the S3 folders, that way we can do testing locally on fake seller data in the future as needed and not need to be pulling real seller data. That enables us to rebuild the whole system. That doesn't need to be; that's not the immediate need of this project, though. We want to get all the new endpoints working first, and then that'll be one of the last phases to migrate that concept over. The current sample data loading in the way it does actually lets us test the frontend endpoint too and see that calculations are still working correctly.

For the endpoint order, it doesn't really matter. It kind of feels like we could just build them all at once in parallel. They all should function essentially the same. The only caveat here is that I'm not positive our development account is going to have access to all of these endpoints. Some of them might give us errors when we try to pull data from them, so we'll have to discover that as we go. Additionally, I'd like you to look in the gap analysis file and any endpoints that we're not identified as that we should pull, that were identified as endpoints we should skip. I'd like you to evaluate why we skip them and let me know, and then ask me if we should add any of those into this process.

For the Reports API, we want all the historical data. My hope is that managing the pull and wait pattern is built into the Amazon Seller Python client API client that we're using that's in our library already. If it's not, look that up and see if it is built in there. If it's not, let's discuss architecture for how we want to build that. Check that first, though. We obviously want to implement this the correct way long term, because we're going to have to do this for accounts when they first sign up. We're going to have to pull all their history.

Don't really know what KMS security is. What do you propose? Should we just build this in from the start? Is it complex architecture? Is this just encryption that we need to layer in to data in transit or something?

---

**Claude:** Great responses. Let me address each and then move to the plan.

### Skipped Endpoints Evaluation

From the gap analysis, four endpoints were marked "Not proposed":

| Endpoint | Reason Given | Recommendation |
|----------|--------------|----------------|
| **Fulfillment Outbound API** | "Multi-channel fulfillment (out of MVP scope)" | **Skip for now.** This is for sellers who use Amazon to fulfill orders from other channels (eBay, Shopify). Only relevant if your customers do multi-channel fulfillment. |
| **AWD API** | "AWD warehouse levels (niche use)" | **Consider adding.** Amazon Warehousing & Distribution is growing. If any of your target customers use AWD, this data would be valuable for complete inventory visibility. |
| **Feeds API** | "Write operations (future: auto-reprice)" | **Skip for now.** This is for WRITING to Amazon (update prices, inventory). We're building a read-focused analytics platform. Future feature for auto-repricing. |
| **Shipping API** | "MFN shipping (target customer uses FBA)" | **Skip for now.** Only for Merchant Fulfilled Network sellers who ship their own orders. If target customers are FBA sellers, they don't need this. |

**Question:** Do any of your target customers use AWD (Amazon Warehousing & Distribution)? If so, we should add that endpoint.

### Reports API / python-amazon-sp-api Library

I researched the library. Here's what I found:

**The library provides low-level API wrappers**, not a convenience `downloadReport()` method like the JavaScript library has. We'll need to build our own async report fetcher that:
1. Calls `Reports().create_report()` to request the report
2. Polls `Reports().get_report()` until status = DONE (or CANCELLED/FATAL)
3. Calls `Reports().get_report_document()` to get the download URL
4. Downloads and decompresses the file

**Architecture recommendation:** Build a `ReportService` class that wraps this workflow with:
- Configurable polling interval (default 30 seconds)
- Max wait timeout (default 10 minutes for most reports)
- Optional SQS notification support (instead of polling) for production

This is moderate complexity but essential; we should build it properly from the start since it's used for historical backfills on new customer signups.

### KMS Encryption Explained

**What it is:** AWS Key Management Service (KMS) provides managed encryption keys. Currently, your SP-API credentials are encrypted with Fernet (a Python symmetric encryption library). The encryption key is stored in AWS Secrets Manager.

**The compliance requirement:** Amazon's Data Protection Policy (DPP) requires "AES-256 encryption at rest." Fernet uses AES-128. Adding KMS wrapping provides:
- AES-256 encryption (compliance)
- AWS-managed key rotation
- Audit logging of every key usage
- Defense-in-depth (two layers: KMS encrypts the Fernet key)

**My recommendation:** Include KMS as an early phase (not first, but before production). It's not architecturally complex; it wraps the existing Fernet encryption. Estimated 1-2 days of work. Critical before you have real customer data.

### High-Level Plan

Based on your answers, here's a proposed phased approach:

**Phase 1: Wire Up S3 → Pipeline (Foundation)**
- Connect existing S3 data to pipeline
- Add API route to trigger S3-based ingestion
- Test with current Orders and FBA Inventory endpoints

**Phase 2: Database Schema for New Data**
- Add all new tables identified in gap analysis
- Single migration with all new tables
- Add columns to existing `product` table

**Phase 3: Report Service + New Fetchers**
- Build async ReportService for Reports API
- Add all new endpoint fetchers (Catalog, Listings, Finances, Pricing, etc.)
- Handle endpoints that may not work with dev account

**Phase 4: Transformers + Pipeline Integration**
- Build transformers for each new endpoint
- Wire into PipelineController
- Add to sync orchestration

**Phase 5: KMS Encryption**
- Add KMS layer to credential encryption
- Update decryption flow
- Test thoroughly before production

**Phase 6: Sample Data Generation**
- Generate fake SP-API response data for each endpoint
- Migrate warmup to load from S3
- Enable full local testing without real credentials

**Phase 7: Frontend Updates**
- Update dashboards for new data
- Add profitability views
- Add inventory health views

**Phase 8: Testing & Verification**
- Auth boundary tests for all new routes
- Tenant isolation tests for new tables
- Idempotency tests
- Performance tests

---

**TBJ:** Got it. Let me spin up the research agents in parallel, and I'll also add the KMS note to the relevant ADR.

[Claude continues with detailed implementation planning, spinning up research agents to investigate the python-amazon-sp-api library capabilities, queuing architecture needs, and logging infrastructure requirements]

---

**Claude:** Based on all the research, I've created a comprehensive plan document. The plan expands from 2 to 15 SP-API endpoints, adds 8 new database tables, introduces a hexagonal architecture for the fetcher layer, and includes detailed testing requirements.

Key architectural decisions:
- **Hexagonal architecture** for fetcher layer with ports and adapters
- **ReportService** for async report workflow (request → poll → download)
- **Circuit breaker pattern** for API resilience
- **Parallel endpoint development** since they follow similar patterns
- **Sequential sync** for 100 users is sufficient; monitor for when queuing is needed

---

**TBJ:** I'd also like you to look up if our client library supports AWD. That endpoint may not even be available in our client library. If it is, and it looks like it's a stable endpoint, let's add it. If there's any ambiguity there, just skip it and note that we skipped it in the planning doc, as well as why.

---

**Claude:** I researched the AWD API support. The `python-amazon-sp-api` library does support AWD with dedicated classes: `AWDInbound` for inbound operations and `AWDOutbound` for outbound operations. The API version is `2024-05-09`, which is relatively recent.

The AWD API provides:
- Inventory summaries (AWD-specific stock levels)
- Inbound shipment tracking to AWD warehouses
- Outbound/replenishment status to FBA

**Recommendation:** Add AWD as a P2 priority endpoint. It uses the same OAuth credentials and follows similar patterns to other endpoints. The data is valuable for customers who use AWD as part of their supply chain.

I've updated the plan document to include AWD with three new tables:
- `product_awd_inventory_snapshots`
- `product_awd_inbound_shipments`
- `product_awd_shipment_items`

---

**Claude:** Done. I've updated the SP-API Data Pipeline Expansion Plan with the following changes:

## Changes Made

### Fixed Skills References
- Replaced the non-existent skills list with proper ADR references

### Added AWD API Integration

**New Endpoint:**
- Added AWD API as P2 priority tier (AWD inventory levels, inbound shipments, FBA replenishment status)

**New Database Tables (3):**
| Table | Natural Key | Purpose |
|-------|-------------|---------|
| `product_awd_inventory_snapshots` | `(org_id, marketplace_id, seller_sku, snapshot_date)` | Point-in-time AWD inventory levels |
| `product_awd_inbound_shipments` | `(org_id, marketplace_id, shipment_id)` | Track inbound shipments to AWD |
| `product_awd_shipment_items` | `(org_id, marketplace_id, shipment_id, seller_sku)` | SKU-level detail per shipment |

**Updated Throughout:**
- Summary (2 → 16 endpoints)
- Success metrics
- In Scope section (8 → 11 tables)
- Phase 2 duration estimate (2-3 → 3-4 days)
- Phase 3 tasks (added AWD fetcher)
- Initial sync flow (added AWD to historical backfill)
- Nightly sync flow (added AWD to per-org sync)
- Tenant isolation tests list
- Mock fixtures list
- TableNames registry
- Open questions (added AWD role access question)

**New User Story:**
- US-4: AWD Supply Chain Visibility

**Key AWD Details:**
- Uses same OAuth as other SP-API endpoints
- Requires "Amazon Warehousing and Distribution" role (may need to add to dev app)
- Rate limits: 1-2 req/sec (per application-seller pair)
- Supported by `python-amazon-sp-api` library
- Existing `awd_quantity` column in `product_inventory_snapshots` will be populated from this data
