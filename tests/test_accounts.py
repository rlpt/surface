"""Tests for accounts module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script, make_dolt_db_dir, mock_subprocess_csv, mock_subprocess_val

accounts = import_script("accounts", "accounts")


class TestDsqlCsv(unittest.TestCase):
    """Test dsql_csv parsing logic."""

    @patch.object(accounts, "check_db")
    @patch("subprocess.run")
    def test_returns_rows_without_header(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(
            stdout="path,account_type\nassets:bank:tide,assets\nexpenses:infra,expenses\n",
            returncode=0,
        )
        result = accounts.dsql_csv("SELECT path, account_type FROM accounts;")
        self.assertEqual(result, ["assets:bank:tide,assets", "expenses:infra,expenses"])

    @patch.object(accounts, "check_db")
    @patch("subprocess.run")
    def test_empty_result(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(stdout="col\n", returncode=0)
        # When only header, strip gives "col", split gives ["col"], len is 1
        result = accounts.dsql_csv("SELECT COUNT(*) FROM accounts;")
        self.assertEqual(result, [])

    @patch.object(accounts, "check_db")
    @patch("subprocess.run")
    def test_single_row(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(stdout="count\n18\n", returncode=0)
        result = accounts.dsql_csv("SELECT COUNT(*) FROM accounts;")
        self.assertEqual(result, ["18"])


class TestDsqlVal(unittest.TestCase):
    """Test dsql_val returns first row or empty string."""

    @patch.object(accounts, "check_db")
    @patch("subprocess.run")
    def test_returns_first_row(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(stdout="count\n42\n", returncode=0)
        self.assertEqual(accounts.dsql_val("SELECT COUNT(*)..."), "42")

    @patch.object(accounts, "check_db")
    @patch("subprocess.run")
    def test_empty_returns_empty_string(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(stdout="col\n", returncode=0)
        self.assertEqual(accounts.dsql_val("SELECT ..."), "")


class TestCheckDb(unittest.TestCase):
    """Test check_db exits when database is missing."""

    def test_missing_db_exits(self, ):
        with patch.dict(os.environ, {"SURFACE_DB": "/nonexistent/path"}):
            # Re-assign module variable
            old_db = accounts.SURFACE_DB
            accounts.SURFACE_DB = "/nonexistent/path"
            try:
                with self.assertRaises(SystemExit):
                    accounts.check_db()
            finally:
                accounts.SURFACE_DB = old_db

    def test_existing_db_passes(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, ".surface-db")
            dolt_path = os.path.join(db_path, ".dolt")
            os.makedirs(dolt_path)
            old_db = accounts.SURFACE_DB
            accounts.SURFACE_DB = db_path
            try:
                accounts.check_db()  # should not raise
            finally:
                accounts.SURFACE_DB = old_db


class TestCmdCheck(unittest.TestCase):
    """Test the check command validation logic."""

    @patch.object(accounts, "dsql_val")
    @patch.object(accounts, "dsql_csv")
    def test_clean_check_passes(self, mock_csv, mock_val):
        # No orphans, no unbalanced
        mock_csv.side_effect = [[], []]
        mock_val.side_effect = ["18", "5"]
        # Should not raise
        accounts.cmd_check()

    @patch.object(accounts, "dsql_val")
    @patch.object(accounts, "dsql_csv")
    def test_orphan_accounts_fail(self, mock_csv, mock_val):
        mock_csv.side_effect = [
            ["expenses:unknown"],  # orphans
            [],  # no unbalanced
        ]
        mock_val.side_effect = ["18", "5"]
        with self.assertRaises(SystemExit):
            accounts.cmd_check()

    @patch.object(accounts, "dsql_val")
    @patch.object(accounts, "dsql_csv")
    def test_unbalanced_transactions_fail(self, mock_csv, mock_val):
        mock_csv.side_effect = [
            [],  # no orphans
            ["1,0.50"],  # unbalanced txn
        ]
        mock_val.side_effect = ["18", "5"]
        with self.assertRaises(SystemExit):
            accounts.cmd_check()


class TestCmdBal(unittest.TestCase):
    """Test balance command SQL dispatch."""

    @patch.object(accounts, "dsql")
    def test_bal_no_filter(self, mock_dsql):
        accounts.cmd_bal("")
        sql = mock_dsql.call_args[0][0]
        self.assertIn("account_balances", sql)

    @patch.object(accounts, "dsql")
    def test_bal_with_filter(self, mock_dsql):
        accounts.cmd_bal("expenses:infra")
        sql = mock_dsql.call_args[0][0]
        self.assertIn("expenses:infra", sql)
        self.assertIn("LIKE", sql)

    @patch.object(accounts, "dsql")
    def test_bal_filter_escapes_quotes(self, mock_dsql):
        accounts.cmd_bal("test'quote")
        sql = mock_dsql.call_args[0][0]
        self.assertIn("test''quote", sql)


class TestCmdIs(unittest.TestCase):
    """Test income statement command."""

    @patch.object(accounts, "dsql")
    def test_is_no_period(self, mock_dsql):
        accounts.cmd_is([])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("revenue", sql)
        self.assertIn("expenses", sql)

    @patch.object(accounts, "dsql")
    def test_is_with_period(self, mock_dsql):
        accounts.cmd_is(["-p", "Jan 2026"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("Jan 2026", sql)
        self.assertIn("INTERVAL 1 MONTH", sql)


class TestCmdReg(unittest.TestCase):
    """Test register command."""

    def test_reg_no_account_exits(self):
        with self.assertRaises(SystemExit):
            accounts.cmd_reg("")

    @patch.object(accounts, "dsql")
    def test_reg_escapes_input(self, mock_dsql):
        accounts.cmd_reg("assets:bank")
        sql = mock_dsql.call_args[0][0]
        self.assertIn("assets:bank", sql)


class TestRouting(unittest.TestCase):
    """Test main() dispatch."""

    @patch.object(accounts, "cmd_bal")
    def test_route_bal(self, mock_cmd):
        with patch("sys.argv", ["accounts", "bal", "expenses"]):
            accounts.main()
        mock_cmd.assert_called_once_with("expenses")

    @patch.object(accounts, "cmd_is")
    def test_route_is(self, mock_cmd):
        with patch("sys.argv", ["accounts", "is", "-p", "Jan 2026"]):
            accounts.main()
        mock_cmd.assert_called_once_with(["-p", "Jan 2026"])

    @patch.object(accounts, "cmd_bs")
    def test_route_bs(self, mock_cmd):
        with patch("sys.argv", ["accounts", "bs"]):
            accounts.main()
        mock_cmd.assert_called_once()

    @patch.object(accounts, "cmd_check")
    def test_route_check(self, mock_cmd):
        with patch("sys.argv", ["accounts", "check"]):
            accounts.main()
        mock_cmd.assert_called_once()

    @patch.object(accounts, "cmd_help")
    def test_route_unknown_shows_help(self, mock_cmd):
        with patch("sys.argv", ["accounts", "unknown-command"]):
            accounts.main()
        mock_cmd.assert_called_once()

    @patch.object(accounts, "cmd_help")
    def test_route_no_args_shows_help(self, mock_cmd):
        with patch("sys.argv", ["accounts"]):
            accounts.main()
        mock_cmd.assert_called_once()


if __name__ == "__main__":
    unittest.main()
