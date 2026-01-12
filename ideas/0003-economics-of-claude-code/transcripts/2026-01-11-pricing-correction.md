# Pricing Correction: Opus 4.5 vs Opus 4.1 Rates
- person: T. Brian Jones
- ai: Claude Opus 4.5
- emotional analysis: corrective, slightly embarrassed but not derailed; relief that core thesis holds; intellectual honesty taking precedence over ego

## Ideas & Themes

- **External Validation Catches Error**: Gemini flagged that the original article's pricing calculations were based on incorrect API rates. This demonstrates the value of cross-model review; the human's original calculations and Claude's review both missed the error.

- **The Magnitude of the Error**: Opus 4.5 was priced at $15/$75 per million tokens (input/output), but the actual Opus 4.5 pricing is $5/$25. The article had used Opus 4.1 rates for an Opus 4.5 calculation, inflating the API cost estimate from approximately $2,000 to approximately $5,000.

- **Revised Value Multiplier**: The corrected math yields roughly 10x value multiplier, not 25x. Still significant; the core thesis that Anthropic is subsidizing Claude Code subscriptions remains valid. The dramatic framing needs adjustment, not the conclusion.

- **Intellectual Integrity Over Narrative**: The 25x figure made for better storytelling than 10x, but the facts are what they are. The correction is a minor hit to the article's punch but not to its substance.

## Transcript Summary

### The Gemini Flag
User received feedback from Gemini (used for cross-model review) indicating that the API pricing used in the economics article appeared incorrect. The specific claim: Opus 4.5 costs $15 input / $75 output per million tokens was flagged as potentially wrong.

### Verifying Current Pricing
Fetched current Anthropic API pricing documentation. Confirmed the actual rates:
- Claude Opus 4 (claude-opus-4-20250514): $15 input / $75 output
- Claude Sonnet 4.5 (claude-sonnet-4-5-20250514): $3 input / $15 output
- Claude Opus 4.5 (claude-opus-4-5-20251101): $5 input / $25 output

The article had mistakenly applied Opus 4 pricing ($15/$75) to Opus 4.5, which actually costs $5/$25.

### Recalculating the Economics
With correct pricing:
- Original estimate: ~$5,000 in API costs for the month
- Corrected estimate: ~$2,000 in API costs for the month
- Original value multiplier: 25x ($5,000 value for $200 subscription)
- Corrected value multiplier: ~10x ($2,000 value for $200 subscription)

### Core Thesis Still Holds
Even at 10x value, the subscription remains heavily subsidized. A $200/month subscription providing $2,000 in API equivalent value is still remarkable. The story is less dramatic but the conclusion is unchanged: Anthropic is betting on inference costs dropping, or absorbing losses to build market share, or both.

## Full Transcript

### Initial Prompt
**T. Brian Jones:** Gemini just told me the pricing in my Claude Code economics article is wrong. It says I used incorrect API rates.

---

### Q1: The Specific Claim
**Claude:** What specifically did Gemini flag?

**T. Brian Jones:** It said the $15/$75 per million tokens for Opus 4.5 isn't right. That's what I based all the math on.

---

### Q2: Verifying the Rates
**Claude:** Let me fetch the current Anthropic pricing. [Verified via API documentation that Opus 4.5 (claude-opus-4-5-20251101) is priced at $5 input / $25 output per million tokens, while Opus 4 (claude-opus-4-20250514) is $15 input / $75 output.]

**T. Brian Jones:** So I was using the old Opus pricing for the new model. That's a 3x error on both input and output.

---

### Q3: Impact on the Math
**Claude:** The corrected calculation brings the API equivalent cost from approximately $5,000 to approximately $2,000.

**T. Brian Jones:** So the value multiplier drops from 25x to about 10x. That's still a lot, but it's not the same story.

---

### Q4: Does the Conclusion Change?
**Claude:** The core conclusion; that Anthropic is subsidizing Claude Code subscriptions significantly; remains valid. 10x value is still substantial.

**T. Brian Jones:** Right. It's just less dramatic. The article loses some punch but not its point. The subscription is still heavily subsidized, just not as heavily as I claimed.

---

### Q5: Next Steps
**T. Brian Jones:** I need to update the article with the correct numbers. And probably add a note about the correction.

**Claude:** A correction note at the top of the article would be appropriate. Readers who saw the original version should know the math has been revised.
