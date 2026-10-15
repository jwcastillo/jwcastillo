<picture>
  <source media="(prefers-color-scheme: dark) and (max-width: 640px)" srcset="assets/waterfall-dark-narrow.svg">
  <source media="(prefers-color-scheme: light) and (max-width: 640px)" srcset="assets/waterfall-light-narrow.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/waterfall-dark.svg">
  <img alt="Wen Castillo's GitHub profile loading as a Chrome DevTools network waterfall: performance engineer in Santiago, Chile; k6 load testing; Core Web Vitals budgets; AI agent skill audits with NVIDIA SkillSpector; merged upstream fixes." src="assets/waterfall-light.svg" width="100%">
</picture>

### Request headers

```http
GET /jwcastillo HTTP/2
host: github.com
x-role: performance engineer
x-location: Santiago, Chile
accept: k6, core-web-vitals, clean-architecture, test-first
x-also: AI agent tooling (Claude Code, Codex, OpenCode, Gemini CLI)
```

I measure before I claim. I load test with k6, keep Core Web Vitals inside their budgets, design systems with Clean and Hexagonal Architecture, and audit AI agent skills with [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector) before sending the fixes upstream.

### Response · `upstream-prs.json`

- `200 merged` [NVIDIA/SkillSpector#645](https://github.com/NVIDIA/SkillSpector/pull/645): removed three classes of analyzer false positives.
- `200 merged` [wshobson/agents#765](https://github.com/wshobson/agents/pull/765): restricted CORS origins and made the FastAPI template run end to end.
- `200 merged` [wshobson/agents#766](https://github.com/wshobson/agents/pull/766) · [#767](https://github.com/wshobson/agents/pull/767) · [#768](https://github.com/wshobson/agents/pull/768): brought the monorepo, end-to-end testing and Git workflow skills up to current tool behavior.
- `200 merged` [sickn33/agentic-awesome-skills#1929](https://github.com/sickn33/agentic-awesome-skills/pull/1929): moved the web performance skill to INP and fixed its tree-shaking and image advice.
- `200 merged` [JuliusBrussee/caveman#1234](https://github.com/JuliusBrussee/caveman/pull/1234): documented that `/caveman-compress` sends the file to the model provider.

### Sources

- [**k6-enterprise-framework**](https://github.com/jwcastillo/k6-enterprise-framework): a TypeScript k6 load testing framework with a two-layer architecture, observability and multi-client isolation.

### Timing

Editor LazyVim · multiplexers tmux and Zellij · agents Claude Code, Codex, OpenCode and Gemini CLI.

### Initiator

Need a load test, a Core Web Vitals budget or a second look at an agent setup? [Say hi on LinkedIn](https://cl.linkedin.com/in/jwcastillo/).

<sub>The waterfall is a metaphor: the timings are illustrative, the links are real.</sub>
