# Section Templates

Reference templates for each standard README section. Uses `{{PLACEHOLDER}}` syntax for values to be filled in by the generator.

---

## 1. Logo / Header

### Variant A: Real Logo

```markdown
<div align="center">

<img src="{{LOGO_URL}}" alt="{{PROJECT_NAME}} Logo" width="{{LOGO_WIDTH}}">

# {{PROJECT_NAME}}

{{NAV_LINKS}}

</div>
```

### Variant B: Emoji Fallback

```markdown
<div align="center">

# {{EMOJI}} {{PROJECT_NAME}}

{{NAV_LINKS}}

</div>
```

### Navigation Links Row

```markdown
[Documentation]({{DOCS_URL}}) | [Changelog]({{CHANGELOG_URL}}) | [Contributing](CONTRIBUTING.md) | [License](LICENSE)
```

**Example (Variant B):**

```markdown
<div align="center">

# 🚀 SuperTool

[Docs](https://supertool.dev/docs) | [Changelog](CHANGELOG.md) | [Contributing](CONTRIBUTING.md) | [License](LICENSE)

</div>
```

---

## 2. Language Switcher

Placed immediately after the header block. Only included in bilingual mode (`lang_mode = bilingual`).

```markdown
<div align="center">

[{{LANG_1_NAME}}]({{LANG_1_FILE}}) | [{{LANG_2_NAME}}]({{LANG_2_FILE}})

</div>
```

**Example:**

```markdown
<div align="center">

[中文](README.md) | [English](README_EN.md)

</div>
```

---

## 3. Badges Row

Centered div wrapping badge markdown. Badge definitions reference `badge-templates.md`.

```markdown
<div align="center">

{{BADGES}}

</div>
```

**Example:**

```markdown
<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/user/project/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-yellow)](https://www.python.org/)

</div>
```

---

## 4. Tagline

One sentence, under 120 characters. Three patterns to choose from:

### Pattern A: "What it is"

```
{{PROJECT_NAME}} is a {{ADJECTIVE}} {{NOUN}} for {{PURPOSE}}.
```

**Example:** `SuperTool is a lightweight CLI for managing cloud deployments.`

### Pattern B: "Action-oriented"

```
{{VERB}} your {{NOUN}} with {{PROJECT_NAME}}.
```

**Example:** `Automate your infrastructure with SuperTool.`

### Pattern C: "Problem-first"

```
Tired of {{PAIN_POINT}}? {{PROJECT_NAME}} {{SOLUTION}}.
```

**Example:** `Tired of manual deploys? SuperTool automates your entire CI/CD pipeline.`

---

## 5. Introduction (Blockquote)

Admonition blockquote format, 2-3 sentences describing core capability.

```markdown
> [!TIP]
> {{SENTENCE_1}} {{SENTENCE_2}} {{SENTENCE_3}}
```

**Example:**

```markdown
> [!TIP]
> SuperTool is an all-in-one deployment CLI that supports AWS, GCP, and Azure.
> It handles infrastructure provisioning, application deployment, and monitoring
> in a single declarative configuration file.
```

---

## 6. Features

Bullet list with bold feature names. Aim for 5-8 items.

```markdown
## ✨ Features

- **{{FEATURE_1}}** -- {{DESCRIPTION_1}}
- **{{FEATURE_2}}** -- {{DESCRIPTION_2}}
- **{{FEATURE_3}}** -- {{DESCRIPTION_3}}
- **{{FEATURE_4}}** -- {{DESCRIPTION_4}}
- **{{FEATURE_5}}** -- {{DESCRIPTION_5}}
```

**Example:**

```markdown
## ✨ Features

- **Multi-Cloud** -- Deploy to AWS, GCP, or Azure with one config
- **Rollback** -- Instant rollback to any previous deployment
- **Secrets Management** -- Built-in integration with Vault and AWS Secrets Manager
- **Monitoring** -- Real-time dashboards and alerting out of the box
- **CLI-First** -- Full control from the command line, no GUI required
```

---

## 7. Quick Start

Installation command plus a minimal working code example.

```markdown
## 🚀 Quick Start

```bash
{{INSTALL_COMMAND}}
```

```{{LANG}}
{{MINIMAL_CODE_EXAMPLE}}
```
```

