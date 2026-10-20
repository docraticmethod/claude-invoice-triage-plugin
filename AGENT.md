# Invoice Triage Plugin — Complete Build Plan

Claude Code plugin for the Curie agent developer screen. Reporting date: **2026-10-19**.
Follow top to bottom. Everything self-contained.

---



---

## Step 1 — Prerequisites (do before the clock starts)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # uv (skip if installed)
python3 --version                                   # confirm 3.10+
git clone https://github.com/curie-eng/agent-screen-starter.git
cd agent-screen-starter
claude
```

Inside Claude Code: approve the `.mcp.json` server, run `/mcp`, confirm `mock-invoices` is **connected**.
Ask it to call `list_open_invoices` once and eyeball four rows. First launch may pull the MCP SDK via uv; let it finish.

---

## Step 2 — Scaffold (from repo root)

```bash
mkdir -p invoice-triage/.claude-plugin invoice-triage/commands
```

Resulting structure:

```
invoice-triage/
  .claude-plugin/
    plugin.json
  commands/
    invoices-today.md
```

---

## Step 3 — Manifest: `invoice-triage/.claude-plugin/plugin.json`

```json
{
  "name": "invoice-triage",
  "description": "Flags unpaid invoices needing attention as of the reporting date.",
  "version": "0.1.0"
}
```

---

## Step 4 — Command: `invoice-triage/commands/invoices-today.md`

```markdown
---
description: Report unpaid invoices needing attention as of the reporting date
---
Reporting date: 2026-10-19.

1. Call `list_open_invoices` from the `mock-invoices` MCP server.
2. Convert each balance to USD dollars (balance_cents / 100).
3. Sort invoices into three buckets:
   - PAST DUE: due_date earlier than 2026-10-19
   - DUE WITHIN 7 DAYS: due_date from 2026-10-19 through 2026-10-26 inclusive
   - MISSING INFORMATION: due_date is null (cannot be aged)
4. Within each bucket, sort by balance descending.
5. Print each bucket as a table: id, customer, balance, due_date, days overdue (blank when missing).
6. Close with total past-due exposure in dollars and the single top-priority account.

Read-only. Do not send messages or modify data.
```

---

## Step 5 — Launch and test

```bash
claude --plugin-dir ./invoice-triage
```

Inside: `/mcp` (confirm connected), then run `/invoices-today`.

**Restart gotcha:** if you created the files after launching, fully quit and relaunch. Plugins load at launch; the command will not register otherwise.

---

## Step 6 — Verify output against known data

The mock tool returns exactly four invoices. Correct result:

| Bucket | Invoice | Customer | Balance | Due | Days overdue |
|---|---|---|---|---|---|
| Past due | INV-102 | Beta | $800.00 | 2026-09-18 | 31 |
| Past due | INV-101 | Acme | $1,200.00 | 2026-09-19 | 30 |
| Due ≤7 days | INV-103 | Coda | $500.00 | 2026-10-25 | — |
| Missing info | INV-104 | Delta | $250.00 | null | — |

Within "Past due," balance sort puts **Acme $1,200 first, Beta $800 second**.
Total past-due exposure: **$2,000.00**. Top priority: **Acme, $1,200 at 30 days**.

---

## Step 7 — Closing narration (the highest-scoring 5 minutes)

- "Needs attention" is a definition problem. I bucket by urgency, rank by dollars inside each, so it reads top to bottom for a finance client.
- The null due_date is the real test. I surface Delta as "missing information" rather than drop it or guess a date. The correct action is to go get the date, not age a fiction.
- Chose a slash command over an agent or skill: this is an on-demand, repeatable report. Lowest ceremony that fits the ask.
- The 7-day window is a knob the client owns. Coda sits on the boundary (10-25), which is exactly the case the window exists to catch.

---

## Optional upgrade — only if time allows or they press on correctness

Move date math into a script for determinism:

1. Add `invoice-triage/scripts/triage.py` that reads the invoice JSON, computes buckets and day counts, prints the tables.
2. In the command, instruct Claude to run it: `${CLAUDE_PLUGIN_ROOT}/scripts/triage.py`.

Say the tradeoff out loud: "I'd ship the script version for production so dates never drift. For a four-row screen, the prompt version is faster to build and sufficient." That one line shows you know when not to over-engineer.

---

## Constraints (do not violate)

- Read-only. Never send messages or modify invoice data.
- Share your plugin directory or a private repo after the session. No public PR against the starter repo.