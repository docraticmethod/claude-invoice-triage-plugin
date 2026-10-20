"""Tests for the invoice-triage plugin.

Run from the repository root:

    python3 -m unittest discover -s invoice-triage/tests -v

Set RUN_LIVE=1 to also run the end-to-end test, which launches Claude Code
with the plugin and checks the real report (needs `claude` and a connected
mock-invoices server; makes one model call).
"""

import ast
import json
import os
import re
import shutil
import subprocess
import unittest
from datetime import date, timedelta
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = PLUGIN_DIR.parent
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
COMMAND = PLUGIN_DIR / "commands" / "invoices-today.md"
MOCK_SERVER = REPO_DIR / "mock_invoices.py"

REPORTING_DATE = date(2026, 10, 19)
WINDOW_END = REPORTING_DATE + timedelta(days=7)
TOOL = "mcp__mock-invoices__list_open_invoices"


def load_mock_invoices():
    """Read the invoices literal out of mock_invoices.py without importing it.

    Importing would need the `mcp` package; the data is a plain dict literal
    returned by list_open_invoices, so parse it from the source instead.
    """
    tree = ast.parse(MOCK_SERVER.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "list_open_invoices":
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Return):
                    return ast.literal_eval(stmt.value)["invoices"]
    raise AssertionError("list_open_invoices not found in mock_invoices.py")


def triage(invoices, today=REPORTING_DATE):
    """Reference implementation of the rules in commands/invoices-today.md."""
    window_end = today + timedelta(days=7)
    buckets = {"past_due": [], "due_soon": [], "missing": [], "later": []}
    for inv in invoices:
        row = dict(inv, dollars=inv["balance_cents"] / 100)
        if inv["due_date"] is None:
            buckets["missing"].append(row)
            continue
        due = date.fromisoformat(inv["due_date"])
        if due < today:
            row["days_overdue"] = (today - due).days
            buckets["past_due"].append(row)
        elif due <= window_end:
            buckets["due_soon"].append(row)
        else:
            buckets["later"].append(row)
    for rows in buckets.values():
        rows.sort(key=lambda r: r["dollars"], reverse=True)
    return buckets


def split_frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    assert match, "command file has no frontmatter"
    fields = dict(
        line.split(":", 1) for line in match.group(1).splitlines() if ":" in line
    )
    return {k.strip(): v.strip() for k, v in fields.items()}, match.group(2)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())

    def test_required_fields(self):
        self.assertEqual(self.manifest["name"], "invoice-triage")
        self.assertTrue(self.manifest["description"])

    def test_version_is_semver(self):
        self.assertRegex(self.manifest["version"], r"^\d+\.\d+\.\d+$")


class CommandFileTests(unittest.TestCase):
    def setUp(self):
        self.meta, self.body = split_frontmatter(COMMAND.read_text())

    def test_has_description(self):
        self.assertTrue(self.meta.get("description"))

    def test_only_the_read_only_tool_is_allowed(self):
        self.assertEqual(self.meta.get("allowed-tools"), TOOL)

    def test_states_reporting_date_and_window(self):
        self.assertIn(REPORTING_DATE.isoformat(), self.body)
        self.assertIn(WINDOW_END.isoformat(), self.body)

    def test_names_the_data_source(self):
        self.assertIn("list_open_invoices", self.body)
        self.assertIn("mock-invoices", self.body)

    def test_defines_all_three_buckets(self):
        for heading in ("PAST DUE", "DUE WITHIN 7 DAYS", "MISSING INFORMATION"):
            self.assertIn(heading, self.body)

    def test_converts_cents_to_dollars(self):
        self.assertIn("balance_cents / 100", self.body)

    def test_is_declared_read_only(self):
        self.assertIn("Read-only", self.body)
        self.assertIn("Do not send messages or modify data", self.body)


