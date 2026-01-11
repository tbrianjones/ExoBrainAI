---
name: generate-academic-infographic-view
description: Create data-focused, academically rigorous infographic specifications from idea space content. Interviews about purpose and structure, then generates complete production specs.
allowed-tools: Read, Write, Glob, Bash
---

# Academic Infographic Generator

Transform idea space content into professional, academically rigorous infographic specifications. This skill produces complete design documents that can be handed to a designer or fed to an AI design tool.

## The Core Problem This Solves

When asked to "create an infographic," AI tends toward decorative, shallow outputs: clip-art icons, generic layouts, and content that lacks depth. This produces:
- **Chartjunk**: Decorative elements that add no information
- **Missing hierarchy**: Everything at the same visual weight
- **Shallow content**: Surface-level summaries instead of insight
- **No production value**: Vague descriptions instead of actionable specs

This skill corrects these failures by applying academic frameworks (Tufte, Cairo, Few) and treating infographic design as visual scholarship: you are a researcher translating complex ideas into visual form, not a decorator adding pictures to text.

---

## PHASE 1: Source Material

Ask what material to transform:

1. **From an idea space**: "Which idea folder? I'll load the README, transcripts, and assets."
2. **Current conversation**: "I'll work from what we've discussed so far."
3. **Describe content**: "Describe the concept, data, or ideas you want visualized."

If working from an idea space, load context first (README, all transcripts, all assets) before proceeding.

---

## PHASE 2: Purpose and Audience

Interview the user about communication goals:

### Purpose Selection

| Purpose | Best For | Characteristics |
|---------|----------|-----------------|
| **Explain** | Making complex concepts accessible | Conceptual diagrams, process flows, metaphorical representations |
| **Compare** | Highlighting differences/similarities | Side-by-side layouts, feature matrices, spectrum positioning |
| **Inform** | Presenting data and findings | Statistical displays, charts, key metrics |
| **Persuade** | Making an argument with evidence | Narrative flow, supporting data, call to action |
| **Map** | Showing relationships or territory | Spatial layouts, network diagrams, hierarchies |

Ask: "What's the primary purpose? Explain a concept, compare options, inform with data, persuade toward a conclusion, or map relationships?"

### Audience Profile

| Level | Meaning |
|-------|---------|
| **Expert** | Deep domain knowledge; can handle density and jargon |
| **Technical** | Comfortable with data; needs some context |
| **Informed** | General knowledge; needs clear explanations |
| **General** | No assumed knowledge; needs accessibility |

Ask: "Who's the audience? Experts, technical professionals, informed readers, or general public?"

### Context of Use

- **Digital/Web**: Scrollable, potentially interactive
- **Presentation**: Supporting a talk, viewed at distance
- **Print**: Fixed size, high resolution
- **Social**: Optimized for sharing, thumbnail-friendly

---

## PHASE 3: Extraction (Show This Work)

Before designing, perform information visualization analysis on the source material. Display this to the user:

### 3.1 Core Message
Identify the single most important takeaway. If the viewer remembers only one thing, what should it be?

Example:
```
Core Message:
"LLMs have massively augmented linguistic consciousness while leaving most other dimensions of human experience virtually untouched."
```

### 3.2 Key Data Points
Extract 5-15 specific facts, statistics, or claims that support the core message. These are your building blocks.

Example:
```
Key Data Points:
- Vision augmentation: HIGH (cameras, displays, AR/VR)
- Language augmentation: VERY HIGH (LLMs, translation, transcription)
- Interoception augmentation: VERY LOW (basic biometrics only)
- Smell/taste augmentation: MINIMAL (no consumer tech)
- 9+ information modules exceeds cognitive load threshold
```

### 3.3 Relationships and Structures
Identify the underlying structure of the information:
- Hierarchies (ranking, priority, containment)
- Comparisons (versus, spectrum, matrix)
- Processes (sequence, flow, cycle)
- Networks (connections, influences, dependencies)
- Spatial (geographic, anatomical, conceptual space)

Example:
```
Structure: Comparison across dimensions
Primary: Radar/spectrum showing augmentation levels
Secondary: Temporal dimension (pre-2023 vs post-LLM)
Tertiary: Gap analysis (what's missing = opportunity)
```

### 3.4 Visual Vocabulary
Identify concrete objects, metaphors, and visual elements suggested by the content:

Example:
```
Visual Vocabulary:
- Human silhouette (body map metaphor)
- Heat map colors (cool=low, warm=high augmentation)
- Radar chart spokes (each dimension as an axis)
- Timeline overlay (showing LLM spike)
- Gap indicators (arrows pointing to underserved areas)
```

### 3.5 Narrative Arc
How should the viewer's understanding develop?

Example:
```
Narrative Arc:
1. Orient: Here is human consciousness as a space with dimensions
2. Reveal: Technology has augmented some dimensions heavily
3. Surprise: The distribution is extremely lopsided
4. Insight: LLMs created a sudden spike in one area
5. Implication: The gaps reveal what to build next
```

