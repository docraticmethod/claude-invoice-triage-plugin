# Curie agent developer screen

This repository provides the mock accounting tool for a 30-minute live interview. The candidate builds the **entire Claude Code plugin** during the session. There is no plugin starter code here.

## Before the interview

Install [Claude Code](https://code.claude.com/docs/en/quickstart), [uv](https://docs.astral.sh/uv/getting-started/installation/), and Python 3.10 or newer. Clone this repository and start Claude Code from its root:

```sh
git clone https://github.com/curie-eng/agent-screen-starter.git
cd agent-screen-starter
claude
```

Approve the repository's `.mcp.json` server when Claude Code asks. Run `/mcp` and confirm that `mock-invoices` is connected. The first launch may download the Python MCP SDK, so complete this check before the timed exercise.

## The 30-minute exercise

A finance client says: **“I want a Claude plugin that tells me which unpaid invoices need attention today.”** Build a complete, runnable Claude Code plugin that uses the supplied `list_open_invoices` MCP tool. Use **October 19, 2026** as the reporting date.

You have 30 minutes:

1. **First 5 minutes:** Discuss the request with the interviewer, who will play the client.
2. **Next 20 minutes:** Build the plugin.
3. **Final 5 minutes:** Demonstrate it and explain your decisions.

Create your plugin in a new directory inside this repository. You can test a local plugin with `claude --plugin-dir ./YOUR_PLUGIN_DIRECTORY` (restart Claude Code after creating the plugin).

You may use Claude Code and documentation during the exercise. Do not send messages to customers or modify invoice data.

## Supplied tool

`list_open_invoices()` returns a JSON object containing an `invoices` array. Each invoice has:

- `id`: invoice identifier
- `customer`: customer name
- `balance_cents`: outstanding balance in USD cents
- `due_date`: ISO date string or `null`
- `status`: `open`

The mock data is synthetic.

## Submitting your work

Share your plugin directory or a private repository with the interviewer after the session. Please do not open a public pull request with your solution against this starter repository.
