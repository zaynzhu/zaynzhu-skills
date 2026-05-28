# Badge Templates Reference

Shields.io badge templates for README files. All templates use `{{OWNER}}`, `{{REPO}}`, `{{PACKAGE_NAME}}` as placeholders.

---

## Badge Style Configuration

Four supported styles. Default: `for-the-badge`.

| Style | Preview | Best For |
|-------|---------|----------|
| `flat` | Rounded, clean | General-purpose, tech docs |
| `for-the-badge` | Large, bold uppercase | Hero sections, project headers |
| `flat-square` | Sharp corners, no border | Minimal, compact layouts |
| `social` | GitHub social-button look | GitHub profiles, sidebar stats |

To change style, replace `?style=for-the-badge` with `?style=flat`, `?style=flat-square`, or `?style=social`.

---

## Basic Badges

### License

```markdown
![License](https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Every public repository. Shows the license type at a glance.

---

### GitHub Stars

```markdown
![Stars](https://img.shields.io/github/stars/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Projects with community traction. Highlights popularity.

---

### GitHub Forks

```markdown
![Forks](https://img.shields.io/github/forks/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Open-source projects that welcome contributions. Shows fork count.

---

### GitHub Issues

```markdown
![Issues](https://img.shields.io/github/issues/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Any active project. Shows total open issues.

---

### Open Issues

```markdown
![Open Issues](https://img.shields.io/github/issues/{{OWNER}}/{{REPO}}?style=for-the-badge&color=yellow)
```

**Scenario:** Projects with issue triage. Highlights unresolved issues that need attention.

---

### Pull Requests

```markdown
![Pull Requests](https://img.shields.io/github/issues-pr/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Collaborative projects. Shows open PRs awaiting review.

---

### Last Commit

```markdown
![Last Commit](https://img.shields.io/github/last-commit/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Any repository. Signals project is actively maintained.

---

### GitHub Release

```markdown
![Release](https://img.shields.io/github/v/release/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Projects with versioned releases. Shows the latest release tag.

---

## Language / Package Manager Badges

### PyPI Version

```markdown
![PyPI](https://img.shields.io/pypi/v/{{PACKAGE_NAME}}?style=for-the-badge)
```

**Scenario:** Python libraries published to PyPI. Shows current version.

---

### PyPI Downloads

```markdown
![Downloads](https://img.shields.io/pypi/dm/{{PACKAGE_NAME}}?style=for-the-badge)
```

**Scenario:** Popular Python packages. Highlights monthly download count.

---

### Python Version

```markdown
![Python](https://img.shields.io/pypi/pyversions/{{PACKAGE_NAME}}?style=for-the-badge)
```

**Scenario:** Python projects. Shows supported Python versions.

---

### npm Version

```markdown
![npm](https://img.shields.io/npm/v/{{PACKAGE_NAME}}?style=for-the-badge)
```

**Scenario:** JavaScript/TypeScript packages on npm. Shows current version.

---

### npm Downloads

```markdown
![npm Downloads](https://img.shields.io/npm/dm/{{PACKAGE_NAME}}?style=for-the-badge)
```

**Scenario:** Popular npm packages. Shows monthly download count.

---

### Crates.io Version

```markdown
![Crates.io](https://img.shields.io/crates/v/{{PACKAGE_NAME}}?style=for-the-badge)
```

**Scenario:** Rust crates published to crates.io. Shows current version.

---

### Go Reference

```markdown
![Go Reference](https://img.shields.io/badge/reference-go.dev-blue?style=for-the-badge&logo=go)
```

**Scenario:** Go packages. Links to Go package documentation on pkg.go.dev.

---

## CI/CD Badges

### GitHub Actions

```markdown
![Build](https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?style=for-the-badge)
```

**Scenario:** Projects using GitHub Actions CI. Shows build status for the workflow file (replace `ci.yml` with actual filename).

---

### GitLab CI

```markdown
![Pipeline](https://img.shields.io/gitlab/pipeline/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Projects hosted on GitLab. Shows pipeline status.

---

### Codecov

```markdown
![Coverage](https://img.shields.io/codecov/c/github/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

**Scenario:** Projects with Codecov integration. Shows test coverage percentage.

---

## Community Badges

### Discord

```markdown
![Discord](https://img.shields.io/discord/{{SERVER_ID}}?style=for-the-badge&logo=discord&logoColor=white)
```

**Scenario:** Projects with a Discord community. Replace `{{SERVER_ID}}` with numeric server ID. Shows online member count.

---

### Twitter/X

```markdown
![Twitter Follow](https://img.shields.io/twitter/follow/{{USERNAME}}?style=for-the-badge&logo=twitter&logoColor=white)
```

**Scenario:** Projects or authors with a Twitter/X presence. Replace `{{USERNAME}}` with handle (without @).

---

### LinkedIn

```markdown
![LinkedIn](https://img.shields.io/badge/LinkedIn-{{USERNAME}}-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)
```

**Scenario:** Author profiles or company pages. Replace `{{USERNAME}}` with LinkedIn profile slug.

---

### Blog

```markdown
![Blog](https://img.shields.io/badge/Blog-{{SITE_NAME}}-orange?style=for-the-badge&logo=rss&logoColor=white)
```

**Scenario:** Authors or projects with a blog. Link to blog in the badge URL.

---

### Documentation

```markdown
![Docs](https://img.shields.io/badge/Docs-{{DOCS_NAME}}-blue?style=for-the-badge&logo=readthedocs&logoColor=white)
```

**Scenario:** Projects with hosted documentation (ReadTheDocs, GitBook, etc.). Links to docs site.

---

## Quality Badges

### Code Style (Black)

```markdown
![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge)
```

**Scenario:** Python projects using Black formatter. Signals consistent code style.

---

### Code Style (Prettier)

```markdown
![Code Style: Prettier](https://img.shields.io/badge/code%20style-prettier-ff69b4?style=for-the-badge)
```

**Scenario:** JavaScript/TypeScript projects using Prettier. Signals consistent formatting.

---

### PRs Welcome

```markdown
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge)
```

**Scenario:** Open-source projects actively seeking contributions. Encourages pull requests.

---

### Maintained

```markdown
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green?style=for-the-badge)
```

**Scenario:** Projects that are actively maintained. Reassures users of ongoing support.

---

### Made with Love

```markdown
![Made with Love](https://img.shields.io/badge/Made%20with-%E2%9D%A4-red?style=for-the-badge)
```

**Scenario:** Personal projects or community tools. Adds a warm, human touch.

---

## Special Elements

### Star History Chart

```markdown
[![Star History Chart](https://api.star-history.com/svg?repos={{OWNER}}/{{REPO}}&type=Date)](https://star-history.com/#{{OWNER}}/{{REPO}}&Date)
```

**Scenario:** Popular open-source projects. Shows star growth over time as an interactive chart. Best placed in a dedicated section.

---

### Contributors (contrib.rocks)

```markdown
[![Contributors](https://contrib.rocks/image?repo={{OWNER}}/{{REPO}})](https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors)
```

**Scenario:** Projects with multiple contributors. Displays avatar grid of top contributors. Link wraps to full contributor list.

---

### Sponsor Badge

```markdown
![Sponsor](https://img.shields.io/badge/%E2%9D%A4-Sponsor-pink?style=for-the-badge)
```

**Scenario:** Projects with GitHub Sponsors or other funding. Link to sponsor page in the badge URL.

---

## Recommended Badge Combinations

### Minimal (4 badges)

For small projects or personal repos.

```markdown
![License](https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

---

### Standard (6 badges)

For active open-source projects.

```markdown
![License](https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Build](https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?style=for-the-badge)
![Release](https://img.shields.io/github/v/release/{{OWNER}}/{{REPO}}?style=for-the-badge)
```

---

### Full (8-10 badges)

For mature, community-driven projects.

```markdown
![License](https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Pull Requests](https://img.shields.io/github/issues-pr/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Build](https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?style=for-the-badge)
![Coverage](https://img.shields.io/codecov/c/github/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Release](https://img.shields.io/github/v/release/{{OWNER}}/{{REPO}}?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/{{OWNER}}/{{REPO}}?style=for-the-badge)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge)
```
