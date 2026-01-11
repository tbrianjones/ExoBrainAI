# Economics of Claude Code

**Created**: 2026-01-09
**Status**: seed

## Summary

A deep dive into what Claude Code actually costs under the hood versus what users pay for subscriptions. Triggered by running out of credits and discovering the hidden prompt caching layer that makes the economics work. Explores the 25x value multiplier between API costs and subscription pricing, and what it means that Anthropic is subsidizing this heavily.

## Origin

Hit the credit limit on the $100/month Max plan for the first time, which sparked a rabbit hole into personal usage data at `~/.claude/stats-cache.json`. Discovered caching mechanics that were completely unknown; realized 92% of "tokens" were cheap cache reads. Led to broader questions about business model sustainability and what these economics mean for implementing LLMs in applications.

## Open Questions

- Why isn't the caching layer better documented or discussed? Is this common knowledge that just isn't surfaced?
- How will inference costs evolve? Moore's Law rate? Faster?
- What happens when subscription prices inevitably rise, or usage caps tighten?
- How do these economics change when you're implementing LLMs in your own applications vs using a tool like Claude Code?
- What's the "efficient" way to use these tools, and does efficiency even matter on a subscription?
