"""Tests for dashboard module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

dashboard = import_script("dashboard", "dashboard")


class TestEsc(unittest.TestCase):
    """Test HTML escaping."""

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
    """Test numeric detection."""

    def test_integer(self):
        self.assertTrue(dashboard.is_numeric("42"))

    def test_float(self):
        self.assertTrue(dashboard.is_numeric("3.14"))

    def test_negative(self):
        self.assertTrue(dashboard.is_numeric("-100"))

    def test_comma_separated(self):
        self.assertTrue(dashboard.is_numeric("1,000"))

    def test_large_number(self):
        self.assertTrue(dashboard.is_numeric("1,234,567.89"))

    def test_zero(self):
        self.assertTrue(dashboard.is_numeric("0"))

    def test_text(self):
        self.assertFalse(dashboard.is_numeric("hello"))

    def test_empty(self):
        self.assertFalse(dashboard.is_numeric(""))

    def test_none(self):
        self.assertFalse(dashboard.is_numeric(None))

    def test_mixed(self):
        self.assertFalse(dashboard.is_numeric("42abc"))

    def test_date(self):
        self.assertFalse(dashboard.is_numeric("2026-03-15"))


class TestHtmlTable(unittest.TestCase):
    """Test HTML table generation."""

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

    def test_non_numeric_no_class(self):
        rows = [{"name": "Acme", "status": "active"}]
        result = dashboard.html_table(rows)
        # "active" is not numeric, so no num class
        self.assertNotIn('class="num"', result)

    def test_highlight_column(self):
        rows = [{"name": "Acme", "status": "active"}]
        result = dashboard.html_table(rows, highlight_col="name")
        self.assertIn('class="highlight"', result)

    def test_escapes_content(self):
        rows = [{"name": "<script>alert('xss')</script>"}]
        result = dashboard.html_table(rows)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_multiple_rows(self):
        rows = [
            {"id": "1", "name": "Acme"},
            {"id": "2", "name": "Beta"},
        ]
        result = dashboard.html_table(rows)
        self.assertIn("Acme", result)
        self.assertIn("Beta", result)


class TestPage(unittest.TestCase):
    """Test full page HTML wrapper."""

    def test_includes_title(self):
        result = dashboard.page("Test Title", "<p>body</p>")
        self.assertIn("Test Title", result)
        self.assertIn("<p>body</p>", result)

    def test_includes_nav(self):
        result = dashboard.page("Title", "body")
        self.assertIn("Overview", result)
        self.assertIn("Cap Table", result)
        self.assertIn("Accounts", result)
        self.assertIn("CRM", result)

    def test_active_nav(self):
        result = dashboard.page("Title", "body", "index")
        # The "Overview" link (index.html) should be active
        self.assertIn('class="active"', result)

    def test_includes_brand_colors(self):
        result = dashboard.page("Title", "body")
        self.assertIn(dashboard.COLORS["primary"], result)
        self.assertIn(dashboard.COLORS["bg"], result)

    def test_escapes_title(self):
        result = dashboard.page("A & B <C>", "body")
        self.assertIn("A &amp; B &lt;C&gt;", result)

    def test_valid_html_structure(self):
        result = dashboard.page("Title", "body")
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("<html", result)
        self.assertIn("</html>", result)
        self.assertIn("<head>", result)
        self.assertIn("</head>", result)
        self.assertIn("<body>", result)
        self.assertIn("</body>", result)


class TestQueryRows(unittest.TestCase):
    """Test query_rows parsing."""

    @patch.object(dashboard, "check_db")
    @patch("subprocess.run")
    def test_returns_dicts(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(
            stdout="name,value\nfoo,1\nbar,2\n",
            returncode=0,
        )
        result = dashboard.query_rows("SELECT ...")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "foo")

    @patch.object(dashboard, "check_db")
    @patch("subprocess.run")
    def test_error_returns_empty(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = dashboard.query_rows("SELECT ...")
        self.assertEqual(result, [])


class TestQueryVal(unittest.TestCase):
    """Test query_val scalar extraction."""

    @patch.object(dashboard, "query_rows")
    def test_returns_first_value(self, mock_rows):
        mock_rows.return_value = [{"count": "42"}]
        self.assertEqual(dashboard.query_val("SELECT COUNT(*)"), "42")

    @patch.object(dashboard, "query_rows")
    def test_empty_returns_empty_string(self, mock_rows):
        mock_rows.return_value = []
        self.assertEqual(dashboard.query_val("SELECT ..."), "")


class TestBuildPages(unittest.TestCase):
    """Test page builder functions."""

    @patch.object(dashboard, "query_rows")
    @patch.object(dashboard, "query_val")
    def test_build_index(self, mock_val, mock_rows):
        mock_val.side_effect = ["3", "1000", "5", "500", "2", "10", "18", "5"]
        mock_rows.side_effect = [
            [],  # renewals
            [],  # stale contacts
        ]
        html = dashboard.build_index()
        self.assertIn("Overview", html)
        self.assertIn("<!DOCTYPE html>", html)

    @patch.object(dashboard, "query_rows")
    def test_build_cap_table(self, mock_rows):
        mock_rows.side_effect = [
            [{"holder": "Richard", "class": "ordinary", "held": "1000", "pct": "100"}],
            [{"class": "ordinary", "authorised": "10000", "issued": "1000", "available": "9000"}],
            [],  # pools
            [],  # events
        ]
        html = dashboard.build_cap_table()
        self.assertIn("Cap Table", html)
        self.assertIn("Richard", html)

    @patch.object(dashboard, "query_rows")
    def test_build_accounts(self, mock_rows):
        mock_rows.side_effect = [
            [{"account_path": "assets:bank:tide", "account_type": "assets", "balance": "5000", "currency": "GBP"}],
            [],  # recent txns
        ]
        html = dashboard.build_accounts()
        self.assertIn("Accounts", html)
        self.assertIn("assets:bank:tide", html)


class TestRouting(unittest.TestCase):
    """Test main() dispatch."""

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
