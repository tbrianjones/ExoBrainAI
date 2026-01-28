# Research Report: AI-Powered Content Creation Landscape

> **Note**: This transcript references "Claude Writer," which was the original working name for this project. It has since been renamed to **ExoBrain**.

- researcher: Claude Opus 4.5
- date: 2026-01-10
- purpose: Survey open source projects and patterns for agent-driven content production systems
- relevance: Direct application to Claude Writer's vision of interview-driven, agent-managed content creation

---

## Executive Summary

This report surveys the current landscape of open source AI-powered content creation systems, with particular focus on multi-agent architectures, publishing pipelines, and patterns that could inform the evolution of Claude Writer. The research reveals a maturing ecosystem with several production-ready tools and emerging patterns worth adopting.

Key findings:
- Multi-agent role specialization (researcher, writer, editor) consistently improves output quality
- Git-based content management is becoming the standard for serious content workflows
- The gap between AI generation and automated publishing is rapidly closing
- Slot-based/placeholder patterns enable sophisticated multi-agent coordination
- Interpretable memory (natural language state) enables human oversight without sacrificing automation

---

## Part I: AI Content Creation Systems

### 1. STORM (Stanford Knowledge Curation System)

**Repository**: github.com/stanford-oval/storm
**Stars**: 27,800+
**Focus**: Research synthesis and comprehensive article generation

STORM represents the academic gold standard for AI-driven article generation. Developed at Stanford, it generates Wikipedia-style articles through a sophisticated two-stage pipeline.

**Architecture**:
- Pre-writing stage: Internet research to gather sources; creates structured outlines
- Writing stage: Generates cited articles using collected references
- Uses perspective-guided questioning: simulates conversations between experts with different viewpoints
- Co-STORM variant enables human-AI collaborative workflows

**Key Innovation**: Multi-perspective analysis. Before writing, STORM identifies similar existing articles and extracts the perspectives represented. It then generates questions from each perspective, ensuring comprehensive coverage.

**Relevance to Claude Writer**: The perspective-based questioning maps directly to Claude Writer's interview model. Instead of expecting users to know what to say, the system asks targeted questions from multiple angles. STORM's approach to research synthesis could inform how we handle source material in the `doc_load/` folder.

---

### 2. NovelGenerator

**Repository**: github.com/KazKozDev/NovelGenerator
**Focus**: Long-form fiction with narrative coherence

NovelGenerator tackles the hardest problem in AI writing: maintaining coherence across book-length content.

**Three-Agent Model**:
1. **Structure Agent**: Establishes narrative frameworks with explicit content slots
2. **Character Agent**: Populates dialogue and emotional content
3. **Scene Agent**: Adds atmospheric details and sensory descriptions

**Slot-Based Methodology**: The system uses placeholder markers like `[DIALOGUE_SLOT]`, `[ACTION_SLOT]`, `[EMOTION_SLOT]`. Each agent knows exactly what type of content to generate and where.

**Technical Implementation**:
- 6+ coordinated phases per chapter for quality assurance
- Persistent story context tracking across all chapters
- Multi-stage auto-save checkpoints
- Real-time streaming output
- Export to EPUB, PDF, Markdown

**Relevance to Claude Writer**: The slot-based pattern is powerful. Claude Writer's layered writing stack (topic → outline → chapters → paragraphs → sentences) could benefit from explicit slot markers that tell agents what to generate at each level. The persistent story context maps to Claude Writer's assets folder; both systems need to maintain character/setting/concept consistency across long works.

---

### 3. Dify

**Repository**: github.com/langgenius/dify
**Stars**: 125,000+
**Contributors**: 1,100+
**Focus**: Production-ready agentic workflow development

Dify has emerged as the de facto standard for enterprise AI workflow management. It's not content-specific but provides the infrastructure for content pipelines.

**Capabilities**:
- Visual drag-and-drop workflow builder
- 50+ pre-built agent tools (search, image generation, computation)
- Modular integration with hundreds of LLM providers
- Extensive RAG capabilities with document processing
- Real-time observability and LLMOps monitoring

**Production Scale**: 180,000+ developers, 59,000+ end users

**Relevance to Claude Writer**: Dify demonstrates what production-scale content workflows look like. Claude Writer operates at the command line; Dify provides a visual interface. The eventual "Google Docs but for agents" interface described in the system vision would benefit from studying Dify's approach to workflow visualization and agent orchestration.

