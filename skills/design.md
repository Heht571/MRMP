# CER-CM Frontend Design System

> Apple-inspired design language applied to a Vue 2 + Element UI admin dashboard.

---

## 1. Design Philosophy

Inspired by Apple's web design language. Core principles:

- **Minimalism**: The interface serves the content; reduce visual noise.
- **Binary Contrast**: Alternating dark (`#000000`) and light (`#f5f5f7`) sections create rhythm.
- **Single Accent Color**: Only Apple Blue (`#0071e3`) is used for interactive elements.
- **Borderless Aesthetic**: Borders are rare; hierarchy is built through whitespace and color contrast.
- **Soft Shadows**: Only one diffuse shadow is used (`rgba(0,0,0,0.22) 3px 5px 30px`).
- **Negative Tracking**: Tight letter-spacing across all text sizes for efficiency.

---

## 2. CSS Variables (Design Tokens)

Defined in `frontend/src/styles/design-system.scss` under `:root`.

### 2.1 Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg-dark` | `#000000` | Dark section backgrounds, immersive scenes |
| `--color-bg-light` | `#f5f5f7` | Light section backgrounds, information areas |
| `--color-text-light` | `#ffffff` | Text on dark backgrounds |
| `--color-text-dark` | `#1d1d1f` | Primary text on light backgrounds |
| `--color-text-secondary` | `rgba(0,0,0,0.8)` | Secondary text |
| `--color-text-tertiary` | `rgba(0,0,0,0.48)` | Tertiary / disabled text |
| `--color-accent` | `#0071e3` | Only accent: primary buttons, progress bars, active states |
| `--color-accent-hover` | `#0077ed` | Accent hover state |
| `--color-link-light` | `#0066cc` | Links on light backgrounds |
| `--color-link-dark` | `#2997ff` | Links on dark backgrounds |
| `--color-success` | `#34c759` | Success state |
| `--color-warning` | `#ff9500` | Warning state |
| `--color-danger` | `#ff3b30` | Danger / error state |
| `--color-surface-light` | `#ffffff` | Light card surface |
| `--color-surface-elevated` | `#fafafc` | Elevated surface (button backgrounds) |
| `--color-surface-dark-1` | `#272729` | Dark card background |
| `--color-surface-dark-2` | `#1d1d1f` | Dark secondary surface |
| `--color-btn-active` | `#ededf2` | Button active-state background |

### 2.2 Typography

| Token | Value |
|-------|-------|
| `--font-display` | `'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif` |
| `--font-text` | `'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif` |

> Note: Inter (loaded from Google Fonts) is used as a cross-platform substitute for SF Pro. On macOS/iOS, `-apple-system` automatically falls back to San Francisco.

### 2.3 Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-card` | `rgba(0,0,0,0.22) 3px 5px 30px 0px` | Rarely used: elevated cards, dropdowns, dialogs only |

### 2.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `5px` | Small containers, tags |
| `--radius-md` | `8px` | Buttons, cards, image containers |
| `--radius-lg` | `11px` | Search inputs, filter buttons, dropdowns |
| `--radius-xl` | `12px` | Dialogs, feature panels, drawers |
| `--radius-pill` | `980px` | Pill-shaped link CTAs |
| `--radius-circle` | `50%` | Media controls, status dots |

### 2.5 Spacing

| Token | Value |
|-------|-------|
| `--space-xs` | `4px` |
| `--space-sm` | `8px` |
| `--space-md` | `16px` |
| `--space-lg` | `24px` |
| `--space-xl` | `32px` |
| `--space-xxl` | `48px` |

### 2.6 Transitions

| Token | Value |
|-------|-------|
| `--transition-fast` | `0.15s ease` |
| `--transition-base` | `0.3s ease` |

---

## 3. Global Base Styles

