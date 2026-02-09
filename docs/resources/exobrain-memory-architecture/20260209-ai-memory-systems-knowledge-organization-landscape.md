# AI Memory Systems & Knowledge Organization Landscape

**Date:** 2026-02-09
**Context:** Research conducted during creation of ADR-011 (Primitive Semantics and Knowledge Gardening). Addresses the question of how bleeding-edge AI memory systems handle knowledge organization, taxonomy emergence, and the "where does something belong?" problem.

**Related ADRs:**
- ADR-006: Information-Centric Computing Vision
- ADR-007: Projection Layer Architecture
- ADR-011: Primitive Semantics and Knowledge Gardening

---

## The Core Question

After migrating content from the file-based `ideas/` folder into ExoBrain, a philosophical tension surfaced: should ExoBrain (the project) live in `ideas/` or `projects/`? Should ideation happen inside projects, or separately? Who decides where things go; humans or AI? These questions led to a survey of how the field is handling knowledge organization in 2025-2026.

---

## 1. Personal Knowledge Management with AI Agents

### Mem: The "Self-Organizing Workspace"

Mem brands itself as "the world's first self-organizing workspace." Core thesis: eliminate folders entirely. Users capture thoughts without considering structure; AI handles organization through "Collections" that automatically categorize and connect knowledge based on content and context. As users add notes, Mem analyzes content and suggests relevant Collections with no manual filing. "Heads Up" automatically finds related notes, groups them by topic, and shows related meetings on a timeline.

Mem 2.0 (October 2025) added Voice Mode, which turns unstructured brain dumps into structured, organized notes automatically.

**Where things belong**: "Don't decide; let the AI decide for you." The human's job is capture; classification is delegated.