---

### 4. AntV Infographic

**Repository**: github.com/antvis/Infographic
**Stars**: 3,600+
**Focus**: AI-optimized infographic generation

AntV Infographic bridges AI generation and visual design through a declarative syntax specifically designed for LLM output.

**Technical Approach**:
- Fault-tolerant configuration language that handles LLM formatting quirks
- ~200 built-in templates and data-item components
- Streaming rendering for real-time progressive updates
- SVG output for quality and editability
- Theme system for visual consistency

**Key Innovation**: The syntax is designed to be AI-friendly. Unlike traditional design tools, AntV expects imperfect input and handles edge cases gracefully.

**Relevance to Claude Writer**: The `/generate-academic-infographic-view` command could adopt AntV's declarative approach. Rather than generating raw visuals, Claude Writer could output AntV-compatible specifications that render reliably. The fault-tolerant design philosophy applies broadly; content generation systems should expect and handle LLM inconsistencies.

---

### 5. CrewAI Framework

**Repository**: github.com/crewAIInc/crewAI
**Focus**: Multi-agent collaboration infrastructure

CrewAI has become the industry standard framework for building agent teams. Many content creation examples use it as infrastructure.

**Architecture**:
- Agent-based task orchestration with role definitions
- Task sequencing and handoff mechanisms
- Tool integration for agents
- Real-time collaborative workflows

**Content Workflow Pattern** (from CrewAI examples):
1. Research Specialist (web search and analysis)
2. Content Strategist (outline and strategy)
3. Content Writer (prose generation)
4. Content Editor (refinement)
5. QA Specialist (accuracy verification)
6. SEO Expert (search optimization)
7. Executive Summarizer (brief creation)

**Relevance to Claude Writer**: CrewAI's role-based pattern validates Claude Writer's vision of "journalist agent, Ezra Klein agent, personal voice agent." The difference is that Claude Writer aims to be conversation-driven rather than workflow-driven. Users talk; agents listen and produce. But the underlying role specialization is the same.

---

### 6. RecurrentGPT

**Repository**: github.com/aiwaves-cn/RecurrentGPT
**Focus**: Interactive long-form text with interpretable state

RecurrentGPT solves the context window problem for long-form content through a clever mechanism: natural language memory.

**Architecture**:
- Simulates LSTM recurrence using language-based memory
- At each timestep: generates a paragraph and updates long/short-term memory
- Memory stored as natural language on disk (not embeddings)
- Users can observe and edit the natural language memories directly

**Key Innovation**: Interpretable memory. Unlike vector databases where state is opaque, RecurrentGPT stores memory as readable text files. You can see exactly what the system "remembers" and edit it.

**Relevance to Claude Writer**: This directly validates the "filesystem as database" approach. RecurrentGPT stores memory in files; Claude Writer stores everything in markdown tracked by git. Both systems prioritize human-readable, human-editable state over efficiency. The difference is that Claude Writer goes further; not just memory but the entire content hierarchy lives in the filesystem.

---

### 7. LLM-Powered Multi-Agent Blog Generator

**Repository**: github.com/chanupadeshan/LLM-Powered-Multi-Agent-Blog-Generator
**Focus**: Collaborative blog post generation with CrewAI

A practical implementation of the seven-agent content workflow pattern.

**Agent Roles**:
1. Research Specialist: Web search and source analysis
2. Content Strategist: Outline and strategic planning
3. Content Writer: Prose generation
4. Content Editor: Refinement and polish
5. QA Specialist: Accuracy verification
6. SEO Expert: Search optimization
7. Executive Summarizer: Brief creation

**Technical Stack**: Python, Flask, OpenAI GPT-3.5 Turbo, Serper API, CrewAI

**Implementation Details**:
- Web-based UI with real-time progress tracking
- Modular agent definitions and task separation
- Search integration for research
- Editorial review before publication

**Relevance to Claude Writer**: This is the closest existing implementation to Claude Writer's vision. The key difference: this system runs autonomously after initial input. Claude Writer emphasizes continuous conversation; the user talks throughout the process, not just at the beginning.

---

### 8. LLM-Book-Generator

**Repository**: github.com/fangfufu/LLM-book-generator
**Focus**: End-to-end automated book generation

