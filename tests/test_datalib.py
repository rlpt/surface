"""Tests for datalib — shared YAML data layer."""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules", "data", "scripts"))
import datalib


# ---------------------------------------------------------------------------
# Load / save (with temp files)
# ---------------------------------------------------------------------------

class TestLoadSave(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_data_dir = datalib.DATA_DIR
        datalib.DATA_DIR = self.tmpdir

    def tearDown(self):
        datalib.DATA_DIR = self._orig_data_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_missing_domain(self):
        result = datalib.load("nonexistent")
        self.assertEqual(result, {})

    def test_save_and_load(self):
        data = {
            "holders": [
                {"id": "alice", "display_name": "Alice"},
                {"id": "bob", "display_name": "Bob"},
            ],
        }
        datalib.save("test", data)
        loaded = datalib.load("test")
        self.assertEqual(len(loaded["holders"]), 2)
        self.assertEqual(loaded["holders"][0]["id"], "alice")

    def test_save_overwrites(self):
        datalib.save("test", {"items": [{"v": 1}]})
        datalib.save("test", {"items": [{"v": 2}]})
        loaded = datalib.load("test")
        self.assertEqual(loaded["items"][0]["v"], 2)

    def test_round_trip_types(self):
        data = {
            "rows": [
                {"name": "test", "count": 42, "price": 9.99, "active": True,
                 "event_date": "2026-01-01"},
            ],
        }
        datalib.save("test", data)
        loaded = datalib.load("test")
        row = loaded["rows"][0]
        self.assertEqual(row["name"], "test")
        self.assertEqual(row["count"], 42)
        self.assertAlmostEqual(row["price"], 9.99)
        self.assertIs(row["active"], True)
        self.assertEqual(row["event_date"], "2026-01-01")

    def test_empty_list_preserved(self):
        datalib.save("test", {"items": []})
        loaded = datalib.load("test")
        self.assertEqual(loaded["items"], [])

    def test_date_round_trip(self):
        """Dates in YAML are loaded as date objects but normalised to ISO strings."""
        data = {
            "share_events": [
                {"event_date": "2024-06-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            ],
        }
        datalib.save("test", data)
        loaded = datalib.load("test")
        self.assertEqual(loaded["share_events"][0]["event_date"], "2024-06-01")
        self.assertIsInstance(loaded["share_events"][0]["event_date"], str)


# ---------------------------------------------------------------------------
# holdings()
# ---------------------------------------------------------------------------

class TestHoldings(unittest.TestCase):
    def test_empty_events(self):
        data = {"share_events": []}
        self.assertEqual(datalib.holdings(data), [])

    def test_single_grant(self):
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
        ]}
        h = datalib.holdings(data)
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0]["holder_id"], "alice")
        self.assertEqual(h[0]["shares_held"], 100)

    def test_grant_and_transfer(self):
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            {"event_date": "2024-02-01", "event_type": "transfer-out",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 30},
            {"event_date": "2024-02-01", "event_type": "transfer-in",
             "holder_id": "bob", "share_class": "ordinary", "quantity": 30},
        ]}
        h = datalib.holdings(data)
        by_holder = {r["holder_id"]: r["shares_held"] for r in h}
        self.assertEqual(by_holder["alice"], 70)
        self.assertEqual(by_holder["bob"], 30)

    def test_zero_holdings_excluded(self):
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            {"event_date": "2024-02-01", "event_type": "transfer-out",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            {"event_date": "2024-02-01", "event_type": "transfer-in",
             "holder_id": "bob", "share_class": "ordinary", "quantity": 100},
        ]}
        h = datalib.holdings(data)
        holder_ids = [r["holder_id"] for r in h]
        self.assertNotIn("alice", holder_ids)
        self.assertIn("bob", holder_ids)

    def test_multiple_classes(self):
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "preference", "quantity": 50},
        ]}
        h = datalib.holdings(data)
        self.assertEqual(len(h), 2)


# ---------------------------------------------------------------------------
# cap_table()
# ---------------------------------------------------------------------------

