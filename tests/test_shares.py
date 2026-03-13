"""Tests for shares module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

shares = import_script("shares", "shares")


class TestDsqlRows(unittest.TestCase):
    """Test dsql_rows returns list of dicts."""

    @patch.object(shares, "check_db")
    @patch("subprocess.run")
    def test_returns_dicts(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(
            stdout="name,value\nordinary,0.01\npreferred,1.00\n",
            returncode=0,
        )
        result = shares.dsql_rows("SELECT name, value FROM share_classes;")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "ordinary")
        self.assertEqual(result[0]["value"], "0.01")

    @patch.object(shares, "check_db")
    @patch("subprocess.run")
    def test_empty_result(self, mock_run, mock_check):
        mock_run.return_value = MagicMock(stdout="name\n", returncode=0)
        result = shares.dsql_rows("SELECT name FROM holders;")
        self.assertEqual(result, [])


class TestCmdGrant(unittest.TestCase):
    """Test grant validation logic."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["alice"])

    @patch.object(shares, "dsql_val")
    def test_unknown_holder_exits(self, mock_val):
        mock_val.return_value = ""  # holder not found
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["nobody", "ordinary", "100"])

    @patch.object(shares, "dsql_val")
    def test_unknown_class_exits(self, mock_val):
        mock_val.side_effect = ["Alice Smith", ""]  # holder found, class not
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["alice", "phantom", "100"])

    @patch.object(shares, "dsql_val")
    def test_insufficient_shares_exits(self, mock_val):
        mock_val.side_effect = [
            "Alice Smith",  # holder exists
            "10000",  # class authorised
            "50",  # only 50 available
        ]
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["alice", "ordinary", "100"])

    @patch.object(shares, "cmd_table")
    @patch.object(shares, "dolt_commit")
    @patch.object(shares, "dsql")
    @patch.object(shares, "dsql_val")
    def test_successful_grant(self, mock_val, mock_dsql, mock_commit, mock_table):
        mock_val.side_effect = [
            "Alice Smith",  # holder exists
            "10000",  # class authorised
            "9000",  # 9000 available
        ]
        shares.cmd_grant(["alice", "ordinary", "500"])
        # Verify INSERT was called
        sql = mock_dsql.call_args[0][0]
        self.assertIn("INSERT INTO share_events", sql)
        self.assertIn("'grant'", sql)
        self.assertIn("'alice'", sql)
        self.assertIn("500", sql)
        mock_commit.assert_called_once()
        mock_table.assert_called_once()