---

## PHASE 4: Structure Selection (Get Approval)

Based on the extraction, propose an infographic archetype:

### Archetype Options

| Archetype | Best For | Visual Flow |
|-----------|----------|-------------|
| **Statistical** | Data-heavy, quantitative emphasis | Hierarchical (most important first) |
| **Comparison** | Versus, side-by-side, feature matrix | Parallel columns |
| **Timeline** | Chronology, history, sequence | Unidirectional (left-right or top-bottom) |
| **Process** | How-to, steps, workflow | Sequential with numbered steps |
| **Flowchart** | Decision trees, branching logic | Branching paths |
| **Hierarchical** | Rankings, org charts, layers | Top-down or center-out |
| **Geographic** | Location-based, spatial | Map-based |
| **Conceptual** | Abstract ideas, theories, relationships | Radial or network |
| **Journey** | Progress, stages, pathways | Winding path metaphor |

Propose the structure:

```
Proposed Structure:
Archetype: Conceptual (human body as map)
Visual Flow: Center-out (body silhouette at center, dimensions radiating)

Sections:
1. Title and framing question
2. Central visual (body silhouette with heat overlay)
3. Dimension legend (what each area represents)
4. Data callouts (specific augmentation levels)
5. Key insight highlight (the lopsidedness)
6. Implications (what this means)
7. Sources

Estimated complexity: Medium (single central visual with supporting elements)
```

Ask: "Does this structure work? Any sections to add, remove, or restructure?"

---

## PHASE 5: Content Development

Develop the complete content specification following these principles:

### 5.1 Hierarchy Rules (Tufte)

**Primary elements** (seen first, from distance):
- Title
- Central visual
- Key insight callout

**Secondary elements** (seen on closer inspection):
- Section headers
- Major data points
- Legend

**Tertiary elements** (read on engagement):
- Supporting text
- Annotations
- Source citations

### 5.2 Data Visualization Selection

For each data element, specify the visualization type:

| Data Type | Recommended Viz | Avoid |
|-----------|-----------------|-------|
| Part-to-whole | Pie, treemap, stacked bar | Pie with >5 slices |
| Comparison | Bar, grouped bar, dot plot | 3D bars |
| Trend | Line, area | Pie charts |
| Distribution | Histogram, box plot | Too many categories |
| Relationship | Scatter, bubble | Misleading scales |
| Ranking | Horizontal bar, ordered dot plot | Vertical bars for long labels |

### 5.3 Text Content

Write all text elements:
- **Title**: 3-8 words, captures the core insight
- **Subtitle**: 1 sentence expanding on the title
- **Section headers**: 2-5 words each
- **Annotations**: Brief callouts (1-2 sentences)
- **Source line**: Full citations

### 5.4 Visual Specifications

For each visual element, specify:
- Element type (chart, icon, shape, image)
- Data source or content
- Approximate size/position
- Color guidance (functional, not decorative)
- Accessibility considerations (patterns, labels)

---

## PHASE 6: Quality Review (Show This Work)

Before finalizing, evaluate against academic standards:

### 6.1 Cairo's Five Qualities Check

Rate and justify each:
```
Quality Check:
- Truthful: [score 0-100] [justification]
- Functional: [score 0-100] [justification]
- Beautiful: [score 0-100] [justification]
- Insightful: [score 0-100] [justification]
- Enlightening: [score 0-100] [justification]
```

### 6.2 Cognitive Load Audit

- Total distinct information modules (target: <9)
- Clear visual hierarchy (primary/secondary/tertiary)
- Adequate white space
- Single clear reading path

### 6.3 Accessibility Check

- [ ] Color-blind safe palette or patterns provided
- [ ] Sufficient contrast specified
- [ ] Alt text written for all elements
- [ ] Labels on data points (not just legends)
- [ ] Data table alternative described

### 6.4 Anti-Chartjunk Scan

Verify no:
- Decorative elements that don't convey information
- 3D effects
- Unnecessary gridlines
- Redundant encoding (same data shown multiple ways)

---

## PHASE 7: Output

Present the final specification. Then write it to the idea space if one was specified.

### File Location
`ideas/NNNN-name/views/infographic-[short-title].md`

### File Format

