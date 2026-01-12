# Economics of Claude Code

**Created**: 2026-01-09
**Status**: seed

## Summary

A deep dive into what Claude Code actually costs under the hood versus what users pay for subscriptions. Triggered by running out of credits and discovering the hidden prompt caching layer that makes the economics work. Explores the 25x value multiplier between API costs and subscription pricing, and what it means that Anthropic is subsidizing this heavily.

## Origin

Hit the credit limit on the $100/month Max plan for the first time, which sparked a rabbit hole into personal usage data at `~/.claude/stats-cache.json`. Discovered caching mechanics that were completely unknown; realized 92% of "tokens" were cheap cache reads. Led to broader questions about business model sustainability and what these economics mean for implementing LLMs in applications.

## Correction (2026-01-11)

The original calculations in `views/brief-machias-token-summary.qmd` contained a pricing error. Opus 4.5 tokens were incorrectly priced using Opus 4.1 (legacy) rates ($15/$75 input/output) instead of the correct Opus 4.5 rates ($5/$25 input/output).

**Impact:**
- Original claimed API cost: $5,021.80
- Corrected API cost: $1,995.55
- Original value multiplier: 25x
- Corrected value multiplier: ~10x

The core conclusion remains valid: the subscription is heavily subsidized. See `transcripts/2026-01-11-pricing-correction.md` for full details.

## Open Questions

- Why isn't the caching layer better documented or discussed? Is this common knowledge that just isn't surfaced?
- How will inference costs evolve? Moore's Law rate? Faster?
- What happens when subscription prices inevitably rise, or usage caps tighten?
- How do these economics change when you're implementing LLMs in your own applications vs using a tool like Claude Code?
- What's the "efficient" way to use these tools, and does efficiency even matter on a subscription?