```scss
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: var(--font-text);
  font-size: 14px;
  line-height: 1.5;
  letter-spacing: -0.01em;
  color: var(--color-text-dark);
  background: var(--color-bg-light);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Global typography rules:**
- Base font size: `14px`
- Line height: `1.5`
- Letter spacing: `-0.01em` (negative tracking)
- Background: `#f5f5f7`

---

## 4. Element UI Component Overrides

The system is built on Element UI 2.x, globally overridden via SCSS to match Apple's style.

### 4.1 Card

```scss
.el-card {
  background: #ffffff;
  border: none;              // borderless
  border-radius: 12px;       // --radius-xl
  color: #1d1d1f;
  box-shadow: none;          // no shadow by default
}
```

- **Borderless**: completely removes Element UI's default light-gray border.
- **Shadowless**: hierarchy is built through background contrast.
- **Radius**: `12px`.
- **Header divider**: removed.

### 4.2 Button

| Type | Background | Text | Radius | Notes |
|------|------------|------|--------|-------|
| Primary | `#0071e3` | `#ffffff` | `8px` | Hover `#0077ed`, active `#ededf2` |
| Default | `#fafafc` | `rgba(0,0,0,0.8)` | `8px` | Hover `#ededf2` |
| Text | `transparent` | `#0066cc` | — | Hover `#0071e3`, no background |
| Success | `#34c759` | `#ffffff` | `8px` | |
| Warning | `#ff9500` | `#ffffff` | `8px` | |
| Danger | `#ff3b30` | `#ffffff` | `8px` | |

- All buttons: `border: none`.
- Uniform padding: `8px 15px`.
- Font size: `14px`, weight: `400`.

### 4.3 Input

```scss
.el-input__inner {
  background: #ffffff;
  border: none;
  border-radius: 11px;       // --radius-lg
  padding: 0 14px;
  height: 36px;
  font-size: 14px;
}

.el-input__inner:focus {
  outline: 2px solid #0071e3;  // focus ring
}
```

- Borderless; focus is indicated by a focus ring (`2px solid #0071e3`).
- Select inputs add a `3px solid rgba(0,0,0,0.04)` border.

### 4.4 Table

```scss
.el-table {
  background: transparent;
  color: #1d1d1f;
  font-size: 14px;
}

.el-table th {
  background: transparent;
  color: rgba(0,0,0,0.48);   // muted header text
  font-weight: 600;
  border-bottom: none;       // remove bottom border
}

.el-table td {
  border-bottom: none;       // remove cell bottom border
  padding: 16px 0;
}

.el-table tr:hover td {
  background: #f5f5f7;       // hover highlight
}
```

- Completely borderless design.
- Headers are muted (`rgba(0,0,0,0.48)`); data rows are prominent.
- Row separation relies on whitespace, not lines.

### 4.5 Tag

```scss
.el-tag {
  background: transparent;     // no background
  border: none;
  border-radius: 5px;
  font-size: 14px;
  color: inherit;              // controlled by type classes
}
```

- No background color, no border.
- Pure text color distinguishes states: success (green), warning (orange), danger (red), info (blue).

### 4.6 Dialog

```scss
.el-dialog {
  background: #ffffff;
  border: none;
  border-radius: 12px;
  box-shadow: rgba(0,0,0,0.22) 3px 5px 30px 0px;
}
```

- Soft shadow applied.
- Title font size: `16px`, weight: `600`.

### 4.7 Dropdown / Select

```scss
.el-dropdown-menu,
.el-select-dropdown {
  background: #ffffff;
  border: none;
  border-radius: 11px;
  box-shadow: rgba(0,0,0,0.22) 3px 5px 30px 0px;
}
```

- Radius: `11px`.
- Borderless with soft shadow.

### 4.8 Progress

```scss
.el-progress-bar__outer {
  background: rgba(0,0,0,0.1);
  border-radius: 980px;        // pill shape
}

.el-progress-bar__inner {
  background: #0071e3;         // Apple Blue
  border-radius: 980px;
}
```

- Progress bar uses Apple Blue.
- Both track and fill are pill-shaped (`980px` radius).

