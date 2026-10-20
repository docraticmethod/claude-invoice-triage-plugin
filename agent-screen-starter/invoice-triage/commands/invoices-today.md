---
description: Report unpaid invoices needing attention as of the reporting date
allowed-tools: mcp__mock-invoices__list_open_invoices
---
Reporting date: 2026-10-19.

1. Call `list_open_invoices` from the `mock-invoices` MCP server.
2. Convert each balance to USD dollars (balance_cents / 100).
3. Sort invoices into three buckets:
   - PAST DUE: due_date earlier than 2026-10-19
   - DUE WITHIN 7 DAYS: due_date from 2026-10-19 through 2026-10-26 inclusive
   - MISSING INFORMATION: due_date is null (cannot be aged)
   Invoices due after 2026-10-26 need no attention yet: leave them out of the tables and say how many were omitted.
4. Within each bucket, sort by balance descending.
5. Print each bucket as a table: id, customer, balance, due_date, days overdue. Fill in days overdue only for past-due invoices; leave it blank otherwise.
6. Close with total past-due exposure in dollars and the single top-priority account.

Read-only. Do not send messages or modify data.
