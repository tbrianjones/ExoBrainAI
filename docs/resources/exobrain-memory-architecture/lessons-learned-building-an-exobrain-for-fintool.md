# Lessons from Building AI Agents for Financial Services

**Source article:**  
Nicolas Bustamante, *Lessons from Building AI Agents for Financial Services*  
https://www.nicolasbustamante.com/p/lessons-from-building-ai-agents-for

**Company / product referenced:**  
Fintool – AI research platform for professional investors  
https://fintool.com/

---

## High-Level Summary

This article documents the technical and product lessons learned while building **Fintool**, an AI-powered research platform for institutional and professional equity investors. The core takeaway is that **the reliability, trustworthiness, and usefulness of AI agents in high-stakes domains comes almost entirely from the surrounding systems, not from the LLM itself**.

The work emphasizes execution safety, data normalization, structured context, workflow orchestration, and evaluation rigor as the real determinants of success.

---

## Key Lessons

### 1. High-Stakes Domains Demand Infrastructure, Not Prompting
In finance, even small errors destroy trust. Users are domain experts who notice mistakes immediately. As a result:
- Accuracy and verifiability matter more than fluency.
- Systems must assume adversarial data and user scrutiny.
- The LLM is treated as a reasoning component, not an oracle.

---

### 2. Isolated Execution Environments Are Mandatory
AI agents must perform multi-step tasks involving:
- Code execution
- Data transformations
- File generation
- Iterative recalculation

To support this safely, each agent operates inside a **fully isolated sandbox**:
- Scoped credentials
- Filesystem access
- Controlled package installation
- Bash and scripting support

This isolation is foundational for autonomy and safety.

---

### 3. Context Engineering Is the Core Product
Most failures come from bad or malformed context, not model limitations.

Key practices:
- Normalize all source data into predictable formats (Markdown, CSV, JSON).
- Treat parsing and cleaning as first-class engineering problems.
- Maintain high-quality metadata and chunking strategies.
- Filter or score inputs before they ever reach the model.

The quality of the context pipeline directly determines answer quality.

---

### 4. Parsing Real-World Data Is Adversarial
Financial documents are messy:
- Inconsistent tables
- Embedded footnotes
- Ambiguous fiscal periods
- Industry-specific conventions

Off-the-shelf parsers are insufficient. Robust systems require:
- Custom parsing logic
- Validation checks
- Confidence scoring
- Failure detection and fallback paths

Parsing is a correctness gate, not a preprocessing detail.

---

### 5. “Skills” Replace Prompt Engineering
Rather than relying on large, fragile prompts, the system is organized around **skills**:
- Explicit, modular task definitions
- Often written in Markdown
- Capture domain-specific steps and assumptions
- Editable by domain experts, not just engineers

Skills act as durable, inspectable instructions that encode business logic outside the model.

---

### 6. Design Scaffolding to Be Disposable
As models improve, scaffolding logic becomes obsolete.

The system intentionally:
- Uses simple, human-readable instruction formats
- Avoids over-engineering model workarounds
- Accepts that many skills will shrink or disappear over time

The goal is adaptability, not permanence.

---

### 7. Simple, Durable Storage Wins
The architecture favors **file-centric storage**:
- Object storage (e.g. S3) as the source of truth
- Databases used for indexing and retrieval
- Markdown files for skills, memory, and configuration

Benefits include:
- Easy versioning
- Human readability
- Straightforward migrations
- Clear audit trails

---

### 8. Filesystem and Shell Access Are Powerful Primitives
Providing agents with controlled access to:
- Read/write files
- Run shell commands
- Inspect intermediate outputs

dramatically increases their effectiveness for real analytical work compared to narrow API-only toolsets.

---

### 9. Long-Running Workflows Need Orchestration
Many tasks exceed a single request/response cycle.

To support this, the system uses:
- Durable workflow orchestration (e.g. Temporal-style patterns)
- Persistent state
- Retries, cancellation, and resumability
- Separation between interactive and background work

This is critical for reliability at scale.

---

### 10. Streaming and Incremental UX Builds Trust
Professional users expect responsiveness.

Instead of waiting for full results:
- Partial progress is streamed
- Intermediate artifacts are visible
- Users can see what the agent is doing and why

Transparency improves confidence and usability.

---

### 11. Evaluation Must Be Domain-Specific
Generic LLM metrics are insufficient.

Robust evaluation includes:
- Custom test suites for numeric accuracy
- Disambiguation checks
- Hallucination resistance tests
- Regression gates that block degraded deployments

Evaluation is continuous and enforced in production.

---

### 12. Observability Is a First-Class Feature
Production systems include:
- Structured logs
- Traceability from outputs to inputs
- Automated error reporting
- Cost and complexity routing across models

Observability is required to maintain trust over time.

---

## Core Thesis

**The LLM is not the product.**  
The real product is the surrounding system:
- Data pipelines
- Context normalization
- Skills
- Execution safety
- Workflow orchestration
- Evaluation and monitoring

This pattern generalizes beyond finance to any domain where correctness, trust, and explainability matter.

---

## References

- Article: https://www.nicolasbustamante.com/p/lessons-from-building-ai-agents-for  
- Fintool: https://fintool.com/