### 4.9 Pagination

```scss
.el-pagination .el-pager li {
  background: transparent;
  color: rgba(0,0,0,0.8);
}

.el-pagination .el-pager li.active {
  color: #0071e3;              // active state uses accent color
}
```

- Page numbers have no background; active state is distinguished by color only.

### 4.10 Message

```scss
.el-message {
  background: #ffffff;
  border: none;
  border-radius: 11px;
  box-shadow: rgba(0,0,0,0.22) 3px 5px 30px 0px;
}
```

- Card-style floating layer with soft shadow.
- Borderless.

### 4.11 Form

```scss
.el-form-item__label {
  color: rgba(0,0,0,0.8);
  font-weight: 400;
  font-size: 14px;
}

.el-form-item {
  margin-bottom: 24px;
}
```

- Labels are not bold; differentiation relies on color contrast.
- Form item spacing: `24px`.

---

## 5. Custom Component Styles

### 5.1 Status Indicator

```scss
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.completed   { background: #34c759; }
.status-dot.in-progress { background: #0071e3; }
.status-dot.planning    { background: rgba(0,0,0,0.48); }
.status-dot.paused      { background: #ff9500; }
```

### 5.2 Pill Link (Apple-style CTA)

```scss
.link-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 980px;
  border: 1px solid #0066cc;
  color: #0066cc;
  font-size: 14px;
  background: transparent;
}

.link-pill:hover {
  color: #0071e3;
  border-color: #0071e3;
}
```

- Used for "Learn more" / "Details" lightweight actions.
- `980px` radius creates a capsule shape.

---

## 6. Dark Section Mode

Apply the dark theme to a section via the `.section-dark` class:

```scss
.section-dark {
  background: #000000;
  color: #ffffff;
}
```

In dark mode, child components auto-adapt:

| Component | Dark Adaptation |
|-----------|-----------------|
| Card | Background `#272729`, text white |
| Button (default) | Background `#1d1d1f`, text white |
| Button (text) | Color `#2997ff` |
| Input | Background `#272729`, text white |
| Progress track | `rgba(255,255,255,0.2)` |
| Table hover | Background `#1d1d1f` |
| Form label | `rgba(255,255,255,0.8)` |

---

## 7. Layout Principles

### 7.1 Spacing System

- Base unit: `8px`.
- Controlled by CSS variables: `--space-xs` through `--space-xxl`.
- Card padding: `24px` (desktop) / `16px` (mobile).
- Form item spacing: `24px`.

### 7.2 Containers

- No borders, no visible dividers.
- Section boundaries are built through background color differences.
- Primary radii: `8px`, `11px`, `12px`.

### 7.3 Whitespace Philosophy

- **Compact within sections**: text blocks use negative letter-spacing and tight line heights.
- **Expansive between sections**: visual rhythm is created by background color shifts (black ↔ `#f5f5f7`).

---

## 8. Responsive Adaptation

```scss
@media screen and (max-width: 768px) {
  :root {
    --space-lg: 16px;
    --space-xl: 24px;
  }

  .el-card__body {
    padding: 16px;
  }

  .el-dialog {
    width: 95% !important;
    margin-top: 5vh !important;
  }
}
```

- Breakpoint: `768px`.
- Mobile: reduced spacing, dialogs go full-width.
- Base font size remains `14px` (no scaling).

---

## 9. Usage Guidelines

### Do
- Use `#0071e3` as the only accent color.
- Maintain negative letter-spacing (`-0.01em` or tighter).
- Build hierarchy through background contrast rather than borders.
- Use only `--shadow-card` for shadows.
- Use `8px` radius for buttons, `980px` for pill links.
- Use `.section-dark` class to control dark sections uniformly.

### Don't
- Introduce additional accent colors.
- Use multiple or heavy shadows.
- Use visible borders on cards or containers.
- Use radii larger than `12px` (pill excluded).
- Forget to adapt child components inside dark sections.