A practical pipeline from concept to formatted manuscript.

**Pipeline Stages**:
1. Concept development
2. Chapter planning
3. Content generation
4. Formatting and assembly
5. Export (DOCX, EPUB, PDF)

**Technical Features**:
- Flexible deployment (Google Gemini API or local Ollama)
- YAML-based configuration for book parameters
- Mathematical rendering for technical books (LaTeX to image)
- Response caching to accelerate iterations

**Relevance to Claude Writer**: The caching approach is noteworthy. Long-form content generation is expensive; caching intermediate results enables iteration without regenerating everything. Claude Writer's git-based approach naturally provides this; every commit is a cache point you can return to.

---

### 9. Microsoft LIDA

**Repository**: github.com/microsoft/lida
**Stars**: 3,200+
**Focus**: Data visualization and infographic generation

LIDA treats "visualizations as code," generating charts and infographics through LLM-driven code generation.

**Architecture**:
- Grammar-agnostic: supports matplotlib, seaborn, altair, plotly
- Multi-stage pipeline: summarization → goal generation → visualization
- Includes visualization repair and explanation capabilities
- Beta infographic generation using stable diffusion

**Relevance to Claude Writer**: LIDA's goal-generation stage is interesting. Before creating visualizations, it generates goals (what story should the visualization tell?). This maps to Claude Writer's interview model; understanding intent before generating content.

---

### 10. spaCy-LLM

**Repository**: github.com/explosion/spacy-llm
**Focus**: Structured NLP pipelines with LLM integration

spaCy-LLM brings LLM capabilities into spaCy's proven pipeline architecture.

**Key Contribution**: Structured output extraction. LLMs generate unstructured text; spaCy-LLM converts this into validated, structured data.

**Relevance to Claude Writer**: The structured output pattern applies to any content system. When generating a view, Claude Writer needs consistent frontmatter (audience, style, structure). spaCy-LLM's approach to enforcing structure on LLM output could inform how we validate generated content.

---

## Part II: Content Publishing Pipelines

### Publishing Platform Integrations

**Ghost CMS**
- Repository: github.com/TryGhost/Ghost
- API: Separate Content API (reading) and Admin API (management)
- Automation: GitHub Actions and Pipedream integrations
- Status: Production-ready

**Cross-Platform Publishing**
- shahednasser/cross-post: CLI tool for Dev.to, Hashnode, Medium
- Articles post as drafts by default
- Each platform has different API patterns (REST vs GraphQL)

**WordPress REST API**
- AutomatorWP: No-code automation with webhooks
- Action Scheduler: Job queue for scheduled tasks
- Status: Production-ready

### Editorial Workflow Tools

**Superdesk** (superdesk.org)
- Comprehensive digital newsroom platform
- User-defined editorial workflows
- Headless CMS with easy integration
- Status: Production-ready for media organizations

**Git-Based Content Management**

*Decap CMS* (formerly Netlify CMS)
- Open-source with Git workflow integration
- Editorial workflow approval system
- Integrates with GitHub, GitLab, Gitea

*TinaCMS* (tina.io)
- Git-based with GitHub integration
- Branch-based review/approval
- Strong developer experience

*Strapi*
- Popular open-source headless CMS
- REST and GraphQL APIs
- n8n integration for workflows

### Workflow Automation

**n8n** (github.com/n8n-io/n8n)
- Most comprehensive: 400+ integrations
- Visual node-based workflow builder
- Self-hosted or cloud
- 2,700+ pre-built templates
- Native AI capabilities

Example workflow: Notion database → GPT-4 processing → Save to Notion → Post to Twitter/LinkedIn

**Open-Source Zapier Alternatives**
- Automatisch (automatisch.io): Direct open-source Zapier alternative
- Activepieces (activepieces.com): MIT licensed
- Huginn: Self-hosted hackable automation

### Newsletter Automation

**Buttondown** (buttondown.com)
- Feature-complete API
- Automations and personalizations
- Imports from ConvertKit and Mailchimp

**Integration Pattern**: Most newsletter platforms offer REST APIs; n8n or Zapier can orchestrate content flow from generation to distribution.

### Social Media Distribution

**Late** (getlate.dev)
- API for scheduling across 12+ platforms
- Twitter, Instagram, TikTok, LinkedIn, etc.
- Most flexible API setup

