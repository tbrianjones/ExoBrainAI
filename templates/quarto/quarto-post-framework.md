# Quarto Post Framework

Reference documentation for creating Quarto documents in the ExoBrain system.

## What is Quarto?

Quarto is a scientific and technical publishing system that compiles Markdown, code, and interactive elements into static HTML. It's ideal for:

- Articles with embedded code and output
- Interactive data visualizations
- Tutorials with executable examples
- Small applications embedded in pages

## File Format

Quarto documents use the `.qmd` extension. They're Markdown files with YAML frontmatter and special code block syntax.

## Basic Structure

```qmd
---
title: "Your Title"
description: "Brief description for listings"
author: "T. Brian Jones"
date: "2026-01-10"
categories: [category1, category2]
format:
  html:
    toc: true
    code-fold: true
---

Your content here...
```

## Frontmatter Options

### Required

```yaml
title: "Post Title"
date: "YYYY-MM-DD"
```

### Recommended

```yaml
description: "One-line description"
author: "T. Brian Jones"
categories: [tag1, tag2]
```

### Optional

```yaml
image: "thumbnail.png"           # Preview image for listings
draft: true                      # Hide from published site
toc: true                        # Table of contents
toc-depth: 2                     # How deep to show headings
code-fold: true                  # Collapse code by default
code-tools: true                 # Show code toggle button
execute:
  echo: true                     # Show code in output
  eval: false                    # Don't run code (for display only)
format:
  html:
    page-layout: full            # For apps: remove margins
    toc: false                   # For apps: no sidebar
```

## Code Blocks

### Display only (no execution)

````qmd
```python
def hello():
    return "Hello"
```
````

### With Quarto options

````qmd
```{python}
#| echo: true
#| eval: false
#| label: my-code
def hello():
    return "Hello"
```
````

### Supported languages

- Python: `{python}`
- R: `{r}`
- Julia: `{julia}`
- JavaScript: `{javascript}`
- Observable JS: `{ojs}` (interactive)

## Observable JS (Interactive Elements)

Observable JS runs in the browser and enables reactive, interactive content.

### Basic reactive variable

```{ojs}
x = 5
y = x * 2
```

### Input controls

```{ojs}
// Slider
viewof temperature = Inputs.range([0, 100], {
  value: 50,
  step: 1,
  label: "Temperature"
})

// Dropdown
viewof color = Inputs.select(["red", "blue", "green"], {
  label: "Color"
})

// Text
viewof name = Inputs.text({
  placeholder: "Enter name",
  label: "Name"
})

// Toggle
viewof enabled = Inputs.toggle({
  label: "Enable feature"
})

// Radio
viewof size = Inputs.radio(["small", "medium", "large"], {
  label: "Size"
})

// Date
viewof date = Inputs.date({
  label: "Date"
})
```

### Using input values

```{ojs}
// In text: The temperature is ${temperature}°F
// In code: temperature is reactive
```

### Observable Plot (charting)

```{ojs}
Plot.plot({
  marks: [
    Plot.dot(data, {x: "x", y: "y", fill: "category"}),
    Plot.line(data, {x: "x", y: "y"}),
    Plot.barY(data, {x: "category", y: "value"}),
    Plot.areaY(data, {x: "date", y: "value"}),
    Plot.text(data, {x: "x", y: "y", text: "label"})
  ],
  width: 640,
  height: 400,
  color: {legend: true},
  x: {label: "X Axis"},
  y: {label: "Y Axis"}
})
```

### Loading data

```{ojs}
// From file in same folder
data = FileAttachment("data.csv").csv({typed: true})
json = FileAttachment("data.json").json()

// From URL
remote = fetch("https://api.example.com/data").then(r => r.json())
```

### Common patterns

```{ojs}
// Filter data based on input
filtered = data.filter(d => d.category === selection)

// Compute derived value
total = data.reduce((sum, d) => sum + d.value, 0)

// Conditional display
html`${enabled ? "Feature is ON" : "Feature is OFF"}`
```

## Embedding Applications

For full applications, use a minimal layout:

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
// Inline app code
const app = document.getElementById('app');
app.innerHTML = '<h1>Hello from the app!</h1>';

// Or import from file
import { init } from './app.js';
init(app);
</script>

<style>
#app {
  width: 100%;
  min-height: 80vh;
  padding: 2rem;
}
</style>
```

## Including Images

```qmd
![Alt text](image.png)

![With caption](image.png){fig-alt="Description" fig-cap="Caption text"}
```

## Math (LaTeX)

```qmd
Inline: $E = mc^2$

Block:
$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$
```

## Callouts

```qmd
::: {.callout-note}
This is a note.
:::

::: {.callout-warning}
This is a warning.
:::

::: {.callout-tip}
This is a tip.
:::

::: {.callout-important}
This is important.
:::
```

## Tabs

```qmd
::: {.panel-tabset}
## Tab 1
Content for tab 1

## Tab 2
Content for tab 2
:::
```

## Layout

### Columns

```qmd
::: {.columns}
::: {.column width="50%"}
Left column
:::
::: {.column width="50%"}
Right column
:::
:::
```

### Full width

```qmd
::: {.column-page}
This content spans the full page width
:::
```

## Style Guidelines

When writing Quarto posts for this system:

1. **No dashes or double dashes** in prose; use semicolons
2. **Keep code examples minimal** but complete
3. **Interactive elements should be purposeful**, not decorative
4. **Data files go in the same folder** as the `.qmd`
5. **Categories should be lowercase** and limited to 2-4
6. **Descriptions should be one line** for clean listings

## File Organization

Views are created as `.md` files in idea spaces. When published via `/publish-quarto`, they are converted to Quarto format and saved directly to `site/posts/`:

```
site/posts/YYYY-MM-DD-my-analysis/
├── index.qmd
├── data.csv
├── supplementary.json
└── images/
    └── diagram.png
```

Data files from the view's directory are copied alongside the post.

## Local Preview

```bash
cd site
quarto preview
```

Opens at `http://localhost:4321` with live reload.

## Rendering

```bash
# Render entire site
quarto render

# Render single file
quarto render posts/2026-01-10-my-post/index.qmd
```

Output goes to `_site/` directory.

## Resources

- [Quarto Documentation](https://quarto.org/docs/guide/)
- [Observable JS](https://observablehq.com/@observablehq/observable-javascript)
- [Observable Plot](https://observablehq.com/@observablehq/plot)
- [Observable Inputs](https://observablehq.com/@observablehq/inputs)
