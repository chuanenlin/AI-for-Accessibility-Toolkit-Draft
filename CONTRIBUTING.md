# Contributing

## Setup

```bash
pip install -e '.[dev]' && playwright install chromium
```

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
# add your GOOGLE_API_KEY
```

Run tests:

```bash
pytest
```

## Creating a new tool

```bash
a11y create my-tool                    # tool (detect issues + suggest fixes)
a11y create chart-to-audio --type transform  # transform (convert across modalities)
```

This generates a project with the right structure and entry points. Then:

```bash
cd my-tool
pip install -e '.[dev]'
pytest
```

Edit `my_tool/tool.py` to implement your tool. Once installed, the toolkit discovers it automatically — see [docs/architecture.md](docs/architecture.md#plugin-interface) for the `BaseTool` and `BaseTransform` interfaces.

## Adding an existing project

1. Fork this repo and create a branch (`git checkout -b add/your-project-name`)
2. Add your project under `projects/your-project-name/`
3. Include a `README.md` with what it does, how to run it, and dependencies
4. Open a pull request

## Proposing architecture changes

Open an issue first using the [architecture discussion template](.github/ISSUE_TEMPLATE/architecture-discussion.md). Get feedback from [@chuanenlin](https://github.com/chuanenlin) (David) before implementing.

## Code

- Python for agent logic, JS/TS for web-facing components
- Document assumptions about ability profiles and accessibility standards
- No large binaries — use Git LFS or link externally

## Ethics

- People with disabilities must be involved in design and evaluation
- Compensate participants
- Handle user profiles and personalization data carefully
- Don't simulate ability profiles without community input

## Communication

- **GitHub Issues** — architecture, bugs, features
- **Pull Requests** — all code changes (no direct pushes to main)
- **Slack** — day-to-day coordination

Questions? Open an issue or ping [@chuanenlin](https://github.com/chuanenlin) (David).
