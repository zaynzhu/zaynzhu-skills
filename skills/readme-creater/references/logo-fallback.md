# Logo Fallback Rules

When no logo or banner image is detected in a project, use the following rules to select a fallback emoji for the README header.

---

## Language-to-Emoji Mapping

| Language       | Emoji |
|----------------|-------|
| Python         | 🐍    |
| JavaScript     | ⚡    |
| TypeScript     | 💎    |
| Rust           | 🦀    |
| Go             | 🔵    |
| Java           | ☕    |
| Ruby           | 💎    |
| PHP            | 🐘    |
| C#             | 💜    |
| C++            | ⚙️    |
| Swift          | 🦅    |
| Kotlin         | 🟣    |
| Dart           | 🎯    |
| Lua            | 🌙    |
| R              | 📊    |
| Julia          | 🔷    |
| Zig            | ⚡    |
| Elixir         | 💧    |
| Multi-language | 🌐    |
| Unknown        | 📦    |

---

## Category-Based Emoji (Alternative)

Use when the project type is identifiable but the language is not the primary signal.

| Category          | Emoji |
|-------------------|-------|
| Web Framework     | 🌐    |
| CLI Tool          | 🖥️    |
| API               | 🔌    |
| Database          | 🗄️    |
| AI/ML             | 🤖    |
| Chat Bot          | 💬    |
| Game              | 🎮    |
| Mobile App        | 📱    |
| Browser Extension | 🧩    |
| DevOps Tool       | 🔧    |
| Security Tool     | 🔒    |
| Data Tool         | 📊    |
| Documentation     | 📖    |
| Testing Tool      | 🧪    |

---

## Full Header Template

Use a centered `<div>` block containing the emoji, project name, tagline, and navigation links.

```html
<div align="center">

{emoji} **{project-name}**

{one-line tagline}

[Docs](link) | [Install](link) | [Changelog](link)

</div>
```

### Example (Python project)

```html
<div align="center">

🐍 **my-tool**

A fast CLI utility for processing data.

[Docs](https://example.com/docs) | [Install](#installation) | [Changelog](#changelog)

</div>
```

---

## ASCII Art Banner (Optional)

Use only for personal or brand projects where a distinctive header is desired.

Guidelines:
- Maximum 6 lines of ASCII art.
- Must render correctly in monospace fonts.
- Wrap in `<pre>` tags to preserve formatting.
- Place above the project name in the header.

### Example

```html
<div align="center">

<pre>
 ___
|   |___
|  _   _|
|_| |_|_|
</pre>

🐍 **my-tool**

A fast CLI utility for processing data.

[Docs](https://example.com/docs) | [Install](#installation)

</div>
```

---

## Decision Flow

Use this flow to pick the fallback emoji:

1. **Has logo or banner image?**
   - Yes -> Use the real logo. No emoji fallback needed.
2. **Is the primary language identifiable?**
   - Yes -> Use the corresponding emoji from the Language-to-Emoji Mapping table.
3. **Is the project category identifiable?**
   - Yes -> Use the corresponding emoji from the Category-Based Emoji table.
4. **Default**
   - Use 📦 as the fallback emoji.
