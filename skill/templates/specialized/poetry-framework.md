# Poetry Generation Framework

For generating poetry views from idea spaces.

## Methodology: Poetic Inquiry

Poetry should emerge from the material, not be imposed on it. This framework uses the raw ideation transcripts as the source, finding the poetry latent in the human's own words.

## Process

1. **Load the idea space** - Read all transcripts, assets, README
2. **Identify emotional cores** - What moments carried the most weight?
3. **Extract key images** - Concrete, sensory language from the transcripts
4. **Find the question** - What is this idea really asking?
5. **Draft with constraints** - Apply the rules below

## Poetic Rules

### Lineation
- Each line should be able to stand somewhat alone
- Line breaks create meaning through pause and emphasis
- Avoid breaking mid-phrase unless intentional

### Language
- Prefer concrete over abstract
- Prefer specific over general
- Prefer verbs over adjectives
- No clichés; find fresh language

### Forbidden Words
Avoid these overused poetic words unless absolutely necessary:
- soul, heart, dream, silence, darkness, light (as abstractions)
- eternal, infinite, vast
- whisper, murmur, echo (unless literal)
- dance (as metaphor)

### Sound
- Read aloud; attend to rhythm
- Internal rhyme over end rhyme
- Consonance and assonance over obvious rhyme

## Structure Options

| Form | When to Use |
|------|-------------|
| Free verse | Default; follows the thought's natural shape |
| Prose poetry | When the idea resists line breaks |
| Numbered sections | For ideas with distinct phases |
| Couplets | For call-and-response or dialogue |
| Tercets | For ideas that spiral or layer |

## Output Format

```yaml
---
title: [Poem Title]
type: poem
form: [free-verse | prose-poem | sections | couplets | tercets]
source-idea: [idea folder name]
---
```

Followed by the poem itself, with clear stanza breaks.