Sources:
- [Mem: Building the World's First Self-Organizing Workspace](https://get.mem.ai/blog/building-the-worlds-first-self-organizing-workspace)
- [Organize Your Notes with AI using Collections](https://get.mem.ai/blog/organize-your-notes-with-ai-using-collections)

### Tana: Emergent Structure via Supertags and Knowledge Graphs

Tana ($25M raised, February 2025) makes structure lightweight and emergent through "Supertags" that classify notes without requiring decisions about hierarchy. The workspace is a knowledge graph: take notes anywhere, add supertags, and "the information will flow to where it's needed." Structure emerges naturally; no schema design upfront, no choosing between notes and databases.

AI command nodes automatically classify content, extract fields (e.g., "Key Findings," "Limitations" from a paper), and generate structure from unstructured input.

**Where things belong**: "Things don't belong in places; they belong to types (supertags), and views/queries surface them by context."

Sources:
- [Tana AI-native workspace](https://tana.inc/)
- [Tana Knowledge Graph](https://tana.inc/knowledge-graph)
- [TechCrunch: Tana snaps up $25M](https://techcrunch.com/2025/02/03/tana-snaps-up-25m-with-its-ai-powered-knowledge-graph-for-work-racking-up-a-160k-waitlist/)

### Notion 3.0: AI Agents Within Structured Workspaces

Notion 3.0 (2025) introduced autonomous AI Agents that execute work within Notion's existing structured workspace. Rather than eliminating structure, Notion adds intelligence to navigate it; multi-model AI with deep personalization and cross-platform context. Philosophy: keep the human-designed structure but make AI smart enough to work within it.

Source: [Notion AI Review 2026](https://max-productive.ai/ai-tools/notion-ai/)

### Obsidian + Smart Connections: Embedding-Based Discovery

Smart Connections (786K+ downloads, January 2026) adds AI-powered semantic linking on top of Obsidian's user-controlled, local-first vault. Computes embeddings across all notes and surfaces related content as you write, without reorganizing anything. User maintains full control over structure; AI provides discovery.

**Where things belong**: "Wherever the user puts them." AI finds connections the user missed; it doesn't move things around.

Sources:
- [Smart Connections App](https://smartconnections.app)
- [Obsidian Smart Connections GitHub](https://github.com/brianpetro/obsidian-smart-connections)

### Limitless (formerly Rewind AI): Ambient Capture

Limitless represented "capture everything, organize later"; a wearable pendant that records conversations and transforms audio into structured summaries, to-do lists, and searchable lifelogs. Meta acquired Limitless in December 2025 and shut down the desktop Rewind app. Organization was a post-processing step on ambient capture, not a human decision at capture time.

Sources:
- [Limitless AI](https://rewind.ai/)
- [Meta acquires Limitless; TechCrunch](https://techcrunch.com/2025/12/05/meta-acquires-ai-device-startup-limitless/)

---

## 2. LLM Memory Architectures

### Four Design Paradigms (Serokell, December 2025)

A comprehensive analysis identified four core patterns for long-term LLM memory:

**Pattern 1: OS-Inspired Hierarchy (MemGPT/Letta)**
Primary Context (RAM; fixed-size prompt) and External Context (disk; Recall Storage for searchable logs, Archival Storage for vector-based semantic search). Agent self-manages paging between tiers. Tradeoff: agent consumes cognitive bandwidth managing its own memory.

**Pattern 2: Global Personalization (ChatGPT)**
Four layers: session metadata, explicit long-term facts (persistent "profile"), AI-generated conversation summaries, and current session context. OpenAI skips retrieval; they pre-compute summaries and inject everything with every message. Avoids search latency but creates context leakage risk.

**Pattern 3: Compartmentalized Control (Claude)**
Project-scoped memory with hard boundaries. CLAUDE.md files provide versioned, Git-managed context. Memory grows only as fast as users curate it. Tradeoff: predictability and transparency vs. scalability.

**Pattern 4: Composable Primitives (LangChain, Autogen)**
Buffer memory, summary memory, entity memory, and knowledge-graph memory. Developer designs write-back cycles. Industry moving "from mere similarity search toward relational reasoning" via knowledge graphs.

**Key observation**: The field is migrating from unstructured vector snippets toward knowledge graph usage. Graphs handle relational queries that flat vector stores cannot.

Source: [Design Patterns for Long-Term Memory in LLM-Powered Architectures](https://serokell.io/blog/design-patterns-for-long-term-memory-in-llm-powered-architectures)

### Letta (MemGPT): Self-Editing Memory Blocks

Letta's most significant 2025-2026 development is **Memory Blocks**: agents learn how to use memory autonomously through descriptive labels. An agent might start with basic blocks ("persona," "human") but evolve to create specialized sections. The agent self-restructures its memory as it learns. The "memory omni-tool" (September 2025) lets agents dynamically manage their own blocks.

**Critical benchmark result**: **Letta Filesystem** (July 2025) achieved 74.0% on the LoCoMo benchmark by simply storing conversational histories as files, beating specialized memory libraries. This suggests that with well-designed agents, even simple filesystem tools outperform complex retrieval pipelines.

**Why this matters for ExoBrain**: This directly validates the projection layer architecture (ADR-007). SQLite as truth, markdown files as the AI-readable surface, well-designed agents operating on those files. The "simple" approach works better than the "sophisticated" one.

Letta also introduced the Agent File (.af) format (April 2025) for serializing stateful agents with persistent memory, and the Conversations API (January 2026) for shared memory across parallel user experiences.

Sources:
- [Letta Memory Blocks](https://www.letta.com/blog/memory-blocks)
- [Benchmarking AI Agent Memory: Is a Filesystem All You Need?](https://www.letta.com/blog/benchmarking-ai-agent-memory)
- [Letta Memory Omni-Tool](https://www.letta.com/blog/introducing-sonnet-4-5-and-the-memory-omni-tool-in-letta)

### LangMem: Hierarchical Namespaces + Three Memory Types

LangMem (LangChain's memory SDK, May 2025) uses **hierarchical namespaces** to organize memory. Memories grouped by organization, user, application, or any arbitrary hierarchy with template variables; e.g., `("acme_corp", "{user_id}", "code_assistant")`.

Three memory types:
- **Semantic memory**: Facts and knowledge stored in profiles or collections
- **Episodic memory**: Full context of past interactions as learning examples
- **Procedural memory**: Behavioral rules encoded as system instructions, refined through prompt optimization

Two storage patterns: **Profiles** for well-scoped, schema-based data and **Collections** for unbounded knowledge requiring search-time reconciliation.

**Why this matters for ExoBrain**: LangMem's hierarchical namespaces are the closest external analog to ExoBrain's space hierarchy. The dual storage pattern (profiles vs. collections) maps to ExoBrain's object types vs. free-text content.

Sources:
- [LangMem Conceptual Guide](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/)
- [LangMem SDK Launch](https://blog.langchain.com/langmem-sdk-launch/)

### Mem0: The Memory Orchestration Layer

Mem0 ($24M raised, 2025) positions itself as a memory layer between AI agents and storage:

- **Base Mem0**: Extracts and manages salient information using priority scoring and contextual tagging
- **Mem0g (Graph-based)**: Directed labeled graphs with entities as nodes and relationships as edges

Key insight: intelligent filtering to avoid "memory bloat." The most successful agents use a hybrid architecture combining vector search with graph traversal. Achieved 26% improvement over OpenAI's memory, 91% lower p95 latency, 90%+ token cost savings.

Sources:
- [Mem0 Research Paper (arxiv:2504.19413)](https://arxiv.org/abs/2504.19413)
- [Mem0 Research](https://mem0.ai/research)
- [Mem0 GitHub](https://github.com/mem0ai/mem0)

---

## 3. Knowledge Gardening and Curation by AI

### A-MEM: Zettelkasten-Inspired Agentic Memory (NeurIPS 2025)

The most directly relevant system for AI-driven knowledge gardening. Implements Zettelkasten principles where each memory is an "atomic note" containing:

1. Original content and timestamp
2. LLM-generated keywords
3. LLM-generated tags
4. Contextual description (semantic understanding beyond raw data)
5. Dense embedding
6. Link set (connections to related memories)

**The gardening mechanism**: When new memories integrate, two operations trigger: (a) link generation between new and historical memories via embedding similarity + LLM reasoning, and (b) **memory evolution**, where existing memories' contextual descriptions and attributes update based on new information. The knowledge base is continuously refined; old memories literally change their representations as new information arrives, enabling "higher-order patterns" to emerge.

**Why this matters for ExoBrain**: This is the academic validation of the knowledge gardening vision in ADR-011. ExoBrain doesn't do memory evolution today; objects are static once created. A future gardening agent could enrich existing objects based on new context, updating summaries, adding tags, and strengthening links as the knowledge base grows. This would be a significant architectural decision worth its own ADR.

Sources:
- [A-MEM Paper (arxiv:2502.12110)](https://arxiv.org/abs/2502.12110)
- [A-MEM GitHub](https://github.com/agiresearch/A-mem)
- [NeurIPS 2025 Poster](https://neurips.cc/virtual/2025/poster/119020)

### EverMemOS: Self-Organizing Memory OS (January 2026)

Introduces an "engram-inspired lifecycle" with three phases:

1. **Episodic Trace Formation**: Dialogue streams converted into **MemCells** (individual observations/facts) linked chronologically
2. **Semantic Consolidation**: MemCells autonomously organized into thematic **MemScenes** through emergent clustering; groupings discovered dynamically based on content relationships, not predetermined categories
3. **Reconstructive Recollection**: MemScene-guided agentic retrieval

Structure emerges from the data itself. The system progressively refines how memories relate, consolidating related information without human-defined hierarchies.

Achieved 93.05% accuracy on LoCoMo, with dominance in multi-hop reasoning (+19.7%) and temporal tasks (+16.1%).

Sources:
- [EverMemOS Paper (arxiv:2601.02163)](https://arxiv.org/abs/2601.02163)
- [EverMind Launch Announcement](https://www.prnewswire.com/news-releases/end-agentic-amnesia-evermind-launches-a-memory-platform-and-an-80-000-global-competition-as-evermemos-sets-new-sota-results-across-multiple-benchmarks-302678025.html)

### MIRIX: Six-Memory Multi-Agent System (July 2025)

The maximalist approach: six memory types each managed by a dedicated Memory Manager agent, plus a Meta Memory Manager for routing:

- **Core Memory**: Persistent agent/user profiles
- **Episodic Memory**: Time-stamped events and interactions
- **Semantic Memory**: Abstract knowledge independent of time
- **Procedural Memory**: Learned user habits
- **Resource Memory**: References to external documents, images, audio
- **Knowledge Vault**: Sensitive verbatim information

Each Memory Manager decides independently what to store, how to index, when to update. The clearest example of delegating "where does it belong?" to specialized AI agents.

Sources:
- [MIRIX Paper (arxiv:2507.07957)](https://arxiv.org/abs/2507.07957)
- [MIRIX GitHub](https://github.com/Mirix-AI/MIRIX)

### MAGMA: Multi-Graph Agentic Memory (January 2026)

Maintains and updates external memory using multiple graph structures, enabling agents to accumulate knowledge, preserve identity, and remain coherent across sessions. Achieved highest overall judge score (0.7), outperforming MemoryOS (0.553).

Source: [MAGMA Paper](https://arxiv.org/html/2601.03236v1)

### The Autonomy Spectrum

No production system handles the full loop of AI reorganization with human approval gates. The field splits cleanly:

| System | AI Autonomy | Human Role |
|--------|-------------|------------|
| Obsidian + Smart Connections | Lowest; AI suggests, human decides | Full control over structure |
| Claude (CLAUDE.md) | Low; human curates, AI reads | Explicit curation, project-scoped |
| Notion 3.0 | Medium; AI agents within human structure | Defines workspace, AI navigates |
| Mem | High; AI organizes, human captures | Capture only; trust AI classification |
| A-MEM | High; AI creates links and evolves memories | No human role in organization |
| EverMemOS | Highest; fully self-organizing | No human role; structure emerges |

**The gap**: Nobody has built the middle path where AI proposes and humans confirm when uncertain, with obvious decisions happening autonomously. This is what ExoBrain's knowledge gardening model (ADR-011) describes.

---

## 4. The "Projects vs Ideas" Problem

### PARA Method: Actionability as Organizing Principle

Tiago Forte's PARA (Projects, Areas, Resources, Archive) sorts by actionability. Projects are most actionable (finite, with deadlines), Areas are ongoing responsibilities, Resources are topics of interest, Archive is inactive. Ideas live in Resources until they become actionable enough to be a Project.

Critical insight: PARA is a project management system with a filing system. It is not designed for ideation or knowledge building.

### Zettelkasten: Ideas as First-Class Citizens

Zettelkasten treats ideas as the primary unit: "You don't necessarily have to think to which project a note belongs. Because this is the essence of this way of taking notes. You don't know what will emerge." Ideas exist independently and form connections over time; projects emerge from the idea network, not the other way around.

### The Emerging Consensus: Hub and Spoke

The most cited 2025 synthesis proposes PARA as the "Hub of Action" and Zettelkasten as the "Spoke of Insight"; functionally connected without being structurally conflated.

- PARA manages actionable work (projects with deadlines, areas of responsibility)
- Zettelkasten manages knowledge and ideation (atomic notes, emergent connections)
- They reference each other but live in separate structures

**How this maps to ExoBrain**: The `ideas/` space hierarchy is the Zettelkasten spoke. `projects/` (when it emerges) would be the PARA hub. Ideation does not live inside projects; ideation feeds projects but is not contained by them.

### Johnny Decimal: Wrong Abstraction for Ideas

Johnny Decimal (max 10 areas, 10 categories each) is designed for managing projects and files, not knowledge. Complementary for file organization but not applicable to the ideas-vs-projects question.

Sources:
- [Zettelkasten + PARA Combined](https://zettelkasten.de/posts/building-a-second-brain-and-zettelkasten/)
- [PARA and Zettelkasten Combined; Digital Garden](https://digital-garden.ontheagilepath.net/para-and-zettelkasten-combined)
- [PARA Method vs. Zettelkasten](https://mattgiaro.com/para-method-and-zettelkasten/)

---

## 5. Emergent vs Prescribed Taxonomy

### Research Systems That Let Categories Emerge

**EverMemOS** (January 2026): Semantic Consolidation phase discovers thematic groupings from content rather than applying predetermined categories.

**A-MEM** (NeurIPS 2025): Tags and keywords generated per-memory via LLM. Links emerge from embedding similarity + LLM reasoning, not from a prescribed ontology.

**Tana** (production, 2025): "Structure emerges naturally; no designing schemas upfront." Supertags created on the fly; queries surface content by context rather than location.

### Enterprise Knowledge Intelligence

The Knowledge Intelligence framework (Enterprise Knowledge, 2025): AI identifies emerging patterns and uncovers semantic relationships, but human taxonomists remain essential. "Using ChatGPT/LLM technologies can help with various sub-tasks of creating taxonomies but not for a taxonomy as a whole."

Most honest assessment of the state of the art: AI generates candidate taxonomies and discovers clusters, but production-quality taxonomy still requires human judgment for coherence.

### The Bottom-Up Taxonomy Pipeline

From EMNLP 2025 work on occupation taxonomies:
1. Semantic clustering of content (bottom-up)
2. Multi-agent collaboration to label clusters
3. Human review and refinement

A hybrid where categories emerge from content, are refined by AI, and are validated by humans.

Sources:
- [Enterprise Knowledge: Enhancing Taxonomy Management](https://enterprise-knowledge.com/enhancing-taxonomy-management-through-knowledge-intelligence/)
- [Knowledge Base Taxonomy Best Practices 2026](https://www.matrixflows.com/blog/knowledge-base-taxonomy-best-practices)

---

## 6. Synthesis: Implications for ExoBrain

### The Field is Converging on Hybrid Memory

Vector embeddings for retrieval + structured relationships (graphs, links, tags) for organization. Pure flat retrieval is losing ground to systems that maintain explicit relationships. ExoBrain's type+space+tag+link model is well-positioned.

### Self-Editing Memory is the Frontier

A-MEM's "memory evolution" and Letta's self-restructuring memory blocks represent the most interesting pattern: the knowledge base as a living system. ExoBrain objects are currently static once created. A future gardening agent that enriches existing objects would move ExoBrain into this frontier.

### The "Where Does It Belong?" Question is Being Dissolved

Systems like Mem, Tana, and A-MEM move toward "things don't belong in places; they belong to types and relationships, and views surface them by context." But spaces still earn their existence for three reasons:

1. **Projection geography.** The Letta benchmark proved filesystem-based approaches work. Projection needs a directory tree; spaces provide it.
2. **Command scoping.** When `/ideate` works within `ideas/memory-palace`, that scope is load-bearing. Tags can't provide that boundary because they're many-to-many.
3. **Future access control.** Spaces as permission boundaries.

Spaces should not carry semantic meaning. "This is in `ideas/`" says something about the *workflow* that created it and the *context* in which it's useful, not what it's *about*.

### Ideation and Projects Are Structurally Separate

The Zettelkasten/PARA synthesis is clear: ideas are a network that feeds projects, not a subset of projects. ExoBrain's `ideas/` as a separate-but-linked structure is consistent with this consensus.

### Nobody Has Built the Middle Path

The field splits between "AI does everything" (research systems) and "human maintains control" (production tools). ExoBrain's knowledge gardening model; AI proposes, human confirms when uncertain, obvious decisions happen autonomously; is genuinely novel in production systems. This is the gap to fill.

### The Repo-ExoBrain Bridge is the Next Architecture Question

The `docs/` folder (ADRs, active plans, archived plans) is a proto-project space that should eventually live in ExoBrain. The architecture for "a repo has a view into ExoBrain" doesn't exist yet. Options include symlinks, projection target overrides, or Git integration. This warrants its own ADR when the time comes.

---

## Additional Reading

- [Mem0 GitHub](https://github.com/mem0ai/mem0)
- [Agent Memory Paper List (survey)](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)
- [Letta Agent File (.af) Format](https://www.letta.com/blog/agent-file)
- [LangMem SDK](https://blog.langchain.com/langmem-sdk-launch/)
- [The End of Forgetting: Limitless, Rewind, and the Rise of Personal Knowledge AI](https://asktodo.ai/blog/ai-memory-assistants-limitless-rewind-trends-2025)