**Example:**

```markdown
## 🚀 Quick Start

```bash
pip install supertool
```

```python
from supertool import deploy

deploy(config="deploy.yaml")
```
```

---

## 8. Installation

Multiple install methods and a requirements list.

```markdown
## 📦 Installation

### {{METHOD_1_NAME}}

```bash
{{METHOD_1_COMMAND}}
```

### {{METHOD_2_NAME}}

```bash
{{METHOD_2_COMMAND}}
```

### Requirements

- {{REQUIREMENT_1}}
- {{REQUIREMENT_2}}
- {{REQUIREMENT_3}}
```

**Example:**

```markdown
## 📦 Installation

### pip

```bash
pip install supertool
```

### From Source

```bash
git clone https://github.com/user/supertool.git
cd supertool
pip install -e .
```

### Requirements

- Python >= 3.8
- Docker (for container deployments)
- Cloud provider CLI configured (aws-cli, gcloud, or az)
```

---

## 9. Usage

2-3 use cases with code examples.

```markdown
## 💡 Usage

### {{USE_CASE_1_TITLE}}

```{{LANG}}
{{USE_CASE_1_CODE}}
```

### {{USE_CASE_2_TITLE}}

```{{LANG}}
{{USE_CASE_2_CODE}}
```

### {{USE_CASE_3_TITLE}}

```{{LANG}}
{{USE_CASE_3_CODE}}
```
```

**Example:**

```markdown
## 💡 Usage

### Basic Deployment

```python
from supertool import deploy

deploy(config="deploy.yaml", env="production")
```

### Rollback

```python
from supertool import rollback

rollback(version="v1.2.0")
```

### Check Status

```bash
supertool status --env production
```
```

---

## 10. Documentation

Table format with Topic and Description columns.

```markdown
## 📚 Documentation

| Topic | Description |
|-------|-------------|
| {{TOPIC_1}} | {{DESCRIPTION_1}} |
| {{TOPIC_2}} | {{DESCRIPTION_2}} |
| {{TOPIC_3}} | {{DESCRIPTION_3}} |
| {{TOPIC_4}} | {{DESCRIPTION_4}} |
```

**Example:**

```markdown
## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and first deployment |
| [Configuration](docs/configuration.md) | Full config file reference |
| [Cloud Providers](docs/providers.md) | Provider-specific setup guides |
| [API Reference](docs/api.md) | Python API documentation |
```

---

## 11. Contributing

Fork/branch/commit/PR workflow plus dev setup instructions.

