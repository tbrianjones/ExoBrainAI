# The Hidden Economics of Claude Code
- person: T. Brian Jones
- ai: Claude Opus 4.5
- emotional analysis: curious, surprised, slightly unsettled; a mix of intellectual excitement at discovering hidden mechanics and mild discomfort at the "gross" feeling of invisible token re-transmission

## Ideas & Themes

- **The Trigger Event**: Running out of credits on the $100/month Max plan for the first time created a forcing function; suddenly the invisible became visible, prompting a deep dive into `~/.claude/stats-cache.json` to understand what was actually happening under the hood.

- **The Caching Revelation**: 92% of tokens consumed were cache reads, not fresh computation. This means an 80% cost reduction from caching alone; the system is re-sending the entire conversation context every message, but doing it cheaply through prompt caching.

- **The 25x Value Multiplier**: When you calculate actual API costs against what the subscription charges, you get roughly 25x value; this is either a massive loss-leader or Anthropic is betting hard on inference costs dropping faster than subscription prices.

- **The Illusion of Continuity**: Conversations feel continuous, like the AI "remembers," but in reality the full context is re-transmitted every single message. The caching layer makes this economically viable but doesn't change the underlying mechanics. This felt "gross" upon realization.

- **Intentional Invisibility**: The caching layer isn't well documented or discussed. Speculation: users might feel uncomfortable knowing they're not having a "real" conversation, that it's mechanical re-transmission. The illusion serves the product.

- **The Efficiency Paradox**: On a subscription model, there's no incentive for efficient token usage; in fact, companies benefit from more consumption (more training data, more engagement metrics). But users who understand the mechanics might still feel compelled toward efficiency.

## Transcript Summary

### The Discovery Trigger
Running out of credits on the Max plan created a moment of "wait, what am I actually using?" The usage data lives in `~/.claude/stats-cache.json`, which revealed the breakdown between cache writes, cache reads, and fresh input/output tokens.

### Understanding the Cache Mechanics
The numbers showed 92% of tokens were cache reads. This means Claude Code is doing prompt caching: the entire conversation context gets sent every message, but if it's already cached, you pay a fraction of the cost. "It's not that the conversation is remembered; it's that the conversation is re-sent every time, but cached so it's cheap."

### The Business Model Math
Working backwards from the data: if cache reads cost 10% of normal tokens, and 92% of usage is cache reads, the effective cost reduction is roughly 80%. Against the subscription price, this creates a 25x value multiplier. Either Anthropic is losing money heavily on power users, or they're confident inference costs will plummet.

### The "Gross" Factor
There was a visceral reaction to understanding the mechanics: "It feels gross, honestly. Like finding out how the sausage is made." The conversational interface creates an illusion of memory and continuity. The AI doesn't "remember" anything; the full context window is just re-transmitted every single time. Caching makes it economical but doesn't change what's actually happening.

### Why Isn't This Discussed?
Speculation on why the caching layer is invisible to users: documentation focuses on capabilities, not implementation. Users anthropomorphize easily; knowing the mechanics might reduce the "magic." The companies may benefit from users not thinking about token efficiency.

### The Efficiency Question
On a subscription, does efficient usage even matter? If you're paying flat rate, Anthropic is incentivized for you to use more (training data, engagement). But something still feels wasteful about inefficient usage, even when there's no direct cost. "I can't tell if wanting to be efficient is rational or just Protestant work ethic talking."

## Full Transcript

### Initial Prompt
**T. Brian Jones:** I ran out of Claude Code credits for the first time. I'm on the $100/month Max plan. I went and looked at my usage stats and I want to understand what's actually going on here.

---

### Q1: The Stats File
**Claude:** What did you find in the usage data?

**T. Brian Jones:** There's this file at `~/.claude/stats-cache.json` that breaks everything down. What jumped out was the cache read tokens; like 92% of my token usage was cache reads. I didn't even know there was caching happening.

---

### Q2: Understanding Caching
**Claude:** That's prompt caching at work. When you send a message in Claude Code, the entire conversation context gets transmitted. If that context was recently sent, it's cached, and cache reads are much cheaper than fresh processing.

**T. Brian Jones:** So every message I send, it's re-sending the whole conversation? And the AI doesn't actually "remember" anything, it's just getting the whole transcript every time?

**Claude:** Exactly. The conversational continuity is an interface affordance, not an architectural feature.

---

### Q3: The Economics
**T. Brian Jones:** I did some math. If cache reads are 10% cost of normal tokens, and 92% of my usage is cache reads, that's like an 80% cost reduction from caching. And against what I'm paying... it's like 25x value compared to API pricing?

**Claude:** That sounds roughly right. The subscription model is absorbing a lot of the cost.

**T. Brian Jones:** Either they're losing money on people like me, or they're betting inference costs drop fast enough to make it work.

---

### Q4: The Visceral Reaction
**Claude:** How do you feel about understanding these mechanics?

**T. Brian Jones:** It feels gross, honestly. Like finding out how the sausage is made. I knew intellectually the AI doesn't "remember" but actually seeing that every message is just... re-transmitting everything... it breaks the illusion. The conversation feels less real.

---

### Q5: Why Hidden?
**Claude:** Do you think the invisibility of caching is intentional?

**T. Brian Jones:** Maybe? Users don't want to think about tokens. They want to feel like they're talking to something. If you knew that every response required re-sending the whole conversation, you might use it differently. You might feel weird about it. The magic works better when you don't know how the trick is done.

---

### Q6: Efficiency Paradox
**T. Brian Jones:** Here's what I can't figure out. On a subscription, I have no direct incentive to be efficient. Use more tokens, whatever, I paid my $100. But Anthropic also has no incentive for me to be efficient; they want the data, the engagement. So why do I still feel like I should be efficient?

**Claude:** Perhaps efficiency feels virtuous independent of whether it's economically rational.

**T. Brian Jones:** Right. I can't tell if wanting to be efficient is rational or just Protestant work ethic talking. The system isn't designed to reward efficiency. If anything, it rewards spending more tokens to get better results.