**RSS Feed Generation**
- @bliztek/feed-generator: Simple Node.js library
- No external dependencies
- TypeScript support

### Analytics and Feedback

**Open-Source A/B Testing**

*GrowthBook* (github.com/growthbook/growthbook)
- Open-source A/B testing platform
- Integrates with data warehouses
- Bayesian, Frequentist, Sequential testing

*PostHog*
- Built-in A/B testing with product analytics
- Feature flags and session recording
- 12,000+ GitHub stars

**Privacy-Focused Analytics**

*Plausible Analytics* (github.com/plausible/analytics)
- Open-source, privacy-friendly
- Scroll depth tracking (1-100%)
- Custom events and conversions
- GDPR compliant (no cookies)

### Headless CMS Patterns

**JAMstack Architecture**
- Content models → CI/CD pipelines → Static generation
- Webhooks trigger automatic publishing
- Multi-channel: single source, multiple platforms

**Leading Platforms**
- Sanity: Enterprise JAMstack, powerful image pipeline
- Contentful: Commercial, team coordination
- TinaCMS: Open-source, best DX
- Strapi: Popular open-source option

---

## Part III: Key Patterns and Their Application to Claude Writer

### Pattern 1: Role-Based Agent Specialization

**What It Is**: Rather than a single general-purpose agent, content systems use specialized agents with distinct roles: researcher, writer, editor, SEO specialist, fact-checker.

**Evidence**:
- CrewAI's seven-agent blog workflow
- NovelGenerator's three-agent model (Structure, Character, Scene)
- LLM-Blog-Generator's explicit role separation

**Application to Claude Writer**:

Current state: Claude Writer uses a single agent context that shifts roles based on commands (`/ideate`, `/generate-view`, `/generate-transcript`).

Opportunity: Explicit agent personas could improve quality. Consider:
- **Interviewer Agent**: Draws out ideas through targeted questions
- **Transcriber Agent**: Converts raw conversation to structured content
- **Writer Agent**: Generates prose from outlines
- **Editor Agent**: Refines voice, eliminates AI patterns, enforces style rules
- **Publisher Agent**: Handles distribution to platforms

The key is that these agents would still be conversational. The user talks to whichever agent is active; the agents coordinate behind the scenes.

---

### Pattern 2: Multi-Stage Pipelines

**What It Is**: Content moves through explicit stages, each optimized for a specific task. Common pattern: research → outline → draft → edit → review → publish.

**Evidence**:
- STORM's two-stage (pre-writing, writing) architecture
- NovelGenerator's 6+ phases per chapter
- LLM-Book-Generator's five-stage pipeline

**Application to Claude Writer**:

Current state: Claude Writer's layered stack (topic → outline → chapters → paragraphs → sentences) is conceptually similar but not explicitly staged.

Opportunity: Make stages explicit and visible. Each stage could:
- Have its own section in the idea space folder structure
- Be versioned independently via git
- Allow stage-specific editing without regenerating other stages

Proposed structure enhancement:
```
ideas/NNNN-name/
├── README.md           # Topic/concept
├── outlines/           # Stage 2: Structural outlines
├── drafts/             # Stage 3: Working drafts
├── assets/             # Supporting materials
├── transcripts/        # Raw ideation
└── views/              # Stage 5: Final published content
```

---

### Pattern 3: Slot/Placeholder Architecture

**What It Is**: Content templates include explicit placeholders (`[DIALOGUE_SLOT]`, `[ACTION_SLOT]`) that tell agents exactly what type of content to generate and where.

**Evidence**:
- NovelGenerator's slot-based methodology
- AntV Infographic's declarative component syntax

**Application to Claude Writer**:

Current state: Views are generated as complete documents; no explicit slot system.

Opportunity: Introduce placeholder syntax for structured generation:

```markdown
# Article Title

[HOOK: Engaging opening that establishes stakes]

## Background
[CONTEXT: Brief history, why this matters now]

## Main Argument
[THESIS: Core claim with supporting evidence]

### Point 1
[EVIDENCE: Data, quotes, examples]
[ANALYSIS: Interpretation and implications]

### Point 2
[EVIDENCE: Data, quotes, examples]
[ANALYSIS: Interpretation and implications]

## Conclusion
[SYNTHESIS: Tie together points]
[CALL_TO_ACTION: What reader should do/think]
```