class TestCmdTransfer(unittest.TestCase):
    """Test transfer validation logic."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["alice", "bob"])

    @patch.object(shares, "dsql_val")
    def test_unknown_source_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["nobody", "bob", "ordinary", "10"])

    @patch.object(shares, "dsql_val")
    def test_unknown_target_exits(self, mock_val):
        mock_val.side_effect = ["Alice Smith", ""]
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["alice", "nobody", "ordinary", "10"])

    @patch.object(shares, "dsql_val")
    def test_insufficient_holdings_exits(self, mock_val):
        mock_val.side_effect = [
            "Alice Smith",  # from holder
            "Bob Chen",  # to holder
            "5",  # only holds 5
        ]
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["alice", "bob", "ordinary", "10"])

    @patch.object(shares, "cmd_table")
    @patch.object(shares, "dolt_commit")
    @patch.object(shares, "dsql")
    @patch.object(shares, "dsql_val")
    def test_successful_transfer(self, mock_val, mock_dsql, mock_commit, mock_table):
        mock_val.side_effect = [
            "Alice Smith",
            "Bob Chen",
            "100",  # holds 100
        ]
        shares.cmd_transfer(["alice", "bob", "ordinary", "10"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("transfer-out", sql)
        self.assertIn("transfer-in", sql)
        self.assertIn("'alice'", sql)
        self.assertIn("'bob'", sql)
        mock_commit.assert_called_once()


class TestCmdCheck(unittest.TestCase):
    """Test shares consistency check."""

    @patch.object(shares, "dsql_csv")
    def test_clean_check_passes(self, mock_csv):
        mock_csv.side_effect = [[], [], [], []]  # no errors in any check
        shares.cmd_check()

    @patch.object(shares, "dsql_csv")
    def test_bad_holders_fails(self, mock_csv):
        mock_csv.side_effect = [
            ["unknown_holder"],  # bad holders
            [],  # no bad classes
            [],  # no negative
            [],  # no over-issued
        ]
        with self.assertRaises(SystemExit):
            shares.cmd_check()

    @patch.object(shares, "dsql_csv")
    def test_bad_classes_fails(self, mock_csv):
        mock_csv.side_effect = [
            [],  # no bad holders
            ["phantom_class"],  # bad classes
            [],
            [],
        ]
        with self.assertRaises(SystemExit):
            shares.cmd_check()

    @patch.object(shares, "dsql_csv")
    def test_negative_holdings_fails(self, mock_csv):
        mock_csv.side_effect = [
            [],
            [],
            ["alice,ordinary,-50"],  # negative holdings
            [],
        ]
        with self.assertRaises(SystemExit):
            shares.cmd_check()

    @patch.object(shares, "dsql_csv")
    def test_over_issued_fails(self, mock_csv):
        mock_csv.side_effect = [
            [],
            [],
            [],
            ["ordinary,10000,15000"],  # over issued
        ]
        with self.assertRaises(SystemExit):
            shares.cmd_check()


class TestCmdAddHolder(unittest.TestCase):
    """Test add-holder command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_add_holder(["alice"])

    @patch.object(shares, "dsql_val")
    def test_duplicate_holder_exits(self, mock_val):
        mock_val.return_value = "alice"  # already exists
        with self.assertRaises(SystemExit):
            shares.cmd_add_holder(["alice", "Alice Smith"])

    @patch.object(shares, "dolt_commit")
    @patch.object(shares, "dsql")
    @patch.object(shares, "dsql_val")
    def test_successful_add(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = ""  # doesn't exist
        shares.cmd_add_holder(["alice", "Alice Smith"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("INSERT INTO holders", sql)
        self.assertIn("'alice'", sql)
        self.assertIn("'Alice Smith'", sql)

    @patch.object(shares, "dolt_commit")
    @patch.object(shares, "dsql")
    @patch.object(shares, "dsql_val")
    def test_escapes_quotes_in_name(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = ""
        shares.cmd_add_holder(["bob", "Bob O'Brien"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("Bob O''Brien", sql)


class TestCmdAddPool(unittest.TestCase):
    """Test add-pool command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_add_pool(["esop"])

    @patch.object(shares, "dsql_val")
    def test_unknown_class_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            shares.cmd_add_pool(["esop", "phantom", "1000"])

    @patch.object(shares, "dolt_commit")
    @patch.object(shares, "dsql")
    @patch.object(shares, "dsql_val")
    def test_successful_add(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "10000"  # class exists
        shares.cmd_add_pool(["esop", "ordinary", "1000"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("INSERT INTO pools", sql)


class TestCmdPoolAdd(unittest.TestCase):
    """Test pool-add command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_pool_add(["esop"])

    @patch.object(shares, "dsql_val")
    def test_unknown_pool_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            shares.cmd_pool_add(["phantom", "alice"])

    @patch.object(shares, "dsql_val")
    def test_unknown_holder_exits(self, mock_val):
        mock_val.side_effect = ["esop", ""]  # pool exists, holder doesn't
        with self.assertRaises(SystemExit):
            shares.cmd_pool_add(["esop", "nobody"])


class TestCmdBrief(unittest.TestCase):
    """Test brief context dump."""

    @patch.object(shares, "dsql_rows")
    def test_outputs_context(self, mock_rows):
        mock_rows.side_effect = [
            [{"name": "ordinary", "nominal_value": "0.01", "nominal_currency": "GBP", "authorised": "10000"}],
            [{"id": "richard", "display_name": "Richard"}],
            [{"holder": "Richard", "class": "ordinary", "held": "1000", "pct": "100.0"}],
            [{"class": "ordinary", "issued": "1000", "authorised": "10000", "available": "9000"}],
        ]
        # Should not raise
        shares.cmd_brief()


class TestRouting(unittest.TestCase):
    """Test main() dispatch."""

    @patch.object(shares, "cmd_table")
    def test_route_table(self, mock_cmd):
        with patch("sys.argv", ["shares", "table"]):
            shares.main()
        mock_cmd.assert_called_once()

    @patch.object(shares, "cmd_grant")
    def test_route_grant(self, mock_cmd):
        with patch("sys.argv", ["shares", "grant", "alice", "ordinary", "100"]):
            shares.main()
        mock_cmd.assert_called_once_with(["alice", "ordinary", "100"])

    @patch.object(shares, "cmd_transfer")
    def test_route_transfer(self, mock_cmd):
        with patch("sys.argv", ["shares", "transfer", "a", "b", "ordinary", "10"]):
            shares.main()
        mock_cmd.assert_called_once_with(["a", "b", "ordinary", "10"])

    @patch.object(shares, "cmd_check")
    def test_route_check(self, mock_cmd):
        with patch("sys.argv", ["shares", "check"]):
            shares.main()
        mock_cmd.assert_called_once()

    @patch.object(shares, "cmd_help")
    def test_route_unknown_shows_help(self, mock_cmd):
        with patch("sys.argv", ["shares", "garbage"]):
            shares.main()
        mock_cmd.assert_called_once()

    @patch.object(shares, "cmd_pdf")
    def test_route_pdf(self, mock_cmd):
        with patch("sys.argv", ["shares", "pdf", "table"]):
            shares.main()
        mock_cmd.assert_called_once_with(["table"])


class TestPdfMarkdown(unittest.TestCase):
    """Test PDF markdown generation (without actually generating PDFs)."""

    @patch.object(shares, "generate_pdf")
    @patch.object(shares, "dsql_rows")
    @patch.object(shares, "dsql_val")
    def test_pdf_table_with_data(self, mock_val, mock_rows, mock_pdf):
        mock_val.return_value = "1000"
        mock_rows.return_value = [
            {"holder": "Richard", "class": "ordinary", "held": "1000", "pct": "100.0"}
        ]
        shares.cmd_pdf_table()
        md = mock_pdf.call_args[0][1]
        self.assertIn("Cap Table", md)
        self.assertIn("Richard", md)
        self.assertIn("1000", md)

    @patch.object(shares, "generate_pdf")
    @patch.object(shares, "dsql_val")
    def test_pdf_table_empty(self, mock_val, mock_pdf):
        mock_val.return_value = "0"
        shares.cmd_pdf_table()
        md = mock_pdf.call_args[0][1]
        self.assertIn("No shares issued", md)

    @patch.object(shares, "generate_pdf")
    @patch.object(shares, "dsql_rows")
    def test_pdf_history(self, mock_rows, mock_pdf):
        mock_rows.return_value = [
            {
                "event_date": "2024-06-01",
                "event_type": "grant",
                "display_name": "Richard",
                "share_class": "ordinary",
                "quantity": "1000",
            }
        ]
        shares.cmd_pdf_history()
        md = mock_pdf.call_args[0][1]
        self.assertIn("Share History", md)
        self.assertIn("grant", md)
        self.assertIn("Richard", md)

    @patch.object(shares, "generate_pdf")
    @patch.object(shares, "dsql_rows")
    @patch.object(shares, "dsql_val")
    def test_pdf_holder(self, mock_val, mock_rows, mock_pdf):
        mock_val.side_effect = [
            "Richard",  # display_name lookup
            # cap_table rows handled by dsql_rows
        ]
        mock_rows.side_effect = [
            [{"class": "ordinary", "held": "1000", "pct": "100.0"}],
        ]
        # Need to also mock the second dsql_val call and dsql_rows
        mock_val.side_effect = ["Richard", "1000"]
        mock_rows.side_effect = [
            [{"class": "ordinary", "held": "1000", "pct": "100.0"}],
            [{"event_date": "2024-06-01", "event_type": "grant", "share_class": "ordinary", "quantity": "1000"}],
        ]
        shares.cmd_pdf_holder("richard")
        md = mock_pdf.call_args[0][1]
        self.assertIn("Holder Statement", md)
        self.assertIn("Richard", md)

    def test_pdf_holder_no_id_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_pdf_holder("")

    @patch.object(shares, "dsql_val")
    def test_pdf_holder_unknown_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            shares.cmd_pdf_holder("nobody")


if __name__ == "__main__":
    unittest.main()
