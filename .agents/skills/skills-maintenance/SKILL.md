---
name: skills-maintenance
description: Use when auditing and improving skill definitions, triggers, references, naming, and progressive-disclosure hygiene.
---

# Skills Maintenance Skill

## Purpose

The skills maintenance skill provides a structured workflow for auditing and improving the existing skills in the repository. As the project evolves, skill definitions, triggers, and references can drift out of sync. This skill allows a dedicated agent to:

1. Enumerate all skills in `.agents/skills`.
2. Verify that each `SKILL.md` has a unique, descriptive `name` and `description` with no project prefixes or redundant namespaces.
3. Review the `trigger` or usage instructions for clarity and conflict with other skills.
4. Check that each skill’s references in root `AGENTS.md`, nested `AGENTS.md` overrides, relevant docs, and any skill-local reference files are correct, concise, and up to date.
5. Recommend or apply updates to skill metadata, `agents/openai.yaml`, or content, subject to review.
6. Propose new skills when repeated patterns or workflows emerge.
7. Remove obsolete or duplicated skill files.
8. Prefer existing system/plugin/curated capabilities when they remove repo-local complexity; avoid adding new repo-local skill surface when a stable out-of-the-box capability already fits.
9. Use a stricter audit tool in addition to `agent-skills-lint` when the repo needs deeper checks for `agents/openai.yaml`, unreferenced scripts, or imported-skill adaptation work.

## Usage

Invoke this skill when you need to audit the skills catalog or when a retrospective identifies skill confusion or duplication. The skills maintenance agent should operate in read–write mode only when explicitly permitted by the coordinator. Otherwise, it should report suggested changes for a human or implementer agent to apply.
Audit skill entrypoints for explicit batch-reasoning-before-tools cues, Spark-first bounded delegation, and bounded child-worker fan-out when a workflow branches.

## Guidelines

* **Naming**: Skill names must be short and descriptive (e.g., `django-feature`, `taskmaster`, `release-manager`). Avoid prefixes like `libraryops-`.
* **Triggers**: The `description` should state when to use the skill. Each skill should have unique trigger phrases to reduce ambiguity.
* **Discovery**: Skill selection should be capability-based. Prefer the skill whose
  trigger and workflow best match the task, not the one with the most familiar
  name or prefix.
* **Lint scope**: Keep `skills:lint` scoped to skill entrypoints only
  (`.agents/skills/*/SKILL.md` or an equivalent entrypoint-only finder). Do not
  broaden linting to reference markdown or other leaf docs.
* **Progressive disclosure**: Use references and scripts to avoid one giant file, but do not optimize for thinness. Important recurring workflows should keep enough top-level context that Codex does not repeatedly miss the right path.
  When a workflow branches, keep the entrypoint explicit about the bounded child-worker handoff instead of flattening the guidance into a wider local pass.
* **References**: Keep reference files only when they provide concrete progressive-disclosure material linked from `SKILL.md`; remove placeholder-only reference directories and avoid separate leaf docs when the `SKILL.md` can hold the durable guidance directly.
* **Metadata richness**: Add `agents/openai.yaml` when it improves discovery, default prompting, or machine-readable dependency declaration.
* **Out-of-the-box first**: Before adding a new repo-local skill, check whether an existing system/plugin/curated skill already covers the need well enough.
* **Review**: Summarize the outcome of each maintenance session, including the number of skills audited, changes proposed or made, and any outstanding follow‑ups.

## Completion criteria

* Every skill has a unique, descriptive name.
* No skill names have unnecessary project prefixes.
* Each skill has clear triggers and usage instructions.
* The skills catalog has no duplicate directories or files.
* Any recommended changes are either applied or documented for follow‑up.
