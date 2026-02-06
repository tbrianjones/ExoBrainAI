# Conversation: The Future of Personal Knowledge Systems

**Person:** T. Brian Jones
**AI:** Claude
**Date:** 2026-02-06

---

**Brian:** I've been thinking about how personal knowledge systems fail. They all start with this promise of "capture everything" but then you end up with a graveyard of notes you never revisit. The problem isn't capture; it's retrieval and resurfacing.

---

**Claude:** That's a pattern I see across tools like Evernote, Notion, Roam. The initial enthusiasm of capturing creates a write-heavy system with no read incentive. What would a read-incentivized system look like to you?

---

**Brian:** Exactly. So what if the system itself had opinions about what you should be looking at? Not in an algorithmic feed way, but more like a librarian who knows your interests. The projection layer in ExoBrain is my attempt at this; it surfaces the "hot" objects, the ones you've been touching recently, and puts them where you'll see them.

---

**Claude:** The librarian metaphor is compelling. A librarian doesn't just retrieve what you ask for; they make recommendations based on what they've seen you reading. How do you think about the scoring mechanism? Pure recency, or something richer?

---

**Brian:** Right now it's recency-weighted, which is a starting point. But I want to layer in access frequency, link density (objects that connect to many others are probably more important), and eventually semantic similarity. If I'm working on topic X, surface things related to X even if I haven't touched them in months.

---

**Claude:** That's essentially a personal PageRank. The link density signal is particularly interesting because it emerges from your own curation behavior rather than being imposed externally. Each link you create is a vote of relatedness.

---

**Brian:** Yes! And the beautiful thing is that it compounds. The more you use the system, the smarter the resurfacing becomes. Early on it's mostly recency, but as your knowledge graph densifies, the structural signals dominate. It shifts from "what did I just touch" to "what matters in the context of what I'm doing now."

---

**Claude:** How do you think about the cold start problem? A new user with five objects doesn't have enough signal for meaningful scoring.

---

**Brian:** That's where the projection layer's simplicity helps. With five objects, just show all five. The hot tier limit of 200 means you don't need scoring until you have more than 200 objects. Below that threshold, everything is projected. The complexity scales with the data, not with the user's first experience.
