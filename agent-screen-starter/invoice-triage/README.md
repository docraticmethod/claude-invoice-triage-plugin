# invoice-triage

A Claude Code plugin that reports which unpaid invoices need attention today. It uses the `list_open_invoices` tool from the `mock-invoices` MCP server and is read-only: it sends no messages and changes no data.

## Run

From the repository root, with the `mock-invoices` server approved and connected (`/mcp`):

```sh
claude --plugin-dir ./invoice-triage
```

Then run `/invoices-today`. Plugins load at launch, so restart Claude Code if you created or changed the plugin while it was running.

## What it reports

The reporting date is fixed at **2026-10-19**. Invoices land in three buckets, each sorted by balance, highest first:

| Bucket | Rule |
|---|---|
| Past due | `due_date` is before 2026-10-19 |
| Due within 7 days | `due_date` is 2026-10-19 through 2026-10-26, inclusive |
| Missing information | `due_date` is null, so the invoice can't be aged |

Each table shows id, customer, balance in dollars, due date, and days overdue (past-due invoices only). The report ends with total past-due exposure and the top-priority account.

## Assumptions

- A null due date is reported, not dropped or guessed. The fix is to get the date.
- Invoices due after 2026-10-26 are left out and counted in a note.
- The 7-day window and the reporting date are fixed in `commands/invoices-today.md`.
- Every invoice is treated as open, because the tool only returns open invoices.

## Tests

From the repository root:

```sh
python3 -m unittest discover -s invoice-triage/tests -v
```

This runs offline checks of the manifest, the command file (frontmatter, tool restriction, dates, read-only wording), the mock data, and the bucketing rules including the date boundaries. To also run the end-to-end test, which launches Claude Code with the plugin and checks the real report, set `RUN_LIVE=1`. It needs `claude` on the PATH and makes one model call.
