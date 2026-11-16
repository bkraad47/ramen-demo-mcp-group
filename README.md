# ramen-demo-mcp-group

A ready-to-connect **group repo** for [Ramen](https://github.com/bkraad47/ramen). Point a Ramen group at this repo, click Deploy, and you get one tool, one resource and one prompt.

## Layout (the Ramen group contract)
```
mcp/
  requirements.txt                       pip requirements for the worker
  tools/<name>/<name>.py                 callable code (utils/ is importable)
  tools/<name>/<name>.json               proto: type, name, callable, input, output, error (+ "task": true)
  tests.yaml                             golden tools/call cases the console runs on the canary (optional)
  evals/promptfooconfig.yaml             promptfoo evals the console runs on the canary after the golden cases (optional, 1.0.0c)
  skills/<name>/SKILL.md                 agent skills shipped with the group, scanned by SkillSpector on deploy (optional, 1.0.0c)
  llm-config/manifest.yaml + fragments   initial LLM client configs every member accepts at sign-in (optional, 1.0.0c Phase 3)
  guardrails.yaml + guardrails/          per-tool pre/post rails: NeMo config or your own policy.py (optional, 0.7.5)
  resources/<name>/<name>.py + .json     same shape, plus uri and mime_type
  prompts/<name>/<name>.json             + SKILL.md (agent-skills template) + settings.json
  apps/<name>/index.html + app.yaml      MCP Apps: HTML a host renders next to a tool's result; a tool names it with "ui" (optional, 1.0.0c)
```
Rules: folder name == json `name` == file stem; json `type` must match its folder; `type` ∈ {tool, resource, prompt}.
Secrets are referenced in code as `{{$group_name.secret_var}}` and resolved by the worker at call time.

`mcp/env.yaml` (or `mcp/.env`) is the group's environment: flat `KEY: value` lines the worker exports to the Python
runtime at load, with `{{$group.SECRET}}` references rendered from the group's secrets (Ramen 0.6.0). Tool code reads
`os.environ["DEMO_MODE"]`; the worker's own cloud identity (its GCP service account / AWS role, with the permissions
approved on the console) is what the code runs as, so cloud SDKs need no keys.

## What is in it (1.0.0)
| Kind | Name | Does |
|---|---|---|
| tool | `demo_calculator_tool` | add, subtract, multiply, divide two numbers; divide by zero is a tool error |
| tool | `word_count` | characters, words and lines of a text, returned as an object (`structuredContent`) |
| tool | `unit_convert` | length, mass and temperature conversions; unknown or mixed units are a tool error |
| tool | `confirm_delete_note` | asks the user to confirm before deleting a demo note (MCP 2026-07-28 elicitation); declining is a normal result |
| tool | `slow_report` | takes up to 30 s and reports progress; runs as a task for clients that support MCP tasks |
| resource | `demo_readme` | this README |
| prompt | `get_calculation_prompt` | guides an agent to use the calculator |

