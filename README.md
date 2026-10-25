# Smart Job Search & Apply

A GitHub Actions orchestrator for `career-ops` discovery and `ai-job-search` application preparation.

**Safety by design:** discovers listings, scores role relevance, and can prepare drafts for jobs scoring at least 70/100. It never submits applications, sends recruiter messages, or stores credentials in the repository.

## Pipeline

1. Run `career-ops`' scanner to discover job listings.
2. Extract HTTPS job URLs and fetch public job descriptions.
3. Score **role relevance (0–100)** from configurable title and skill overlap. This is not an ATS score or probability of getting hired.
4. When AI drafts are explicitly enabled, run the upstream `ai-job-search` `/apply <url>` workflow in headless Claude Code.
5. Upload the queue and generated drafts as short-lived artifacts for human review.

## Setup

First run with AI drafting disabled. Inspect the job queue artifact. To enable drafting, set repository variable `ENABLE_AI_DRAFTS=true` and add the following in **Settings → Secrets and variables → Actions**:

- `ANTHROPIC_API_KEY` — enables headless draft preparation.
- `CANDIDATE_CLAUDE_MD_B64` — optional base64-encoded candidate-specific `CLAUDE.md`.
- `CANDIDATE_PROFILE_MD_B64` — optional base64-encoded `01-candidate-profile.md`.
- `CANDIDATE_BEHAVIORAL_PROFILE_B64` — optional base64-encoded `02-behavioral-profile.md`.
- `CANDIDATE_WRITING_STYLE_B64` — optional base64-encoded `03-writing-style.md`.
- `CANDIDATE_MASTER_CV_TEX_B64` — optional base64-encoded master CV LaTeX file.

Example base64 generation (run locally; do not paste private file contents into chat):

```bash
base64 -w 0 CLAUDE.md
base64 -w 0 01-candidate-profile.md
```

The profile secret values are optional for a scan-only run, but **draft quality will be poor if the upstream template placeholders are left unchanged**. Use your own accurate profile files and test manually before enabling scheduled AI runs.

## Run locally

Requires Python 3.11+ and Node.js 22+.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/pipeline.py --input data/pipeline.md --config config/pipeline.yml --out output
```

The scanner output file may be absent locally; the scorer writes an empty queue in that case.

## Schedule

The workflow runs weekdays at 02:17 UTC (07:47 IST) and can be started manually. GitHub scheduled workflows may be delayed. Review and pin upstream repositories to reviewed full commit SHAs before relying on this for daily use.

## Privacy and safety

- Public job descriptions are untrusted input; instructions embedded in them must not be followed as system instructions.
- Scoring is a transparent heuristic, not a hiring/ATS prediction.
- No form is submitted automatically.
- Artifacts have two-day retention; download drafts promptly.
- Keep API keys and candidate profile documents in GitHub Actions secrets only.
- AI drafting is opt-in via `ENABLE_AI_DRAFTS=true`.