Agents would recognize these slots and generate appropriate content. Users could approve or modify each slot independently.

---

### Pattern 4: Interpretable Memory

**What It Is**: System state is stored as human-readable text rather than opaque embeddings or database entries.

**Evidence**:
- RecurrentGPT's natural language memory stored on disk
- Git-based CMS approaches (Decap, TinaCMS)

**Application to Claude Writer**:

Current state: Already implemented. Filesystem is the database; git versions content. This is a strength.

Opportunity: Make memory more explicit. Consider:
- `ideas/NNNN-name/context.md`: Running summary of what's been discussed
- `ideas/NNNN-name/decisions.md`: Key choices made during ideation
- `ideas/NNNN-name/open-questions.md`: Unresolved issues to address

These files would be auto-updated by agents but human-readable and editable.

---

### Pattern 5: Structured Output Validation

**What It Is**: LLM output is validated against schemas or templates to ensure consistency and prevent malformed content.

**Evidence**:
- spaCy-LLM's structured output extraction
- AntV Infographic's fault-tolerant configuration language

**Application to Claude Writer**:

Current state: Views have frontmatter conventions but no formal validation.

Opportunity: Define schemas for different content types:

```yaml
# View schema
required:
  - title
  - audience
  - style
  - structure
  - content
optional:
  - sources
  - related_assets
  - publish_to
```

Commands could validate output against schemas before writing files.

---

### Pattern 6: Editorial Workflow Integration

**What It Is**: Content moves through approval stages before publication; multiple reviewers can comment and request changes.

**Evidence**:
- Superdesk's newsroom workflows
- TinaCMS's branch-based review
- CrewAI's QA Specialist agent

**Application to Claude Writer**:

Current state: Views go directly to the views folder; no review stage.

Opportunity: Git branches as review stages:
- `draft/view-name`: Initial generation
- `review/view-name`: Ready for human review
- `main`: Approved content

Commands could manage this workflow:
- `/submit-for-review`: Merge draft to review branch
- `/approve`: Merge review to main
- `/request-changes`: Add comments, return to draft

---

### Pattern 7: Publishing Pipeline Integration

**What It Is**: Content flows automatically from the creation system to publishing platforms (Ghost, Medium, newsletters, social).

**Evidence**:
- n8n workflows for multi-platform publishing
- Late API for social scheduling
- Ghost/WordPress API integrations

**Application to Claude Writer**:

Current state: No publishing integration; views are local markdown files.

Opportunity: Add `/publish` command with platform targeting:

```
/publish --platform=ghost,substack --schedule="2026-01-15 09:00"
```

Implementation approach:
1. Store platform credentials in `.claude/config/platforms.yml`
2. `/publish` command reads view, transforms to platform format, calls API
3. Track publishing status in view frontmatter

Minimum viable publishing:
- Ghost (for long-form)
- Substack/Buttondown (for newsletters)
- Late or Buffer (for social)

---

### Pattern 8: Feedback Loop Integration

**What It Is**: Published content performance informs future content decisions; analytics data feeds back into the creation system.

**Evidence**:
- GrowthBook A/B testing
- Plausible privacy-focused analytics

**Application to Claude Writer**:

Current state: No analytics integration.

Opportunity: Track performance in view metadata:

```yaml
---
title: "Article Title"
published_to:
  - platform: ghost
    url: https://blog.example.com/article
    date: 2026-01-10
performance:
  views: 1234
  read_time_avg: 4.2m
  engagement_rate: 0.08
  last_updated: 2026-01-12
---
```

A `/sync-analytics` command could pull performance data from platforms and update views. Over time, this data could inform which content types and styles perform best.

---

## Part IV: Recommended Evolution Path for Claude Writer

Based on this research, here's a prioritized roadmap:

### Phase 1: Strengthen Core Patterns

**1.1 Explicit Agent Roles**
- Define distinct agent personas in `.claude/agents/`
- Interviewer, Writer, Editor, Publisher as minimum set
- Each agent has clear responsibilities and voice

**1.2 Slot-Based Templates**
- Create template library in `templates/structures/`
- Blog post, research paper, short story, newsletter templates
- Each template uses placeholder syntax

**1.3 Memory Files**
- Add `context.md`, `decisions.md`, `open-questions.md` to idea spaces
- Auto-update during ideation sessions
- Human-readable and editable

