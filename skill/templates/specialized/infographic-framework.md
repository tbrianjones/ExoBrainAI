# Infographic Generation Framework

For generating visual content specifications from idea spaces.

## What This Produces

Not an actual image, but detailed specifications that could be handed to a designer or image generation tool. Focuses on:

- Data relationships
- Visual hierarchy
- Text content
- Layout suggestions

## Process

1. **Load the idea space** - Read all context
2. **Identify the core argument** - What's the one thing this should communicate?
3. **Extract data points** - Numbers, comparisons, sequences
4. **Find the visual metaphor** - How does this information want to be seen?
5. **Specify the layout** - Sections, flow, emphasis

## Infographic Types

| Type | Best For | Example |
|------|----------|---------|
| Comparison | Two or more things contrasted | "X vs Y" side-by-side |
| Process | Sequential steps | Flowchart, timeline |
| Hierarchy | Ranked or nested information | Pyramid, tree |
| Data | Numerical relationships | Charts, graphs |
| Map | Spatial or conceptual territory | Augmentation map, ecosystem |
| Anatomy | Parts of a whole | Labeled diagram |

## Output Format

```yaml
---
title: [Infographic Title]
type: infographic
infographic-type: [comparison | process | hierarchy | data | map | anatomy]
source-idea: [idea folder name]
audience: [Who will see this]
key-takeaway: [One sentence the viewer should remember]
---
```

## Specification Sections

### Visual Concept
[2-3 sentences describing the overall visual approach and metaphor]

### Layout
[Description of major sections and how they relate spatially]

### Section 1: [Name]
- **Heading**: [Text]
- **Content**: [Text or data points]
- **Visual treatment**: [How this should look]

### Section 2: [Name]
[Continue for all sections]

### Color Palette
- Primary: [Color and meaning]
- Secondary: [Color and meaning]
- Accent: [Color and meaning]

### Typography Notes
- Headlines: [Style]
- Body: [Style]
- Data/Numbers: [Style]

### Source Citations
[Any data sources that should be credited]
