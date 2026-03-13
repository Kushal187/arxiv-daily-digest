# arXiv Daily Digest — Branding Kit

## Brand Identity

**Name:** arXiv Daily Digest
**Tagline:** ranked daily arxiv for ml researchers
**Voice:** Academic, minimal, tool-oriented — "a tool, not a product"

---

## Color Palette

| Swatch | Name | Hex | Usage |
|--------|------|-----|-------|
| ![#1a4b8c](https://via.placeholder.com/16/1a4b8c/1a4b8c) | **Brand Blue** | `#1a4b8c` | Primary accent, icon backgrounds, links |
| ![#edf3fb](https://via.placeholder.com/16/edf3fb/edf3fb) | **Blue Soft** | `#edf3fb` | Active states, highlights, card gradients |
| ![#1a1a1a](https://via.placeholder.com/16/1a1a1a/1a1a1a) | **Ink** | `#1a1a1a` | Primary text, dark UI elements |
| ![#555555](https://via.placeholder.com/16/555555/555555) | **Muted** | `#555555` | Secondary text, descriptions |
| ![#ffffff](https://via.placeholder.com/16/ffffff/ffffff) | **Background** | `#ffffff` | Page background |
| ![#fafaf8](https://via.placeholder.com/16/fafaf8/fafaf8) | **Surface** | `#fafaf8` | Off-white surfaces, cards |
| ![#e5e5e5](https://via.placeholder.com/16/e5e5e5/e5e5e5) | **Line** | `#e5e5e5` | Borders, dividers |
| ![#1e6a3b](https://via.placeholder.com/16/1e6a3b/1e6a3b) | **Success Green** | `#1e6a3b` | Saved states, confirmations |
| ![#c0392b](https://via.placeholder.com/16/c0392b/c0392b) | **Danger Red** | `#c0392b` | Destructive actions, errors |

---

## Typography

### Body (Serif)
```
Charter, Bitstream Charter, Source Serif 4, Iowan Old Style, Georgia, serif
```
Used for paper abstracts, body text, and long-form content. Evokes an academic journal feel.

### UI (Sans-Serif)
```
IBM Plex Sans, DM Sans, Helvetica Neue, Arial, sans-serif
```
Used for navigation, buttons, tags, metadata, and all interface chrome.

### Code / Scores (Monospace)
```
IBM Plex Mono, SFMono-Regular, Consolas, monospace
```
Used for score badges and numerical data.

---

## Logo & Icon Mark

The icon mark is a stylized document on a brand-blue rounded square. The document features a folded corner and three horizontal lines of decreasing width and opacity, representing a ranked/prioritized digest of papers.

### Assets

| File | Size | Purpose |
|------|------|---------|
| `favicon.svg` | 32x32 | Browser tab favicon |
| `apple-touch-icon.svg` | 180x180 | iOS home screen icon |
| `icon-mark.svg` | 512x512 | App icon, social profiles |
| `logo.svg` | 200x40 | Full wordmark (dark backgrounds) |
| `logo-white.svg` | 200x40 | Full wordmark (light text on dark bg) |
| `og-image.svg` | 1200x630 | Social sharing / Open Graph image |

### Icon Concept
- **Shape:** Rounded square (border-radius ~22%)
- **Fill:** Brand Blue `#1a4b8c`
- **Document:** White paper with folded corner in `#c8d8ed`
- **Text lines:** Three bars at 70%, 50%, 30% opacity — representing ranked/prioritized content
- **Lines decrease in width** — symbolizing a curated digest narrowing to what matters most

---

## Usage Guidelines

### Do
- Use the icon mark on brand blue backgrounds
- Maintain padding around the mark (minimum 25% of mark size)
- Use the serif font stack for content, sans-serif for UI
- Keep the academic, minimal aesthetic

### Don't
- Stretch or distort the icon mark
- Place the mark on busy backgrounds without sufficient contrast
- Use colors outside the defined palette for brand elements
- Add gradients or effects to the icon mark

---

## CSS Variables

All brand tokens are defined as CSS custom properties in `apps/web/app/globals.css`:

```css
:root {
  --bg: #ffffff;
  --surface: #fafaf8;
  --ink: #1a1a1a;
  --muted: #555555;
  --line: #e5e5e5;
  --soft-line: #f0f0f0;
  --accent: #1a4b8c;
  --accent-soft: #edf3fb;
  --tag-bg: #f0f0f0;
  --tag-ink: #444444;
}
```
