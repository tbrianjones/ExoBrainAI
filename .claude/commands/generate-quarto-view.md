---
name: generate-quarto-view
description: Create a Quarto document (.qmd) for publishing to writing.tbryanjones.com. Supports interactive elements, code, and data visualizations.
allowed-tools: Read, Write, Glob, Bash
---

# Quarto View Generator

Create publication-ready Quarto documents within an idea space. These documents can include interactive visualizations, executable code, and rich formatting for the writing site.

## CRITICAL: Load Context First

Before any interaction with the user, you MUST load the entire idea folder:

1. **Read the README.md** in the idea folder
2. **Load ALL transcripts** from `transcripts/`
3. **Load ALL assets** from `assets/`
4. **Scan existing views** in `views/`

Only AFTER loading this context should you proceed with the user interaction.

## Content Guidelines

When writing prose:
- **No dashes or double dashes.** Use semicolons or restructure.
- **Use semicolons** to join related independent clauses.
- **Use ellipses (...)** sparingly for trailing off.
- Keep prose grounded; avoid flowery language.
- Preserve the human's phrasing when it captures the idea well.
- Draw on transcript material; use the human's own words when powerful.

## Process (After Loading Context)

### 1. Confirm the content type

Ask the user:
- What kind of post? (article, tutorial, analysis, interactive exploration, application)
- Who is the audience?
- What's the core purpose or thesis?

### 2. Determine interactivity level

Options:
- **Static**: Code blocks with syntax highlighting; no execution
- **Observable JS**: Reactive visualizations, sliders, interactive charts (runs in browser)
- **Full application**: Custom JavaScript app embedded in the page

Most posts should use Observable JS for interactivity; it's built into Quarto.

### 3. Define the voice

- Ask for a description of the voice/tone/personality
- Or suggest one based on transcripts
- Examples: "conversational expert", "curious explorer", "direct and technical"

### 4. Calibrate style attributes

Discuss and assign 0-100 scores:
- technical (how much assumed knowledge)
- formality (casual to academic)
- density (sparse vs information-packed)
- interactivity (how much user engagement expected)

### 5. Build the outline

- Create structural skeleton first
- Identify where interactive elements will go
- Identify what data/code examples are needed
- Get user approval before generating

### 6. Generate the Quarto document

Write the `.qmd` file with:
- Proper YAML frontmatter
- Markdown content
- Observable JS blocks for interactivity
- Code blocks with appropriate language tags

### 7. Write the file

Output to: `ideas/NNNN-name/views/quarto-[title].qmd`

## Quarto File Structure

```qmd
---
title: "[Title]"
description: "[One-line description for listing pages]"
author: "T. Brian Jones"
date: "YYYY-MM-DD"
categories: [category1, category2]
format:
  html:
    toc: true
    code-fold: true
---

## Introduction

[Opening content...]

## Section with Code

Here's some Python:

```{python}
#| echo: true
#| eval: false
def example():
    return "Hello"
```

## Section with Interactive Elements

```{ojs}
//| echo: false
viewof slider = Inputs.range([0, 100], {value: 50, label: "Adjust"})
```

The value is **${slider}**.

```{ojs}
//| echo: false
Plot.plot({
  marks: [
    Plot.dot(data, {x: "x", y: "y"})
  ]
})
```

## Including Data

```{ojs}
//| echo: false
data = FileAttachment("data.csv").csv({typed: true})
```

## Conclusion

[Closing content...]
```

## Observable JS Quick Reference

### Inputs (interactive controls)

```ojs
// Slider
viewof value = Inputs.range([min, max], {value: default, step: 1, label: "Label"})

// Dropdown
viewof selection = Inputs.select(["Option A", "Option B"], {label: "Choose"})

// Text input
viewof text = Inputs.text({placeholder: "Enter text", label: "Label"})

// Checkbox
viewof checked = Inputs.toggle({label: "Enable feature"})

// Radio buttons
viewof choice = Inputs.radio(["A", "B", "C"], {label: "Pick one"})
```

### Displaying values

```ojs
// Inline: The value is ${variableName}
// Or use a code block that returns the value
```

### Observable Plot (charts)

```ojs
Plot.plot({
  marks: [
    Plot.dot(data, {x: "xColumn", y: "yColumn", fill: "category"}),
    Plot.line(data, {x: "x", y: "y"}),
    Plot.barY(data, {x: "category", y: "value"}),
    Plot.text(data, {x: "x", y: "y", text: "label"})
  ],
  width: 640,
  height: 400
})
```

### Loading data

```ojs
// CSV
data = FileAttachment("data.csv").csv({typed: true})

// JSON
data = FileAttachment("data.json").json()

// From URL (if CORS allows)
data = fetch("https://api.example.com/data").then(r => r.json())
```

## For Full Applications

If the user wants to embed a complete application:

```qmd
---
title: "My App"
format:
  html:
    page-layout: full
    toc: false
---

<div id="app"></div>

<script type="module">
// Application code here
// Or import from a bundled JS file in the same folder
import { createApp } from './app.js';
createApp(document.getElementById('app'));
</script>

<style>
/* App-specific styles */
#app {
  width: 100%;
  min-height: 80vh;
}
</style>
```

## Data Files

If the post needs data files:
1. Create them alongside the `.qmd` file in the idea's views folder
2. When publishing, both the `.qmd` and data files will be copied

Example structure:
```
ideas/0001-example/views/
├── quarto-analysis.qmd
├── data.csv
└── images/
    └── diagram.png
```

## Naming Convention

- File: `quarto-[short-title].qmd` (e.g., `quarto-memory-palace.qmd`)
- Lowercase, hyphens for spaces

## After Generation

Tell the user:
- The file has been created at `ideas/NNNN-name/views/quarto-[title].qmd`
- To publish: run `/publish-quarto` and select this file
- To preview locally: run `quarto preview` in the writing-site directory after copying

## Example Categories

Common categories for the site:
- technology, ai, programming, data, visualization
- ideas, philosophy, thinking, creativity
- tutorial, analysis, exploration, experiment
- meta, personal, reflection