class TestCapTable(unittest.TestCase):
    def test_empty(self):
        data = {"share_events": [], "holders": []}
        self.assertEqual(datalib.cap_table(data), [])

    def test_percentages(self):
        data = {
            "holders": [
                {"id": "alice", "display_name": "Alice"},
                {"id": "bob", "display_name": "Bob"},
            ],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 75},
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "bob", "share_class": "ordinary", "quantity": 25},
            ],
        }
        cap = datalib.cap_table(data)
        by_holder = {r["holder"]: r for r in cap}
        self.assertEqual(by_holder["Alice"]["pct"], 75.0)
        self.assertEqual(by_holder["Bob"]["pct"], 25.0)
        self.assertEqual(by_holder["Alice"]["held"], 75)

    def test_unknown_holder_uses_id(self):
        data = {
            "holders": [],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "mystery", "share_class": "ordinary", "quantity": 100},
            ],
        }
        cap = datalib.cap_table(data)
        self.assertEqual(cap[0]["holder"], "mystery")


# ---------------------------------------------------------------------------
# class_availability()
# ---------------------------------------------------------------------------

class TestClassAvailability(unittest.TestCase):
    def test_no_shares_issued(self):
        data = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "share_events": [],
        }
        result = datalib.class_availability(data)
        self.assertEqual(result[0]["issued"], 0)
        self.assertEqual(result[0]["available"], 10000)

    def test_partial_issue(self):
        data = {
            "share_classes": [{"name": "ordinary", "authorised": 10000}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 3000},
            ],
        }
        result = datalib.class_availability(data)
        self.assertEqual(result[0]["issued"], 3000)
        self.assertEqual(result[0]["available"], 7000)


# ---------------------------------------------------------------------------
# account_balances()
# ---------------------------------------------------------------------------

class TestAccountBalances(unittest.TestCase):
    def test_no_postings(self):
        data = {"accounts": [{"path": "assets:bank", "account_type": "assets"}], "postings": []}
        result = datalib.account_balances(data)
        self.assertEqual(result, [])

    def test_balanced_transaction(self):
        data = {
            "accounts": [
                {"path": "expenses:hosting", "account_type": "expenses"},
                {"path": "assets:bank", "account_type": "assets"},
            ],
            "postings": [
                {"txn_id": 1, "account_path": "expenses:hosting", "amount": 45.0, "currency": "GBP"},
                {"txn_id": 1, "account_path": "assets:bank", "amount": -45.0, "currency": "GBP"},
            ],
        }
        result = datalib.account_balances(data)
        by_path = {r["account_path"]: r for r in result}
        self.assertEqual(by_path["expenses:hosting"]["balance"], 45.0)
        self.assertEqual(by_path["assets:bank"]["balance"], -45.0)

    def test_multiple_transactions_aggregate(self):
        data = {
            "accounts": [{"path": "expenses:hosting", "account_type": "expenses"}],
            "postings": [
                {"txn_id": 1, "account_path": "expenses:hosting", "amount": 45.0, "currency": "GBP"},
                {"txn_id": 2, "account_path": "expenses:hosting", "amount": 55.0, "currency": "GBP"},
            ],
        }
        result = datalib.account_balances(data)
        self.assertEqual(result[0]["balance"], 100.0)


# ---------------------------------------------------------------------------
# vesting_schedule()
# ---------------------------------------------------------------------------