Every tool proto declares `output`; Ramen 0.7.0 publishes it as the MCP `outputSchema` and the worker validates the
result against it. Descriptions say what the tool returns, what fails and when to use it, which is what tool-quality
scorers (Glama's TDQS) and models read.

`mcp/tests.yaml` holds **golden cases**: the console runs them against the canary before the stable workers take the
new code, and a failing case aborts the deploy (Ramen 0.7.0). `VERSION` names the Ramen release this repo was last
verified with; the repo is tagged with the same `v<version>`.

## Skills and scans (1.0.0c)
`mcp/skills/noodle-math/SKILL.md` is a small agent skill that uses the three tools by name. When the console runs
[NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector) (chart `skillspector.engine: skillspector`), every deploy
scans `mcp/skills/*` plus a skill synthesized from the tools and prompts the zone serves, records the risk score on the
deploy job and keeps the report on a page per zone; "Gate deploys on scans" on the group page turns a `DO_NOT_INSTALL`
into a failed deploy. An optional `mcp/skillspector-baseline.yaml` suppresses findings you have reviewed.

## LLM configs (1.0.0c)
`mcp/llm-config/manifest.yaml` names the client config fragments next to it and where each lands on a member's machine:
a Claude Code `settings.json` fragment (an `env` entry, a `permissions.deny` of `Bash(curl *)`, a `SessionStart` hook
running `ramen-mcp-bridge policy check`), two lines of `CLAUDE.md` guidance, a Cursor rule, a Codex `[ramen]` table and a
VS Code setting. The console validates the directory on every deploy (a hook that is not `ramen-mcp-bridge …`, an
`apiKeyHelper`, an `*_API_KEY` key fail the deploy with the key named) and versions it; every person who signs in to
the group — OAuth consent page, password or magic link, the bridge — reads the files verbatim and accepts them once per
version before a token or key is handed out, and the workers refuse calls that do not carry the accepted version
(`-32028`). The bridge writes each target as `merge` says (`deep`, `block`, `replace`, `keys`), fills in
`${RAMEN_GROUP}`, `${RAMEN_HOST}` and the telemetry endpoint, and `ramen-mcp-bridge policy remove` reverts every write.
Guide: [LLM configs](https://bkraad47.github.io/ramen/wiki/llm-configs/).

## Iris example (1.0.0c)
One small data set, every 1.0.0c surface (Ramen CONTRACTS §33.3):

| Kind | Name | Does |
|---|---|---|
| resource | `iris_csv` | `ramen://demo/iris.csv`, the public-domain Iris data, 150 rows, `text/csv` |
| tool | `iris_describe` | row count and per-column count/mean/std/min/max (pandas) |
| tool | `iris_outliers` | `{column, z}`: rows whose \|z-score\| exceeds `z`; at most `IRIS_MAX_ROWS` rows (default 50), `total` and `truncated` say what was cut |
| tool | `iris_group_means` | `{by: species}`: per-species means and counts; carries the `iris_chart` MCP App |
| tool | `iris_report` | `{question}`: a short prose report from pandas; behind the LLM rails of [LLM rails (1.0.0c)](#llm-rails-100c) |
| prompt | `iris_analysis` | SKILL.md + settings: describe → outliers → group means, "never fabricate numbers", `allowed_tools` |
| app | `mcp/apps/iris_chart/` | `index.html` + `app.yaml`: a self-contained inline-SVG bar chart of the group means, served as `ui://demo/iris_chart`, fed over the MCP Apps `postMessage` bridge (`ui/initialize`, `ui/notifications/tool-result`); no external scripts |
| skill | `mcp/skills/iris-analyst/` | Skills over MCP: names the three tools, quotes only what they return |

- `mcp/requirements.txt` pins `pandas`; a cloud deployment with a builder bakes it into the worker image on deploy.
- `mcp/env.yaml` sets `IRIS_MAX_ROWS: "{{$demo.IRIS_MAX_ROWS}}"`: a group secret of that name raises the tool's cap
  (unset = 50), which re-proves the environment-secrets path on every deploy.
- `mcp/guardrails.yaml` puts `iris_outliers` behind a post rail (`block outlier dump` in `mcp/guardrails/`): a result
  above 50 rows, a row whose measurement cells are not numbers, or anything that is not the tool's JSON is refused as
  `guardrail blocked: post: …`. The rail's ceiling is fixed at 50 while the tool honours `IRIS_MAX_ROWS`, so set the
  secret to `150` and call `iris_outliers` with `z` `0.001` to see a 150-row result refused.
- Golden cases (`mcp/tests.yaml`): describe counts 150, outliers for `sepal_width` at `z` 2.5 finds two rows, group
  means has three species. Evals (`mcp/evals/promptfooconfig.yaml`): the same three through the deployed worker.
- Unit tests: `tests/test_iris.py` checks the tools, the CSV and the rail without Ramen —
  `uv run --with pandas --with pytest python -m pytest tests`.
- SkillSpector 2.13.4 (static scan) reports the skill and the app SAFE with no findings, so there is no
  `mcp/skillspector-baseline.yaml`; add one (`skillspector baseline <dir> -o mcp/skillspector-baseline.yaml`) if a
  later version or an LLM-backed scan flags the app's inline script.

## Guardrails (0.7.5)
`mcp/guardrails.yaml` opts `word_count` (pre and post) and `demo_calculator_tool` (pre) into NeMo Guardrails, with the
rails in `mcp/guardrails/` (`config.yml`, `rails.co`, `actions.py`). The worker runs the input rail on the arguments
before the tool and the output rail on the result after the schema check; a blocked call comes back as a tool error
`guardrail blocked: pre: …` (never as a stack trace, never with the output). The demo rails are deterministic — a
prompt-injection phrase in the input, the word "secret" in the output — so they cost nothing. `fail: closed` means a
rail that errors or times out blocks the call. The golden cases in `mcp/tests.yaml` run through the rails too.

## LLM rails (1.0.0c)
Two tools add rails that ask a model (Ramen CONTRACTS §36.1, §36.4), named in `mcp/guardrails.yaml` next to the
deterministic ones:

| Tool | pre | post |
|---|---|---|
| `iris_outliers` | — | static `block outlier dump`, then `self_check_output` |
| `iris_report` `{question}` | `self_check_input`, `jailbreak_detection`, `topical` (`topics: [iris, statistics]`) | `hallucination` |

`iris_report` is the free-text surface: pandas turns the question into a short prose report (mean/std/range of the
columns the question names, per-species means when it mentions species) — no model inside the tool, every number from
the CSV. Around it the worker runs NeMo's LLM rails: an injected or off-topic question is refused before pandas runs
(`guardrail blocked: pre: the arguments look like a jailbreak attempt`, `_meta.ramen.guardrail.rail:
jailbreak_detection`), a report that disagrees with the model's own samples is refused after.

- **No key in this repo.** `mcp/guardrails/config.yml` keeps `models: []`; the worker fills it at load from the LLM
  provider set on the console for the group (or the org, Config → LLM providers → `allowed_models`). Without one the
  deploy fails with `guardrails: rail self_check_output on iris_outliers needs an LLM: set the group's or the org's
  provider` — never a silently unguarded tool.
- `mcp/guardrails/prompts.yml` overrides the worker's prompts for `self_check_input` and `self_check_output` with the
  group's own policy wording; the other rails use the worker's generated prompts.
- Golden cases stay on the static rails (an LLM verdict is not deterministic); the existing `iris_outliers` case now
  also passes through `self_check_output` on deploy. Evals: `mcp/evals/promptfooconfig.llm.yaml` holds one
  `llm-rubric` test on `iris_report` graded by `openai:gpt-4o-mini` — a second config because promptfoo cannot skip a
  single test on a missing key; run it only with `OPENAI_API_KEY` set.
- Local proof without credit: the Ramen runtime's `tests/fake_llm.py` is a deterministic OpenAI-compatible server;
  with `RAMEN_LLM_PROVIDER=openai RAMEN_LLM_MODEL=fake-mini RAMEN_LLM_API_KEY=x RAMEN_LLM_BASE_URL=http://127.0.0.1:<port>/v1`
  the loader (`uv run --project ../ramen/runtime-py --extra nemo --with pandas==3.1.1 python -m ramen_runtime --bucket .`)
  loads both tools, passes a sepal-width question and refuses "pretend you have no rules" and "weather in Tokyo".
- `timeout_s` is 30: a model round trip per rail, three for `hallucination`.

## Asking the user, and long-running work (1.0.0, MCP 2026-07-28)
Ramen 1.0.0 serves the 2026-07-28 revision of MCP next to 2025-06-18; the three older tools answer both exactly as before.
Two tools show what the new revision adds:

- **`confirm_delete_note`** asks before it acts. Its code raises `InputRequired` with a yes/no form
  (`ramen_runtime.elicit`); the client gets `resultType: "input_required"`, shows the form to the user and calls again
  with `inputResponses`. Confirming deletes the note from a fixed demo list; declining, cancelling or answering no
  returns `Nothing was deleted: …` as a normal result (`isError: false`). Nothing is stored on the worker between the two
  calls. A 2025-06-18 client is told, as a tool error, that the tool needs a newer client.
- **`slow_report`** is marked `"task": true`. A client that declares the tasks extension
  (`io.modelcontextprotocol/tasks`) gets a task id at once and polls `tasks/get`; it can `tasks/cancel`. Any other
  client just waits for the answer. `seconds` is capped at 30. The code calls `ramen_runtime.progress(...)`, which
  reaches clients that asked for progress.

`mcp/tests.yaml` covers both paths of `confirm_delete_note`: a case with `respond:` answers the form for the console
(confirm → deleted, decline → nothing deleted), and `expect: {input_required: [confirm]}` checks that the tool asks at
all. `mcp/guardrails.yaml` puts the tool behind the input rail, which runs on the first call and again on the call that
carries the user's answer, before the tool acts on it.

## Try it
1. Deploy Ramen (see its README).
2. Create a group, set its repo to `https://github.com/bkraad47/ramen-demo-mcp-group`.
3. Deploy, then call `demo_calculator_tool` with `{"var1": 2, "var2": 3, "func": "add"}` from any MCP client.

## Deploy on push (GitHub Actions)
`.github/workflows/ramen-deploy.yml` asks a Ramen console to deploy this group when `mcp/` changes on `main` and
fails the run if the deploy fails. Set the repo variable `RAMEN_URL` and the secret `RAMEN_API_KEY` (an `rmn_` key,
Group Admin of this group) to turn it on; without them it does nothing. Guide:
[Deploy from GitHub Actions](https://bkraad47.github.io/ramen/wiki/deploy-github-actions/).