```markdown
## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/{{BRANCH_NAME}}`)
3. Commit your changes (`git commit -m '{{COMMIT_MESSAGE}}'`)
4. Push to the branch (`git push origin feature/{{BRANCH_NAME}}`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/{{USERNAME}}/{{REPO}}.git
cd {{REPO}}
{{DEV_INSTALL_COMMAND}}
{{DEV_TEST_COMMAND}}
```

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.
```

**Example:**

```markdown
## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/user/supertool.git
cd supertool
pip install -e ".[dev]"
pytest
```

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.
```

---

## 12. Community

Links to community channels.

```markdown
## 💬 Community

- [Discord]({{DISCORD_URL}}) -- Join our community chat
- [GitHub Discussions]({{DISCUSSIONS_URL}}) -- Ask questions and share ideas
- [Twitter / X]({{TWITTER_URL}}) -- Follow for updates
- [Stack Overflow]({{SO_URL}}) -- Search `{{SO_TAG}}` for Q&A
```

**Example:**

```markdown
## 💬 Community

- [Discord](https://discord.gg/supertool) -- Join our community chat
- [GitHub Discussions](https://github.com/user/supertool/discussions) -- Ask questions and share ideas
- [Twitter / X](https://twitter.com/supertool) -- Follow for updates
- [Stack Overflow](https://stackoverflow.com/questions/tagged/supertool) -- Search `supertool` for Q&A
```

---

## 13. Star History

star-history.com SVG embed showing the repo's star growth chart.

```markdown
## ⭐ Star History

<a href="https://star-history.com/#{{OWNER}}/{{REPO}}&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos={{OWNER}}/{{REPO}}&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos={{OWNER}}/{{REPO}}&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos={{OWNER}}/{{REPO}}&type=Date" />
 </picture>
</a>
```

**Example:**

```markdown
## ⭐ Star History

<a href="https://star-history.com/#user/supertool&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=user/supertool&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=user/supertool&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=user/supertool&type=Date" />
 </picture>
</a>
```

---

## 14. Contributors

contrib.rocks image embed showing contributor avatars.

```markdown
## 🙏 Contributors

<a href="https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors">
 <img src="https://contrib.rocks/image?repo={{OWNER}}/{{REPO}}" />
</a>
```

**Example:**

```markdown
## 🙏 Contributors

<a href="https://github.com/user/supertool/graphs/contributors">
 <img src="https://contrib.rocks/image?repo=user/supertool" />
</a>
```

---

## 15. License

License name with link to LICENSE file.

```markdown
## 📄 License

This project is licensed under the [{{LICENSE_NAME}}](LICENSE) -- see the [LICENSE](LICENSE) file for details.
```

**Example:**

```markdown
## 📄 License

This project is licensed under the [MIT License](LICENSE) -- see the [LICENSE](LICENSE) file for details.
```

---

## 16. Comparison Table (Optional)

Feature comparison with check/cross indicators.

```markdown
## {{COMPARISON_TITLE}}

| Feature | {{PROJECT_NAME}} | {{COMPETITOR_1}} | {{COMPETITOR_2}} |
|---------|:-----------------:|:-----------------:|:-----------------:|
| {{FEATURE_1}} | {{STATUS_1A}} | {{STATUS_1B}} | {{STATUS_1C}} |
| {{FEATURE_2}} | {{STATUS_2A}} | {{STATUS_2B}} | {{STATUS_2C}} |
| {{FEATURE_3}} | {{STATUS_3A}} | {{STATUS_3B}} | {{STATUS_3C}} |
| {{FEATURE_4}} | {{STATUS_4A}} | {{STATUS_4B}} | {{STATUS_4C}} |
```

Status values: ✅ (supported), ❌ (not supported), ⚠️ (partial).

**Example:**

```markdown
## Comparison

| Feature | SuperTool | DeployX | CloudMan |
|---------|:---------:|:-------:|:--------:|
| Multi-cloud | ✅ | ✅ | ❌ |
| Rollback | ✅ | ❌ | ✅ |
| Secrets Management | ✅ | ✅ | ❌ |
| Monitoring | ✅ | ❌ | ❌ |
```

---

## 17. Roadmap (Optional)

Area/Feature/Status table for upcoming work.

```markdown
## Roadmap

| Area | Feature | Status |
|------|---------|--------|
| {{AREA_1}} | {{FEATURE_1}} | {{STATUS_1}} |
| {{AREA_1}} | {{FEATURE_2}} | {{STATUS_2}} |
| {{AREA_2}} | {{FEATURE_3}} | {{STATUS_3}} |
| {{AREA_3}} | {{FEATURE_4}} | {{STATUS_4}} |
```

Status values: ✅ Done, 🔄 In Progress, 📋 Planned.

**Example:**

```markdown
## Roadmap

| Area | Feature | Status |
|------|---------|--------|
| Cloud | Azure support | ✅ |
| Cloud | Alibaba Cloud support | 🔄 |
| CLI | Interactive mode | 📋 |
| Docs | Video tutorials | 📋 |
```

---

## 18. FAQ (Optional)

Collapsible `<details>` entries for frequently asked questions.

```markdown
## FAQ

<details>
<summary>{{QUESTION_1}}</summary>

{{ANSWER_1}}

</details>

<details>
<summary>{{QUESTION_2}}</summary>

{{ANSWER_2}}

</details>

<details>
<summary>{{QUESTION_3}}</summary>

{{ANSWER_3}}

</details>
```

**Example:**

```markdown
## FAQ

<details>
<summary>Does SuperTool support Windows?</summary>

Yes, SuperTool works on Windows, macOS, and Linux. Use `pip install supertool` on any platform.

</details>

<details>
<summary>Can I use SuperTool without Docker?</summary>

Yes, Docker is only required for container-based deployments. VM and serverless deployments work without it.

</details>

<details>
<summary>How do I report a bug?</summary>

Please open an issue on [GitHub Issues](https://github.com/user/supertool/issues) with steps to reproduce.

</details>
```