### Phase 2: Editorial Workflow

**2.1 Branch-Based Review**
- Draft → Review → Main workflow
- `/submit-for-review` and `/approve` commands
- Comments stored in review branch

**2.2 Quality Validation**
- Schema validation for views
- Style rule enforcement (no dashes, semicolon usage)
- Pre-commit hooks for content quality

### Phase 3: Publishing Pipeline

**3.1 Platform Integrations**
- Ghost CMS (primary long-form)
- Buttondown (newsletters)
- Late API (social scheduling)

**3.2 Publish Command**
- `/publish` with platform targeting
- Schedule support
- Status tracking in view metadata

**3.3 Cross-Platform Syndication**
- Automatic formatting for each platform
- Canonical URL handling
- Platform-specific optimizations

### Phase 4: Feedback Loop

**4.1 Analytics Integration**
- Plausible or similar for website
- Platform-native analytics APIs
- Performance data in view metadata

**4.2 Performance-Informed Creation**
- Analyze what performs well
- Suggest topics/formats based on data
- A/B testing for headlines (future)

---

## Part V: Notable Quotes and Insights

From the original Claude Writer vision transcript:

> "I want everything to be generateable by agents, manageable by agents. I only want to talk to this system."

This aligns perfectly with the multi-agent patterns observed. The key difference from most systems: Claude Writer prioritizes conversation over automation. The user isn't configuring workflows; they're talking.

> "At any point, you can come in and edit a particular sentence; you could edit a paragraph; you could delete a paragraph... at any level."

The layered stack concept is more sophisticated than most existing systems. STORM and NovelGenerator work at document level; Claude Writer aims for sentence-level editability with cascade effects.

> "I could have a journalist agent come in, I could have an Ezra Klein agent come in, I could have my own personal agent come in."

This multi-voice capability is unique. Most systems have one voice; Claude Writer envisions swappable personas that can edit the same content differently.

> "The gold standard is you should not be doing anything yourself; you should only be ideating, and in particular you should be talking to your computer."

Voice-first is a differentiator. The research shows many keyboard-first systems; Claude Writer's Wispr Flow integration puts it ahead of the curve.

---

## Appendix A: Repository Quick Reference

| Project | URL | Stars | Primary Use |
|---------|-----|-------|-------------|
| STORM | github.com/stanford-oval/storm | 27.8k | Research synthesis |
| Dify | github.com/langgenius/dify | 125k | Workflow platform |
| NovelGenerator | github.com/KazKozDev/NovelGenerator | Active | Fiction writing |
| AntV Infographic | github.com/antvis/Infographic | 3.6k | Infographics |
| CrewAI | github.com/crewAIInc/crewAI | Industry std | Agent framework |
| RecurrentGPT | github.com/aiwaves-cn/RecurrentGPT | Research | Long-form memory |
| LIDA | github.com/microsoft/lida | 3.2k | Data visualization |
| n8n | github.com/n8n-io/n8n | 50k+ | Workflow automation |
| Ghost | github.com/TryGhost/Ghost | 47k+ | Publishing platform |
| Plausible | github.com/plausible/analytics | 22k+ | Privacy analytics |
| GrowthBook | github.com/growthbook/growthbook | 6k+ | A/B testing |
| TinaCMS | github.com/tinacms/tinacms | 12k+ | Git-based CMS |

## Appendix B: Publishing Platform APIs

| Platform | API Type | Key Capability |
|----------|----------|----------------|
| Ghost | REST | Full CMS control |
| Medium | REST | Post creation |
| Dev.to | REST | Article publishing |
| Hashnode | GraphQL | Full blog control |
| Substack | Limited | Newsletter focus |
| Buttondown | REST | Newsletter automation |
| WordPress | REST | Complete CMS access |
| Late | REST | Social scheduling |

## Appendix C: Recommended Stack

For a production Claude Writer publishing pipeline:

```
Content Generation
    │
    ▼
Claude Writer (local markdown + git)
    │
    ▼
n8n (workflow orchestration)
    │
    ├──► Ghost (long-form articles)
    ├──► Buttondown (newsletters)
    ├──► Late (social media)
    │
    ▼
Plausible (analytics) ──► Feedback to Claude Writer
```

---

*Research conducted January 2026. Sources include GitHub repositories, official documentation, and community implementations.*
