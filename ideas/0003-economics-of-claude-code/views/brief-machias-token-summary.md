---
title: "Hey Machias: Look At These Ridiculous Numbers"
subtitle: Two months of Claude Code usage and what it would've cost me at API rates
brief: A quick breakdown of my Claude Code token consumption, the equivalent API costs, and the absurd value multiplier if you actually max out a subscription.
type: brief
status: draft
published: true
audience: Machias (friend, fellow dev)
voice: Buddy at a bar sharing something wild he discovered
style:
  humor: 70
  technical: 85
  formality: 15
  warmth: 80
---

## Outline
- One line intro
- Table 1: My token usage (Nov 15, 2025 to Jan 9, 2026)
- Table 2: What I would've paid at API rates
- Table 3: What maxed usage would cost at API rates
- Sign off

## Content

Machias. I ran out of Claude Code credits and fell down a rabbit hole. Here's the damage.

### What I Actually Used (8 weeks)

This is raw token consumption across models. Note: 92% of those tokens are "cache reads" which I'll explain in a sec.

| Model | Input | Output | Cache Read | Cache Write | Total |
|-------|------:|-------:|-----------:|------------:|------:|
| Opus 4.5 | 950,860 | 2,588,991 | 1,358,438,079 | 122,308,882 | **1,484,286,812** |
| Sonnet 4.5 | 201,228 | 4,151,480 | 684,762,875 | 50,804,886 | **739,920,469** |
| Opus 4.1 | 708 | 67,469 | 6,475,584 | 464,816 | **7,008,577** |
| Haiku 4.5 | 96 | 139 | 266,580 | 67,004 | **333,819** |
| **TOTAL** | **1,152,892** | **6,808,079** | **2,049,943,118** | **173,645,588** | **2,231,549,677** |

Yes, 2.2 billion tokens. But here's the thing: every message you send in Claude Code includes the ENTIRE conversation history. So the context gets re-sent constantly. Prompt caching means if it's already been sent, you pay 10% of normal price. That's what "cache read" means. It's how this doesn't bankrupt everyone.

### What That Would've Cost at API Rates

Using Anthropic's published pricing (January 2026):

| Model | Input | Output | Cache Read | Cache Write | **Total** |
|-------|------:|-------:|-----------:|------------:|----------:|
| Opus 4.5 | $4.75 | $64.72 | $679.22 | $764.43 | **$1,513.12** |
| Sonnet 4.5 | $0.60 | $62.27 | $205.43 | $190.52 | **$458.82** |
| Opus 4.1 | $0.01 | $5.06 | $9.71 | $8.72 | **$23.50** |
| Haiku 4.5 | $0.00 | $0.00 | $0.03 | $0.08 | **$0.11** |
| **TOTAL** | **$5.36** | **$132.05** | **$894.39** | **$963.75** | **$1,995.55** |

**I paid $200 (two months of the $100 Max plan). API equivalent: $1,995.55. That's a 10x value multiplier.**

### If You Maxed Out the Subscription

This is the wild part. Anthropic publishes weekly usage limits. If you used every single hour they allow:

| Plan | Monthly Cost | Maxed API Equivalent | Value Multiplier |
|------|-------------:|---------------------:|-----------------:|
| Max 5x | $100 | ~$8,250 | **~83x** |
| Max 20x | $200 | ~$13,300 | **~67x** |

I'm apparently using about 12% of what the plan allows. Someone grinding harder than me is getting 80x value.

Anthropic is either losing money on power users, betting inference costs drop fast, or both. Either way: good deal.

Talk soon.

---

## Tags

claude code, token economics, api pricing, prompt caching, anthropic, llm costs, subscription value, usage analysis, developer tools, ai economics

## Hashtags

#ClaudeCode, #LLMCosts, #AIPricing, #DeveloperTools, #Anthropic, #TokenEconomics, #PromptCaching, #AISubscription, #TechAnalysis, #BuildingWithAI