class TestVestingSchedule(unittest.TestCase):
    def test_no_vesting_fully_vested(self):
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
        ]}
        result = datalib.vesting_schedule(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["vested"], 100)
        self.assertEqual(result[0]["unvested"], 0)
        self.assertEqual(result[0]["pct_vested"], 100.0)

    def test_vesting_in_progress(self):
        # Grant with 48-month vesting, 12-month cliff, started 24 months ago
        from datetime import date, timedelta
        start = date.today() - timedelta(days=730)  # ~24 months ago
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 480,
             "vesting_start": start.isoformat(), "vesting_months": 48,
             "cliff_months": 12},
        ]}
        result = datalib.vesting_schedule(data)
        self.assertEqual(len(result), 1)
        # Should be approximately half vested
        self.assertGreater(result[0]["vested"], 0)
        self.assertLess(result[0]["vested"], 480)
        self.assertEqual(result[0]["total_granted"], 480)

    def test_before_cliff(self):
        from datetime import date, timedelta
        start = date.today() - timedelta(days=30)  # 1 month ago
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "grant",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 480,
             "vesting_start": start.isoformat(), "vesting_months": 48,
             "cliff_months": 12},
        ]}
        result = datalib.vesting_schedule(data)
        self.assertEqual(result[0]["vested"], 0)

    def test_transfers_ignored(self):
        data = {"share_events": [
            {"event_date": "2024-01-01", "event_type": "transfer-in",
             "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
        ]}
        result = datalib.vesting_schedule(data)
        self.assertEqual(len(result), 0)


# ---------------------------------------------------------------------------
# compliance_upcoming()
# ---------------------------------------------------------------------------

class TestComplianceUpcoming(unittest.TestCase):
    def test_no_deadlines(self):
        data = {"deadlines": []}
        self.assertEqual(datalib.compliance_upcoming(data), [])

    def test_upcoming_within_90_days(self):
        from datetime import date, timedelta
        due = (date.today() + timedelta(days=30)).isoformat()
        data = {"deadlines": [
            {"id": "test-1", "title": "Test deadline", "due_date": due,
             "frequency": "annual", "category": "companies-house", "status": "upcoming"},
        ]}
        result = datalib.compliance_upcoming(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "test-1")

    def test_far_future_excluded(self):
        from datetime import date, timedelta
        due = (date.today() + timedelta(days=200)).isoformat()
        data = {"deadlines": [
            {"id": "test-1", "title": "Test deadline", "due_date": due,
             "frequency": "annual", "category": "companies-house", "status": "upcoming"},
        ]}
        result = datalib.compliance_upcoming(data)
        self.assertEqual(len(result), 0)

    def test_filed_excluded(self):
        from datetime import date, timedelta
        due = (date.today() + timedelta(days=30)).isoformat()
        data = {"deadlines": [
            {"id": "test-1", "title": "Test deadline", "due_date": due,
             "frequency": "annual", "category": "companies-house", "status": "filed"},
        ]}
        result = datalib.compliance_upcoming(data)
        self.assertEqual(len(result), 0)

    def test_overdue_marked(self):
        from datetime import date, timedelta
        due = (date.today() - timedelta(days=5)).isoformat()
        data = {"deadlines": [
            {"id": "test-1", "title": "Test deadline", "due_date": due,
             "frequency": "annual", "category": "hmrc", "status": "upcoming"},
        ]}
        result = datalib.compliance_upcoming(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "overdue")


# ---------------------------------------------------------------------------
# Referential integrity — validate_refs()
# ---------------------------------------------------------------------------

class TestValidateRefs(unittest.TestCase):
    def test_clean_shares_data(self):
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            ],
            "pools": [{"name": "founder", "share_class": "ordinary", "budget": 8000}],
            "pool_members": [{"pool_name": "founder", "holder_id": "alice"}],
        }
        self.assertEqual(datalib.validate_refs("shares", data), [])

    def test_orphan_holder_in_events(self):
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "authorised": 10000}],
            "holders": [],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "ghost", "share_class": "ordinary", "quantity": 100},
            ],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("ghost" in e for e in errors))

    def test_orphan_share_class_in_events(self):
        data = {
            "share_classes": [{"name": "ordinary"}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "phantom", "quantity": 100},
            ],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("phantom" in e for e in errors))

    def test_orphan_pool_member(self):
        data = {
            "share_classes": [{"name": "ordinary"}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [],
            "pools": [{"name": "founder", "share_class": "ordinary", "budget": 8000}],
            "pool_members": [{"pool_name": "founder", "holder_id": "ghost"}],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("ghost" in e for e in errors))

    def test_clean_accounts_data(self):
        data = {
            "accounts": [{"path": "expenses:hosting", "account_type": "expenses"}],
            "transactions": [{"id": 1, "txn_date": "2026-01-01", "payee": "AWS", "description": "Hosting"}],
            "postings": [
                {"txn_id": 1, "account_path": "expenses:hosting", "amount": 45.0, "currency": "GBP"},
            ],
        }
        self.assertEqual(datalib.validate_refs("accounts", data), [])

    def test_orphan_account_in_postings(self):
        data = {
            "accounts": [{"path": "expenses:hosting", "account_type": "expenses"}],
            "transactions": [],
            "postings": [
                {"txn_id": 1, "account_path": "expenses:unknown", "amount": 45.0, "currency": "GBP"},
            ],
        }
        errors = datalib.validate_refs("accounts", data)
        self.assertTrue(any("expenses:unknown" in e for e in errors))

    def test_clean_board_data(self):
        data = {
            "board_meetings": [{"id": "bm-2026-01-01", "meeting_date": "2026-01-01", "title": "Q1"}],
            "board_attendees": [{"meeting_id": "bm-2026-01-01", "person_name": "Alice", "role": "chair"}],
            "board_minutes": [{"meeting_id": "bm-2026-01-01", "seq": 1, "item_text": "Called to order"}],
            "board_resolutions": [{"id": "bm-2026-01-01-r1", "meeting_id": "bm-2026-01-01",
                                   "resolution_text": "Approve", "status": "passed"}],
        }
        self.assertEqual(datalib.validate_refs("board", data), [])

    def test_orphan_meeting_in_attendees(self):
        data = {
            "board_meetings": [],
            "board_attendees": [{"meeting_id": "bm-nope", "person_name": "Alice", "role": "chair"}],
            "board_minutes": [],
            "board_resolutions": [],
        }
        errors = datalib.validate_refs("board", data)
        self.assertTrue(any("bm-nope" in e for e in errors))

    def test_unknown_domain_returns_empty(self):
        self.assertEqual(datalib.validate_refs("unknown", {}), [])


# ---------------------------------------------------------------------------
# lint()
# ---------------------------------------------------------------------------

class TestLint(unittest.TestCase):
    def test_clean_shares_data(self):
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01,
                               "nominal_currency": "GBP", "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            ],
            "pools": [{"name": "founder", "share_class": "ordinary", "budget": 8000}],
            "pool_members": [{"pool_name": "founder", "holder_id": "alice"}],
        }
        self.assertEqual(datalib.lint("shares", data), [])

    def test_missing_required_field(self):
        data = {
            "holders": [{"id": "alice"}],  # missing display_name
        }
        errors = datalib.lint("shares", data)
        self.assertTrue(any("display_name" in e for e in errors))

    def test_wrong_type(self):
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01,
                               "nominal_currency": "GBP", "authorised": "ten thousand"}],
        }
        errors = datalib.lint("shares", data)
        self.assertTrue(any("authorised" in e for e in errors))

    def test_invalid_enum(self):
        data = {
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "steal",
                 "holder_id": "alice", "share_class": "ordinary", "quantity": 100},
            ],
        }
        errors = datalib.lint("shares", data)
        self.assertTrue(any("steal" in e for e in errors))

    def test_invalid_account_type(self):
        data = {
            "accounts": [{"path": "misc:stuff", "account_type": "magic"}],
        }
        errors = datalib.lint("accounts", data)
        self.assertTrue(any("magic" in e for e in errors))

    def test_unknown_domain_no_errors(self):
        self.assertEqual(datalib.lint("unknown", {"foo": [{"a": 1}]}), [])


# ---------------------------------------------------------------------------
# print_table()
# ---------------------------------------------------------------------------

class TestPrintTable(unittest.TestCase):
    def test_empty_rows(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            datalib.print_table([])
        self.assertIn("No data", buf.getvalue())

    def test_formats_columns(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            datalib.print_table([{"name": "Alice", "age": 30}])
        output = buf.getvalue()
        self.assertIn("name", output)
        self.assertIn("Alice", output)
        self.assertIn("30", output)


if __name__ == "__main__":
    unittest.main()
