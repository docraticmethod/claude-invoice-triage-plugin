# Invoice Triage Plugin

A Claude Code plugin for the Curie agent-developer screen. It tells a finance
user which unpaid invoices need attention as of the reporting date
(**2026-10-19**), using the supplied `list_open_invoices` MCP tool.

## Run

From the repo root:

    claude --plugin-dir ./invoice-triage

Then, inside the session:

    /invoices-today

(also accepted: `/invoice-triage:invoices-today`)

## What it does

Calls `list_open_invoices` from the `mock-invoices` MCP server, converts each
balance from cents to dollars, and sorts the invoices into three buckets, each
ranked by balance descending:

- **Past due** — due before 2026-10-19
- **Due within 7 days** — due 2026-10-19 through 2026-10-26 inclusive
- **Missing information** — null due_date

Each bucket prints as a table of id, customer, balance, due_date, and days
overdue (filled in for past-due invoices, blank otherwise). The report closes
with total past-due exposure and the single top-priority account.

## Assumptions

- Reporting date is fixed at 2026-10-19 per the exercise.
- The 7-day window is hard-coded. It could be exposed as an argument; the brief
  does not require it.
- Invoice values are never hard-coded. The command works on whatever
  `list_open_invoices` returns.
- A null due_date is reported as missing information, not aged or dropped. The
  correct action is to obtain the date, not infer one.
- Invoices due more than 7 days out are outside "needs attention today" and are
  excluded from the report, which says so.
- `status` is always `open`, so the command does not filter on it.

Read-only: the command sends no messages and modifies no invoice data. Its
frontmatter scopes it to the single tool `mcp__mock-invoices__list_open_invoices`.

## Tests

Stdlib `unittest`. Covers the manifest, the command file, the mock data, the
date-boundary rules, and an opt-in live end-to-end run.

    # offline
    python3 -m unittest discover -s invoice-triage/tests -v

    # live (exercises the MCP tool end to end)
    RUN_LIVE=1 python3 -m unittest discover -s invoice-triage/tests -v

## Developer decision record

Two files at the repo root document how this plugin was built and why:

- **`../AGENT.md`** — the invoice-triage build plan handed to Claude Code.
  Context, the step-by-step construction, the bucket and date-boundary rules,
  verification criteria, and the design calls behind them (one read-only tool
  via `allowed-tools`, no hard-coded invoice values, null due dates surfaced
  for follow-up rather than aged, not-yet-due invoices excluded on purpose).
  Where it differs from this README, the README wins.
  
- **`../log.txt`** — a timestamped execution log Claude Code generated during
  the build. Each step is stamped with the system clock as it completed, along
  with verification runs and test results (23 tests, offline and live).

Together they are the decision trail: what was chosen, what was skipped on
purpose, and the evidence that each step actually ran.