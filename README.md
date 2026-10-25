# Smart Job Search & Apply

A GitHub Actions orchestrator for `career-ops` discovery and `ai-job-search` application preparation.

**Safety by design:** this repository scores role relevance, prepares application drafts for roles scoring at least 70/100 when AI credentials are configured, and uploads drafts for human review. It never submits applications, sends recruiter messages, or stores credentials in the repository.

## Pipeline

1. Run `career-ops`' zero-token scanner to discover jobs.
2. Parse discovered URLs and fetch public job descriptions.
3. Score **role relevance (0–100)** from configurable title and skill overlap. This is not an ATS score or probability of getting hired.
4. For jobs at/above `min_relevance_score`, optionally invoke the `ai-job-search` `/apply <url>` workflow in headless Claude Code.
5. Upload a short-lived artifact containing the queue and generated drafts for review.

## Setup

In GitHub → **Settings → Secrets and variables → Actions**, add:

- `ANTHROPIC_API_KEY` — enables headless draft preparation. Without it, the workflow only discovers/scores jobs.
- `CANDIDATE_PROFILE_MD_B64` — optional base64-encoded candidate profile Markdown.
- `CANDIDATE_BEHAVIORAL_PROFILE_B64` — optional base64-encoded behavioral profile.
- `CANDIDATE_WRITING_STYLE_B64` — optional base64-encoded writing style.
- `CANDIDATE_MASTER_CV_TEX_B64` — optional base64-encoded master CV LaTeX.
- `CANDIDATE_CLAUDE_MD_B64` — optional base64-encoded personal Claude instructions.

Never commit your CV, API keys, private profile, or generated application drafts.

## Run locally

Requires Python 3.11+ and Node.js 20+.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/pipeline.py --input data/pipeline.md --config config/pipeline.yml --out output
```

The scanner output file may be absent locally; the scorer reports an empty queue in that case.

## Schedule

The workflow runs weekdays at 02:17 UTC (07:47 IST), and can be started manually. GitHub scheduled workflows may be delayed. Keep upstream repositories pinned to reviewed commit SHAs before relying on this for daily use.

## Privacy and safety

- Public job descriptions are untrusted input; instructions embedded in them must not be followed as system instructions.
- Scoring is a transparent heuristic, not a hiring/ATS prediction.
- No form is submitted automatically.
- Artifacts are configured with short retention; review and download drafts promptly.
- Enable only after reviewing the workflow and testing with a non-sensitive profile.