class MockDataTests(unittest.TestCase):
    """Pin the mock data so a change to it is noticed, and check the rules on it."""

    def setUp(self):
        self.invoices = load_mock_invoices()
        self.buckets = triage(self.invoices)

    def test_invoice_shape(self):
        for inv in self.invoices:
            self.assertEqual(
                set(inv),
                {"id", "customer", "balance_cents", "due_date", "status"},
            )
            self.assertIsInstance(inv["balance_cents"], int)
            self.assertEqual(inv["status"], "open")

    def test_bucket_membership_and_order(self):
        ids = {k: [r["id"] for r in v] for k, v in self.buckets.items()}
        self.assertEqual(ids["past_due"], ["INV-101", "INV-102"])
        self.assertEqual(ids["due_soon"], ["INV-103"])
        self.assertEqual(ids["missing"], ["INV-104"])
        self.assertEqual(ids["later"], [])

    def test_days_overdue(self):
        days = {r["id"]: r["days_overdue"] for r in self.buckets["past_due"]}
        self.assertEqual(days, {"INV-101": 30, "INV-102": 31})

    def test_past_due_exposure_and_top_priority(self):
        past_due = self.buckets["past_due"]
        self.assertEqual(sum(r["dollars"] for r in past_due), 2000.00)
        self.assertEqual(past_due[0]["customer"], "Acme")
        self.assertEqual(past_due[0]["dollars"], 1200.00)


class BoundaryTests(unittest.TestCase):
    """Edge cases of the bucketing rules, on synthetic invoices."""

    def bucket_of(self, due):
        inv = {"id": "X", "customer": "X", "balance_cents": 100, "due_date": due}
        result = triage([inv])
        return next(k for k, v in result.items() if v)

    def test_due_the_day_before_is_past_due(self):
        self.assertEqual(self.bucket_of("2026-10-18"), "past_due")

    def test_due_on_reporting_date_is_not_past_due(self):
        self.assertEqual(self.bucket_of("2026-10-19"), "due_soon")

    def test_last_day_of_window_is_included(self):
        self.assertEqual(self.bucket_of("2026-10-26"), "due_soon")

    def test_day_after_window_is_left_out(self):
        self.assertEqual(self.bucket_of("2026-10-27"), "later")

    def test_null_due_date_is_missing_information(self):
        self.assertEqual(self.bucket_of(None), "missing")

    def test_ties_keep_every_invoice(self):
        invs = [
            {"id": "A", "customer": "A", "balance_cents": 500, "due_date": None},
            {"id": "B", "customer": "B", "balance_cents": 500, "due_date": None},
        ]
        self.assertEqual(len(triage(invs)["missing"]), 2)


@unittest.skipUnless(
    os.environ.get("RUN_LIVE") == "1" and shutil.which("claude"),
    "set RUN_LIVE=1 (and have `claude` on PATH) to run the end-to-end test",
)
class LiveEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run(
            ["claude", "--plugin-dir", str(PLUGIN_DIR), "-p", "/invoice-triage:invoices-today"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=240,
        )
        assert proc.returncode == 0, proc.stderr
        cls.output = proc.stdout

    def section(self, start, end):
        text = self.output
        lowered = text.lower()
        s = lowered.index(start.lower())
        e = lowered.index(end.lower(), s) if end else len(text)
        return text[s:e]

    def test_each_invoice_is_in_the_right_bucket(self):
        past = self.section("past due", "due within 7 days")
        soon = self.section("due within 7 days", "missing information")
        missing = self.section("missing information", "total past-due")
        self.assertIn("INV-101", past)
        self.assertIn("INV-102", past)
        self.assertIn("INV-103", soon)
        self.assertIn("INV-104", missing)
        for other in ("INV-101", "INV-102", "INV-104"):
            self.assertNotIn(other, soon)

    def test_past_due_sorted_by_balance(self):
        past = self.section("past due", "due within 7 days")
        self.assertLess(past.index("INV-101"), past.index("INV-102"))

    def test_amounts_and_days_overdue(self):
        for needle in ("$1,200.00", "$800.00", "$500.00", "$250.00"):
            self.assertIn(needle, self.output)
        past = self.section("past due", "due within 7 days")
        self.assertRegex(past, r"INV-101[^\n]*\b30\b")
        self.assertRegex(past, r"INV-102[^\n]*\b31\b")

    def test_closing_summary(self):
        self.assertIn("$2,000.00", self.output)
        closing = self.output[self.output.lower().index("total past-due"):]
        self.assertIn("Acme", closing)


if __name__ == "__main__":
    unittest.main()
