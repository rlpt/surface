"""Tests for shares module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

shares = import_script("shares", "shares")

# Shared test data
SHARE_DATA = {
    "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "nominal_currency": "GBP", "authorised": 10000}],
    "holders": [
        {"id": "richard", "display_name": "Richard Targett"},
        {"id": "mark", "display_name": "Mark Holland"},
    ],
    "share_events": [
        {"event_date": "2024-06-01", "event_type": "grant", "holder_id": "richard", "share_class": "ordinary", "quantity": 1000},
    ],
    "pools": [{"name": "founder", "share_class": "ordinary", "budget": 8000}],
    "pool_members": [{"pool_name": "founder", "holder_id": "richard"}],
}


class TestCmdGrant(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["alice"])

    @patch("datalib.load")
    def test_unknown_holder_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["nobody", "ordinary", "100"])

    @patch("datalib.load")
    def test_unknown_class_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["richard", "phantom", "100"])

    @patch("datalib.load")
    def test_insufficient_shares_exits(self, mock_load):
        data = {
            **SHARE_DATA,
            "share_events": [
                {"event_date": "2024-06-01", "event_type": "grant", "holder_id": "richard",
                 "share_class": "ordinary", "quantity": 9990},
            ],
        }
        mock_load.return_value = data
        with self.assertRaises(SystemExit):
            shares.cmd_grant(["richard", "ordinary", "100"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    @patch.object(shares, "cmd_table")
    def test_successful_grant(self, mock_table, mock_load, mock_save, mock_commit):
        mock_load.return_value = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "nominal_currency": "GBP", "authorised": 10000}],
            "holders": [{"id": "richard", "display_name": "Richard Targett"}],
            "share_events": [
                {"event_date": "2024-06-01", "event_type": "grant", "holder_id": "richard", "share_class": "ordinary", "quantity": 1000},
            ],
            "pools": [],
            "pool_members": [],
        }
        shares.cmd_grant(["richard", "ordinary", "500"])
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][1]
        last_event = saved_data["share_events"][-1]
        self.assertEqual(last_event["event_type"], "grant")
        self.assertEqual(last_event["holder_id"], "richard")
        self.assertEqual(last_event["quantity"], 500)
        mock_commit.assert_called_once()


class TestCmdTransfer(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["alice", "bob"])

    @patch("datalib.load")
    def test_unknown_source_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["nobody", "mark", "ordinary", "10"])

    @patch("datalib.load")
    def test_unknown_target_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["richard", "nobody", "ordinary", "10"])

    @patch("datalib.load")
    def test_insufficient_holdings_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA  # richard holds 1000
        with self.assertRaises(SystemExit):
            shares.cmd_transfer(["richard", "mark", "ordinary", "5000"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    @patch.object(shares, "cmd_table")
    def test_successful_transfer(self, mock_table, mock_load, mock_save, mock_commit):
        mock_load.return_value = dict(SHARE_DATA)
        shares.cmd_transfer(["richard", "mark", "ordinary", "10"])
        saved_data = mock_save.call_args[0][1]
        events = saved_data["share_events"]
        self.assertEqual(events[-2]["event_type"], "transfer-out")
        self.assertEqual(events[-1]["event_type"], "transfer-in")
        mock_commit.assert_called_once()


class TestCmdCheck(unittest.TestCase):
    @patch("datalib.load")
    def test_clean_check_passes(self, mock_load):
        mock_load.return_value = SHARE_DATA
        shares.cmd_check()

    @patch("datalib.load")
    def test_bad_holders_fails(self, mock_load):
        data = dict(SHARE_DATA)
        data["share_events"] = [
            {"event_date": "2024-06-01", "event_type": "grant", "holder_id": "nobody",
             "share_class": "ordinary", "quantity": 100},
        ]
        mock_load.return_value = data
        with self.assertRaises(SystemExit):
            shares.cmd_check()

    @patch("datalib.load")
    def test_negative_holdings_fails(self, mock_load):
        data = dict(SHARE_DATA)
        data["share_events"] = [
            {"event_date": "2024-06-01", "event_type": "transfer-out", "holder_id": "richard",
             "share_class": "ordinary", "quantity": 100},
        ]
        mock_load.return_value = data
        with self.assertRaises(SystemExit):
            shares.cmd_check()


class TestCmdAddHolder(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_add_holder(["alice"])

    @patch("datalib.load")
    def test_duplicate_holder_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_add_holder(["richard", "Richard Targett"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_successful_add(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = dict(SHARE_DATA)
        shares.cmd_add_holder(["alice", "Alice Smith"])
        saved_data = mock_save.call_args[0][1]
        holders = saved_data["holders"]
        self.assertTrue(any(h["id"] == "alice" for h in holders))


class TestCmdAddPool(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_add_pool(["esop"])

    @patch("datalib.load")
    def test_unknown_class_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_add_pool(["esop", "phantom", "1000"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_successful_add(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = dict(SHARE_DATA)
        shares.cmd_add_pool(["esop", "ordinary", "1000"])
        mock_save.assert_called_once()


class TestCmdPoolAdd(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_pool_add(["esop"])

    @patch("datalib.load")
    def test_unknown_pool_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_pool_add(["phantom", "richard"])

    @patch("datalib.load")
    def test_unknown_holder_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_pool_add(["founder", "nobody"])


class TestCmdBrief(unittest.TestCase):
    @patch("datalib.load")
    def test_outputs_context(self, mock_load):
        mock_load.return_value = SHARE_DATA
        shares.cmd_brief()


class TestRouting(unittest.TestCase):
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
    @patch.object(shares, "generate_pdf")
    @patch("datalib.load")
    def test_pdf_table_with_data(self, mock_load, mock_pdf):
        mock_load.return_value = SHARE_DATA
        shares.cmd_pdf_table()
        md = mock_pdf.call_args[0][1]
        self.assertIn("Cap Table", md)
        self.assertIn("Richard Targett", md)
        self.assertIn("1000", md)

    @patch.object(shares, "generate_pdf")
    @patch("datalib.load")
    def test_pdf_table_empty(self, mock_load, mock_pdf):
        mock_load.return_value = {"share_classes": [], "holders": [], "share_events": []}
        shares.cmd_pdf_table()
        md = mock_pdf.call_args[0][1]
        self.assertIn("No shares issued", md)

    @patch.object(shares, "generate_pdf")
    @patch("datalib.load")
    def test_pdf_history(self, mock_load, mock_pdf):
        mock_load.return_value = SHARE_DATA
        shares.cmd_pdf_history()
        md = mock_pdf.call_args[0][1]
        self.assertIn("Share History", md)
        self.assertIn("grant", md)

    @patch.object(shares, "generate_pdf")
    @patch("datalib.load")
    def test_pdf_holder(self, mock_load, mock_pdf):
        mock_load.return_value = SHARE_DATA
        shares.cmd_pdf_holder("richard")
        md = mock_pdf.call_args[0][1]
        self.assertIn("Holder Statement", md)
        self.assertIn("Richard Targett", md)

    def test_pdf_holder_no_id_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_pdf_holder("")

    @patch("datalib.load")
    def test_pdf_holder_unknown_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_pdf_holder("nobody")


if __name__ == "__main__":
    unittest.main()
