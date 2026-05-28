# Style Guide — Stunning Full README

Visual style specifications for generating "stunning full" README files. All rules here are mandatory unless marked "recommended".

---

## 1. Emoji Rules

### Section Header Emoji Map

| Section | Emoji |
|---------|-------|
| Features | ✨ |
| Quick Start | 🚀 |
| Installation | 📦 |
| Usage | 💡 |
| Documentation | 📚 |
| Contributing | 🤝 |
| Community | 💬 |
| Star History | ⭐ |
| Contributors | 🙏 |
| License | 📄 |
| Comparison | 🔄 |
| Roadmap | 🗺️ |
| FAQ | ❓ |
| Changelog | 📝 |
| Security | 🔒 |

Custom sections not in this table should use a single relevant emoji or none at all.

### Emoji Constraints

- **Max 1 emoji per header.** Never stack multiple emojis on a single heading.
- **No emojis in body text.** The only exception is status indicators inside tables (see Tables section).
- **No emojis inside code blocks.** Code must remain copy-pasteable without decorative characters.

---

## 2. Typography

### Horizontal Rules

- Use `---` to separate major sections.
- Always leave a blank line before and after the `---`.
- Do not use `***` or `___` as separators.

### Spacing

- Blank line before and after every `##` header.
- Blank line between paragraphs.
- No trailing whitespace on any line.
- Single newline at end of file.

### Code Blocks

- Always specify the language identifier after the opening triple backticks.
- Use ````bash` for shell commands and scripts.
- Use ````json`, ````yaml`, ````python`, etc. for their respective languages.
- Use bare ```` ``` ```` only when the content is truly generic or mixed.

### Links

- Use descriptive link text that explains the destination.
- Never use "click here", "this link", or "here" as link text.

Bad:
```
For details, click [here](https://example.com).
```

Good:
```
See the [API reference](https://example.com) for details.
```

---

## 3. Centered Elements

Use `<div align="center">` to center the following elements:

- **Logo / header block** — project logo, name, tagline.
- **Badge rows** — shields.io badges displayed in a row.
- **Language switcher** — links to alternate language versions of the README.

Rules:

- Always close with `</div>` after each centered block.
- Do not nest `<div align="center">` blocks.
- Do not center regular body content, tables, or code blocks.

Example:

```html
<div align="center">

![Logo](logo.png)

# Project Name

[![Badge](https://img.shields.io/badge/example-blue)](url)

</div>
```

---

## 4. Admonitions

Use GitHub-flavored admonition syntax. Supported types:

```markdown
> [!NOTE]
> Informational context the reader should know.

> [!TIP]
> Helpful advice or best practice.

> [!IMPORTANT]
> Critical information required for success.

> [!WARNING]
> Potential risks or negative outcomes.

> [!CAUTION]
> Actions that may lead to data loss or breaking changes.
```

### Constraints

- Max 2-3 admonitions per README. Overuse dilutes their impact.
- Place admonitions near the relevant content, not stacked at the top.
- Do not put code blocks inside admonitions (GitHub rendering is unreliable for nested fenced code).

---

## 5. Tables

### Alignment Rules

| Content Type | Alignment |
|-------------|-----------|
| Text, names, descriptions | Left |
| Status indicators, icons | Center |
| Numbers, counts, sizes | Right |

### Status Indicators

These are the only emojis permitted in body-table cells:

| Indicator | Meaning |
|-----------|---------|
| ✅ | Done / Supported |
| ❌ | Not supported / No |
| 🚧 | In Progress |
| 📋 | Planned |
| ⚠️ | Partial / Caveat |

### Table Formatting

- Always include a header row and alignment row.
- Keep column content concise; long text belongs in a paragraph above the table.
- Do not exceed 6 columns unless absolutely necessary.

---

## 6. Bilingual Format

### File Naming

| Role | Filename |
|------|----------|
| Primary language | `README.md` |
| English version | `README_EN.md` |
| Chinese version | `README_CN.md` |

### Language Switcher Placement

Place the language switcher immediately after the centered header block, before any badges.

```markdown
<div align="center">

# Project Name

</div>

[中文](README_CN.md) | [English](README_EN.md)

---

<div align="center">

[badges go here]

</div>
```

### Content Parity

- Both language versions must have the same overall structure (same sections, same order).
- Same badges in both versions.
- Same code examples — code does not change between languages.
- Technical terms (API names, library names, CLI commands) may remain in English in the Chinese version.

---

## 7. README Length Guidelines

| Project Type | Recommended Lines |
|-------------|-------------------|
| Single-file script | 50 - 100 |
| Small library | 100 - 200 |
| Medium project | 200 - 400 |
| Large framework | 400 - 600 |
| Enterprise / platform | 600 - 1000 |

These are guidelines, not hard limits. A small project with heavy documentation may exceed its range; a large project with a separate docs site may be shorter. Prioritize clarity over length.