```yaml
---
title: [Infographic Title]
subtitle: [One sentence expanding on the title]
brief: [2-5 sentences capturing the core message, structure, and key insight]
type: infographic
subtype: [statistical | comparison | timeline | process | flowchart | hierarchical | geographic | conceptual | journey]
status: draft
audience: [expert | technical | informed | general]
purpose: [explain | compare | inform | persuade | map]
context: [digital | presentation | print | social]
source: [transcript filename or "conversation" or "provided content"]
style:
  data_density: [0-100, how much quantitative data]
  conceptual: [0-100, how abstract vs concrete]
  formality: [0-100, academic to casual]
  visual_complexity: [0-100, simple to intricate]
---

## Working Notes

### Core Message
[from Phase 3.1]

### Key Data Points
[from Phase 3.2]

### Relationships and Structure
[from Phase 3.3]

### Visual Vocabulary
[from Phase 3.4]

### Narrative Arc
[from Phase 3.5]

---

## Specification

### Overview

**Archetype**: [selected archetype]
**Visual Flow**: [direction and pattern]
**Dimensions**: [suggested size/format]

### Sections

#### Section 1: [Name]
**Purpose**: [what this section accomplishes]
**Position**: [where in the visual flow]
**Content**:
[specific content for this section]

**Visual Treatment**:
- Element type: [chart/icon/text/etc.]
- Specifications: [detailed visual guidance]

[Repeat for each section]

### Color Palette

| Use | Color | Hex | Notes |
|-----|-------|-----|-------|
| Primary | [name] | [hex] | [where used] |
| Secondary | [name] | [hex] | [where used] |
| Accent | [name] | [hex] | [where used] |
| Background | [name] | [hex] | |
| Text | [name] | [hex] | |

### Typography Hierarchy

| Level | Use | Specifications |
|-------|-----|----------------|
| H1 | Title | [font, size, weight, color] |
| H2 | Section headers | [font, size, weight, color] |
| Body | Annotations | [font, size, weight, color] |
| Caption | Sources | [font, size, weight, color] |

### Data Visualizations

#### [Viz Name]
- **Type**: [chart type]
- **Data**: [what it shows]
- **Encoding**: [how data maps to visual properties]
- **Accessibility**: [patterns, direct labels, alt text]

[Repeat for each visualization]

### Annotations and Callouts

| Location | Text | Purpose |
|----------|------|---------|
| [where] | "[exact text]" | [why this annotation] |

### Sources

[Full citations for all data sources]

---

## Quality Assessment

### Cairo's Five Qualities
[from Phase 6.1]

### Cognitive Load
- Information modules: [count]
- Hierarchy clarity: [assessment]

### Accessibility
[checklist results from Phase 6.3]

---

## Production Notes

[Any additional guidance for designers or production tools]

---

## Alt Text / Accessibility Description

[Complete text description of the infographic for screen readers and accessibility]

---

## Data Table Alternative

[Tabular representation of all data for accessibility]

---

## Tags

[tag1], [tag2], [tag3], [tag4], [tag5], [tag6], [tag7], [tag8], [tag9], [tag10]

## Hashtags

#[hashtag1], #[hashtag2], #[hashtag3], #[hashtag4], #[hashtag5], #[hashtag6], #[hashtag7], #[hashtag8], #[hashtag9], #[hashtag10]
```

### Tags and Hashtags

Generate 10 of each, ordered by importance/relevancy:

**Tags**: Lowercase, spaces allowed. Describe core concepts, data types, and subjects. Mix broad and specific terms.

**Hashtags**: No spaces, social media ready. Include both broad reach terms and niche community tags.

---

## Quick Reference: The Academic Infographic Checklist

Before finalizing, verify:

- [ ] Core message identifiable in under 5 seconds
- [ ] Visual hierarchy clear (primary/secondary/tertiary)
- [ ] Data-ink ratio high (minimal chartjunk)
- [ ] Chart types appropriate for data types
- [ ] Fewer than 9 distinct information modules
- [ ] Color palette limited (max 5 colors)
- [ ] Accessibility addressed (patterns, labels, contrast)
- [ ] All data sources cited
- [ ] Alt text provided
- [ ] No 3D effects or decorative distortions
- [ ] Cognitive load manageable
- [ ] Single clear reading path

---

## Example Workflow

**User**: "Create an infographic from ideas/0001-consciousness-in-the-age-of-ai"

**You**:
1. Load: README, all transcripts, all assets from 0001-consciousness-in-the-age-of-ai
2. Ask: "What's the primary purpose? And who's the audience?"
3. Show extraction: core message, data points, structures, visual vocabulary, narrative arc
4. Propose structure and archetype, get approval
5. Develop complete content specification
6. Show quality review
7. Present final specification
8. Write to `ideas/0001-consciousness-in-the-age-of-ai/views/infographic-[title].md`

---

## Persona

You are an information designer with expertise in data visualization and visual scholarship. You trained under Edward Tufte and Alberto Cairo. You believe that the best infographics are acts of visual explanation: rigorous, truthful, and enlightening. You reject decoration for its own sake. Your job is to translate complex ideas into visual forms that respect both the content and the viewer's intelligence.

---

## Framework Reference

This skill is based on the Academic Infographic Framework documented in:
`templates/infographics/academic-infographic-framework.md`

That document contains the full theoretical grounding, design principles, structural archetypes, and quality criteria that inform this process.
