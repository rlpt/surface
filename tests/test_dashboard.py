"""Tests for dashboard module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

dashboard = import_script("dashboard", "dashboard")

SHARES_DATA = {
    "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "nominal_currency": "GBP", "authorised": 10000}],
    "holders": [{"id": "richard", "display_name": "Richard Targett"}],
    "share_events": [
        {"event_date": "2024-06-01", "event_type": "grant", "holder_id": "richard", "share_class": "ordinary", "quantity": 1000},
    ],
    "pools": [{"name": "founder", "share_class": "ordinary", "budget": 8000}],
    "pool_members": [{"pool_name": "founder", "holder_id": "richard"}],
}

OFFICERS_DATA = {
    "officers": [
        {"id": "richard", "person_name": "Richard Targett", "role": "director", "appointed_date": "2025-06-15"},
    ],
}

COMPLIANCE_DATA = {
    "deadlines": [
        {"id": "test-1", "title": "Annual accounts", "due_date": "2026-06-15",
         "frequency": "annual", "category": "companies-house", "status": "upcoming"},
    ],
}


class TestEsc(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(dashboard.esc("hello"), "hello")

    def test_ampersand(self):
        self.assertEqual(dashboard.esc("A & B"), "A &amp; B")

    def test_angle_brackets(self):
        self.assertEqual(dashboard.esc("<b>bold</b>"), "&lt;b&gt;bold&lt;/b&gt;")

    def test_all_special(self):
        self.assertEqual(dashboard.esc("a < b & c > d"), "a &lt; b &amp; c &gt; d")

    def test_numeric_input(self):
        self.assertEqual(dashboard.esc(42), "42")

    def test_empty_string(self):
        self.assertEqual(dashboard.esc(""), "")


class TestIsNumeric(unittest.TestCase):
    def test_integer(self):
        self.assertTrue(dashboard.is_numeric("42"))

    def test_float(self):
        self.assertTrue(dashboard.is_numeric("3.14"))

    def test_negative(self):
        self.assertTrue(dashboard.is_numeric("-100"))

    def test_comma_separated(self):
        self.assertTrue(dashboard.is_numeric("1,000"))

    def test_text(self):
        self.assertFalse(dashboard.is_numeric("hello"))

    def test_empty(self):
        self.assertFalse(dashboard.is_numeric(""))

    def test_none(self):
        self.assertFalse(dashboard.is_numeric(None))


class TestHtmlTable(unittest.TestCase):
    def test_empty_rows(self):
        result = dashboard.html_table([])
        self.assertIn("No data.", result)

    def test_single_row(self):
        rows = [{"name": "Acme Corp", "revenue": "1000"}]
        result = dashboard.html_table(rows)
        self.assertIn("<table>", result)
        self.assertIn("<th>name</th>", result)
        self.assertIn("Acme Corp", result)

    def test_numeric_column_gets_class(self):
        rows = [{"name": "Acme", "amount": "1000"}]
        result = dashboard.html_table(rows)
        self.assertIn('class="num"', result)

    def test_highlight_column(self):
        rows = [{"name": "Acme", "status": "active"}]
        result = dashboard.html_table(rows, highlight_col="name")
        self.assertIn('class="highlight"', result)

    def test_escapes_content(self):
        rows = [{"name": "<script>alert('xss')</script>"}]
        result = dashboard.html_table(rows)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)


class TestPage(unittest.TestCase):
    def test_includes_title(self):
        result = dashboard.page("Test Title", "<p>body</p>")
        self.assertIn("Test Title", result)
        self.assertIn("<p>body</p>", result)

    def test_includes_nav(self):
        result = dashboard.page("Title", "body")
        self.assertIn("Overview", result)
        self.assertIn("Cap Table", result)
        self.assertIn("Officers", result)
        self.assertIn("Compliance", result)

    def test_active_nav(self):
        result = dashboard.page("Title", "body", "index")
        self.assertIn('class="active"', result)

    def test_includes_brand_colors(self):
        result = dashboard.page("Title", "body")
        self.assertIn(dashboard.COLORS["primary"], result)
        self.assertIn(dashboard.COLORS["bg"], result)

    def test_valid_html_structure(self):
        result = dashboard.page("Title", "body")
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("<html", result)
        self.assertIn("</html>", result)


class TestBuildPages(unittest.TestCase):
    @patch("datalib.changelog")
    @patch("datalib.load")
    def test_build_index(self, mock_load, mock_changelog):
        mock_load.side_effect = lambda d: {
            "shares": SHARES_DATA,
            "officers": OFFICERS_DATA, "compliance": COMPLIANCE_DATA,
        }[d]
        mock_changelog.return_value = []
        html = dashboard.build_index()
        self.assertIn("Overview", html)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Shareholders", html)
        self.assertIn("Officers", html)

    @patch("datalib.load")
    def test_build_cap_table(self, mock_load):
        mock_load.return_value = SHARES_DATA
        html = dashboard.build_cap_table()
        self.assertIn("Cap Table", html)
        self.assertIn("richard", html)

    @patch("datalib.load")
    def test_build_officers(self, mock_load):
        mock_load.return_value = OFFICERS_DATA
        html = dashboard.build_officers()
        self.assertIn("Officers", html)
        self.assertIn("Richard Targett", html)

    @patch("datalib.load")
    def test_build_compliance(self, mock_load):
        mock_load.return_value = COMPLIANCE_DATA
        html = dashboard.build_compliance()
        self.assertIn("Compliance", html)
        self.assertIn("Annual accounts", html)


class TestRouting(unittest.TestCase):
    @patch.object(dashboard, "cmd_build")
    def test_route_build(self, mock_cmd):
        with patch("sys.argv", ["dashboard", "build"]):
            dashboard.main()
        mock_cmd.assert_called_once_with([])

    @patch.object(dashboard, "cmd_serve")
    def test_route_serve(self, mock_cmd):
        with patch("sys.argv", ["dashboard", "serve"]):
            dashboard.main()
        mock_cmd.assert_called_once_with([])

    @patch.object(dashboard, "cmd_help")
    def test_route_unknown_shows_help(self, mock_cmd):
        with patch("sys.argv", ["dashboard", "garbage"]):
            dashboard.main()
        mock_cmd.assert_called_once()

    @patch.object(dashboard, "cmd_help")
    def test_route_no_args_shows_help(self, mock_cmd):
        with patch("sys.argv", ["dashboard"]):
            dashboard.main()
        mock_cmd.assert_called_once()


if __name__ == "__main__":
    unittest.main()
