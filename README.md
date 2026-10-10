# ramen-demo-mcp-group

A ready-to-connect **group repo** for [Ramen](https://github.com/bkraad47/ramen). Point a Ramen group at this repo, click Deploy, and you get one tool, one resource and one prompt.

## Layout (the Ramen group contract)
```
mcp/
  requirements.txt                       pip requirements for the worker
  tools/<name>/<name>.py                 callable code (utils/ is importable)
  tools/<name>/<name>.json               proto: type, name, callable, input, output, error
  tests.yaml                             golden tools/call cases the console runs on the canary (optional)
  guardrails.yaml + guardrails/          per-tool pre/post rails: NeMo config or your own policy.py (optional, 0.7.5)
  resources/<name>/<name>.py + .json     same shape, plus uri and mime_type
  prompts/<name>/<name>.json             + SKILL.md (agent-skills template) + settings.json
```
Rules: folder name == json `name` == file stem; json `type` must match its folder; `type` ∈ {tool, resource, prompt}.
Secrets are referenced in code as `{{$group_name.secret_var}}` and resolved by the worker at call time.

`mcp/env.yaml` (or `mcp/.env`) is the group's environment: flat `KEY: value` lines the worker exports to the Python
runtime at load, with `{{$group.SECRET}}` references rendered from the group's secrets (Ramen 0.6.0). Tool code reads
`os.environ["DEMO_MODE"]`; the worker's own cloud identity (its GCP service account / AWS role, with the permissions
approved on the console) is what the code runs as, so cloud SDKs need no keys.

## What is in it (0.7.5)
| Kind | Name | Does |
|---|---|---|
| tool | `demo_calculator_tool` | add, subtract, multiply, divide two numbers; divide by zero is a tool error |
| tool | `word_count` | characters, words and lines of a text, returned as an object (`structuredContent`) |
| tool | `unit_convert` | length, mass and temperature conversions; unknown or mixed units are a tool error |
| resource | `demo_readme` | this README |
| prompt | `get_calculation_prompt` | guides an agent to use the calculator |

Every tool proto declares `output`; Ramen 0.7.0 publishes it as the MCP `outputSchema` and the worker validates the
result against it. Descriptions say what the tool returns, what fails and when to use it, which is what tool-quality
scorers (Glama's TDQS) and models read.

`mcp/tests.yaml` holds **golden cases**: the console runs them against the canary before the stable workers take the
new code, and a failing case aborts the deploy (Ramen 0.7.0). `VERSION` names the Ramen release this repo was last
verified with; the repo is tagged with the same `v<version>`.

## Guardrails (0.7.5)
`mcp/guardrails.yaml` opts `word_count` (pre and post) and `demo_calculator_tool` (pre) into NeMo Guardrails, with the
rails in `mcp/guardrails/` (`config.yml`, `rails.co`, `actions.py`). The worker runs the input rail on the arguments
before the tool and the output rail on the result after the schema check; a blocked call comes back as a tool error
`guardrail blocked: pre: …` (never as a stack trace, never with the output). The demo rails are deterministic — a
prompt-injection phrase in the input, the word "secret" in the output — so they cost nothing; add `models:` to
`config.yml` and an API key to `mcp/env.yaml` for NeMo's LLM-backed self-check flows. `fail: closed` means a rail
that errors or times out blocks the call. The golden cases in `mcp/tests.yaml` run through the rails too.

## Try it
1. Deploy Ramen (see its README).
2. Create a group, set its repo to `https://github.com/bkraad47/ramen-demo-mcp-group`.
3. Deploy, then call `demo_calculator_tool` with `{"var1": 2, "var2": 3, "func": "add"}` from any MCP client.

## Deploy on push (GitHub Actions)
`.github/workflows/ramen-deploy.yml` asks a Ramen console to deploy this group when `mcp/` changes on `main` and
fails the run if the deploy fails. Set the repo variable `RAMEN_URL` and the secret `RAMEN_API_KEY` (an `rmn_` key,
Group Admin of this group) to turn it on; without them it does nothing. Guide:
[Deploy from GitHub Actions](https://bkraad47.github.io/ramen/wiki/deploy-github-actions/).
