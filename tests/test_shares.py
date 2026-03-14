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


class TestModelRound(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_model_round(["500000"])

    @patch("datalib.load")
    def test_no_shares_exits(self, mock_load):
        mock_load.return_value = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "holders": [],
            "share_events": [],
        }
        with self.assertRaises(SystemExit):
            shares.cmd_model_round(["500000", "2000000"])

    @patch("datalib.load")
    def test_dilution_math(self, mock_load):
        mock_load.return_value = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "holders": [
                {"id": "alice", "display_name": "Alice"},
                {"id": "bob", "display_name": "Bob"},
            ],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 750},
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "bob", "share_class": "ordinary", "quantity": 250},
            ],
        }
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            shares.cmd_model_round(["500000", "2000000"])
        output = buf.getvalue()
        # post_money = 2500000, dilution = 500000/2500000 = 20%
        self.assertIn("20.0%", output)
        # new_shares = 1000 * 500000 / 2000000 = 250
        self.assertIn("250", output)
        # post_total = 1000 + 250 = 1250
        # alice pre: 75%, post: 750/1250 = 60%
        self.assertIn("60.0%", output)
        # bob pre: 25%, post: 250/1250 = 20%
        # (20.0% appears for both dilution and bob post — check bob's line)
        self.assertIn("Bob", output)

    @patch("datalib.load")
    def test_equal_split_dilution(self, mock_load):
        """50/50 split with investment equal to pre-money => 50% dilution."""
        mock_load.return_value = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 1000},
            ],
        }
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            shares.cmd_model_round(["1000000", "1000000"])
        output = buf.getvalue()
        # dilution = 1000000/2000000 = 50%
        self.assertIn("50.0%", output)
        # new_shares = 1000 * 1000000 / 1000000 = 1000
        # alice post: 1000/2000 = 50%
        lines = output.split("\n")
        alice_line = [l for l in lines if "Alice" in l][0]
        self.assertIn("50.0%", alice_line)


class TestModelPoolExpand(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            shares.cmd_model_pool_expand(["founder"])

    @patch("datalib.load")
    def test_unknown_pool_exits(self, mock_load):
        mock_load.return_value = SHARE_DATA
        with self.assertRaises(SystemExit):
            shares.cmd_model_pool_expand(["nonexistent", "500"])

    @patch("datalib.load")
    def test_expansion_math(self, mock_load):
        mock_load.return_value = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 1000},
            ],
            "pools": [{"name": "esop", "share_class": "ordinary", "budget": 500}],
            "pool_members": [],
        }
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            shares.cmd_model_pool_expand(["esop", "500"])
        output = buf.getvalue()
        # new_budget = 500 + 500 = 1000
        self.assertIn("1,000", output)
        # post_total = 1000 + 500 = 1500
        # alice post: 1000/1500 = 66.7%
        lines = output.split("\n")
        alice_line = [l for l in lines if "Alice" in l][0]
        self.assertIn("66.7%", alice_line)
        # pool expansion: 500/1500 = 33.3%
        expansion_line = [l for l in lines if "Pool expansion" in l][0]
        self.assertIn("33.3%", expansion_line)

    @patch("datalib.load")
    def test_expansion_budget_display(self, mock_load):
        mock_load.return_value = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 1000},
            ],
            "pools": [{"name": "esop", "share_class": "ordinary", "budget": 200}],
            "pool_members": [],
        }
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            shares.cmd_model_pool_expand(["esop", "300"])
        output = buf.getvalue()
        self.assertIn("Current budget:", output)
        self.assertIn("200", output)
        self.assertIn("300", output)
        self.assertIn("500", output)  # new budget


class TestVestedLookup(unittest.TestCase):
    def test_no_vesting_returns_full_holdings(self):
        """Grants without vesting params are fully vested."""
        data = {
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            ],
        }
        lookup = shares._vested_lookup(data)
        self.assertEqual(lookup[("alice", "ordinary")], 100)

    def test_caps_at_holdings_after_transfer(self):
        """If holder transferred shares away, vested should be capped at current holdings."""
        from datetime import date, timedelta
        # Grant with vesting started long ago (fully vested)
        start = (date.today() - timedelta(days=1500)).isoformat()
        data = {
            "holders": [
                {"id": "alice", "display_name": "Alice"},
                {"id": "bob", "display_name": "Bob"},
            ],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 1000,
                 "vesting_start": start, "vesting_months": 12, "cliff_months": 0},
                # Alice transfers 600 away — now holds 400
                {"event_date": "2025-01-01", "event_type": "transfer-out",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 600},
                {"event_date": "2025-01-01", "event_type": "transfer-in",
                 "holder_id": "bob", "share_class": "ordinary", "quantity": 600},
            ],
        }
        lookup = shares._vested_lookup(data)
        # alice vested = 1000 (fully vested) but holds 400 => capped at 400
        self.assertEqual(lookup[("alice", "ordinary")], 400)

    def test_multiple_grants_aggregate(self):
        """Multiple grants to same holder/class should aggregate vested amounts."""
        data = {
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
                {"event_date": "2024-06-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 200},
            ],
        }
        lookup = shares._vested_lookup(data)
        # Both fully vested (no vesting params)
        self.assertEqual(lookup[("alice", "ordinary")], 300)

    def test_empty_events(self):
        data = {"holders": [], "share_events": []}
        lookup = shares._vested_lookup(data)
        self.assertEqual(lookup, {})

    def test_pre_cliff_vested_zero(self):
        """Before cliff, vested should be 0 but lookup still capped at holdings."""
        from datetime import date, timedelta
        start = (date.today() - timedelta(days=30)).isoformat()
        data = {
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 480,
                 "vesting_start": start, "vesting_months": 48, "cliff_months": 12},
            ],
        }
        lookup = shares._vested_lookup(data)
        # Before cliff: vested = 0, holdings = 480, min(0, 480) = 0
        self.assertEqual(lookup[("alice", "ordinary")], 0)

    def test_multiple_classes_separate(self):
        data = {
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "preference", "quantity": 50},
            ],
        }
        lookup = shares._vested_lookup(data)
        self.assertEqual(lookup[("alice", "ordinary")], 100)
        self.assertEqual(lookup[("alice", "preference")], 50)


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
