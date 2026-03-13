"""Tests for datalib — shared CSV data layer."""

import csv
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules", "data", "scripts"))
import datalib


# ---------------------------------------------------------------------------
# Type coercion
# ---------------------------------------------------------------------------

class TestCoerceTypes(unittest.TestCase):
    def test_integer(self):
        self.assertEqual(datalib._coerce_types({"v": "42"})["v"], 42)

    def test_negative_integer(self):
        self.assertEqual(datalib._coerce_types({"v": "-5"})["v"], -5)

    def test_float(self):
        self.assertAlmostEqual(datalib._coerce_types({"v": "3.14"})["v"], 3.14)

    def test_bool_true(self):
        self.assertIs(datalib._coerce_types({"v": "true"})["v"], True)

    def test_bool_false(self):
        self.assertIs(datalib._coerce_types({"v": "false"})["v"], False)

    def test_string(self):
        self.assertEqual(datalib._coerce_types({"v": "hello"})["v"], "hello")

    def test_empty_string(self):
        self.assertEqual(datalib._coerce_types({"v": ""})["v"], "")

    def test_date_stays_string(self):
        self.assertEqual(datalib._coerce_types({"v": "2026-03-01"})["v"], "2026-03-01")

    def test_path_stays_string(self):
        self.assertEqual(datalib._coerce_types({"v": "assets:bank:tide"})["v"], "assets:bank:tide")

    def test_leading_zeros_stay_string(self):
        # "007" should not become 7
        self.assertEqual(datalib._coerce_types({"v": "007"})["v"], "007")


class TestCsvVal(unittest.TestCase):
    def test_bool_true(self):
        self.assertEqual(datalib._csv_val(True), "true")

    def test_bool_false(self):
        self.assertEqual(datalib._csv_val(False), "false")

    def test_int_passthrough(self):
        self.assertEqual(datalib._csv_val(42), 42)

    def test_string_passthrough(self):
        self.assertEqual(datalib._csv_val("hello"), "hello")


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
                {"name": "test", "count": 42, "price": 9.99, "active": True, "date": "2026-01-01"},
            ],
        }
        datalib.save("test", data)
        loaded = datalib.load("test")
        row = loaded["rows"][0]
        self.assertEqual(row["name"], "test")
        self.assertEqual(row["count"], 42)
        self.assertAlmostEqual(row["price"], 9.99)
        self.assertIs(row["active"], True)
        self.assertEqual(row["date"], "2026-01-01")

    def test_empty_table_removes_file(self):
        datalib.save("test", {"items": [{"v": 1}]})
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "test", "items.csv")))
        datalib.save("test", {"items": []})
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "test", "items.csv")))

    def test_load_ignores_non_csv(self):
        domain_dir = os.path.join(self.tmpdir, "test")
        os.makedirs(domain_dir)
        with open(os.path.join(domain_dir, "notes.txt"), "w") as f:
            f.write("ignore me")
        with open(os.path.join(domain_dir, "items.csv"), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id"])
            writer.writeheader()
            writer.writerow({"id": "a"})
        loaded = datalib.load("test")
        self.assertIn("items", loaded)
        self.assertNotIn("notes", loaded)


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
# contract_summary()
# ---------------------------------------------------------------------------

class TestContractSummary(unittest.TestCase):
    def test_no_contracts(self):
        data = {"customers": [], "contracts": [], "contract_lines": [], "contract_clauses": []}
        self.assertEqual(datalib.contract_summary(data), [])

    def test_mrr_calculation_monthly(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS", "status": "active"}],
            "contract_lines": [
                {"contract_id": "ct-1", "seq": 1, "description": "Licence",
                 "quantity": 1, "unit_price": 200.0, "frequency": "monthly"},
            ],
            "contract_clauses": [],
        }
        result = datalib.contract_summary(data)
        self.assertEqual(result[0]["mrr"], 200.0)
        self.assertEqual(result[0]["company"], "Acme Corp")

    def test_mrr_calculation_quarterly(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS", "status": "active"}],
            "contract_lines": [
                {"contract_id": "ct-1", "seq": 1, "description": "Support",
                 "quantity": 1, "unit_price": 300.0, "frequency": "quarterly"},
            ],
            "contract_clauses": [],
        }
        result = datalib.contract_summary(data)
        self.assertEqual(result[0]["mrr"], 100.0)

    def test_mrr_calculation_annual(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS", "status": "active"}],
            "contract_lines": [
                {"contract_id": "ct-1", "seq": 1, "description": "Annual",
                 "quantity": 1, "unit_price": 1200.0, "frequency": "annual"},
            ],
            "contract_clauses": [],
        }
        result = datalib.contract_summary(data)
        self.assertEqual(result[0]["mrr"], 100.0)

    def test_one_off_not_in_mrr(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS", "status": "active"}],
            "contract_lines": [
                {"contract_id": "ct-1", "seq": 1, "description": "Setup",
                 "quantity": 1, "unit_price": 5000.0, "frequency": "one-off"},
            ],
            "contract_clauses": [],
        }
        result = datalib.contract_summary(data)
        self.assertEqual(result[0]["mrr"], 0.0)

    def test_line_and_clause_counts(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS", "status": "active"}],
            "contract_lines": [
                {"contract_id": "ct-1", "seq": 1, "description": "A", "quantity": 1, "unit_price": 100, "frequency": "monthly"},
                {"contract_id": "ct-1", "seq": 2, "description": "B", "quantity": 1, "unit_price": 50, "frequency": "monthly"},
            ],
            "contract_clauses": [
                {"contract_id": "ct-1", "seq": 1, "heading": "Terms", "body": "..."},
            ],
        }
        result = datalib.contract_summary(data)
        self.assertEqual(result[0]["line_count"], 2)
        self.assertEqual(result[0]["clause_count"], 1)


# ---------------------------------------------------------------------------
# renewals_due()
# ---------------------------------------------------------------------------

class TestRenewalsDue(unittest.TestCase):
    def test_no_active_contracts(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS",
                           "status": "draft", "effective_date": "2024-01-01", "term_months": 1}],
        }
        self.assertEqual(datalib.renewals_due(data), [])

    def test_far_future_not_included(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS",
                           "status": "active", "effective_date": "2026-01-01", "term_months": 120}],
        }
        self.assertEqual(datalib.renewals_due(data), [])

    def test_missing_effective_date_skipped(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contracts": [{"id": "ct-1", "customer_id": "acme", "title": "SaaS",
                           "status": "active", "term_months": 1}],
        }
        self.assertEqual(datalib.renewals_due(data), [])


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

    def test_clean_crm_data(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contacts": [{"id": "acme-jane", "customer_id": "acme", "name": "Jane"}],
            "contracts": [{"id": "ct-acme-1", "customer_id": "acme", "title": "SaaS"}],
            "contract_lines": [{"contract_id": "ct-acme-1", "seq": 1, "description": "Licence",
                                "quantity": 1, "unit_price": 100, "frequency": "monthly"}],
            "contract_clauses": [{"contract_id": "ct-acme-1", "seq": 1, "heading": "Terms", "body": "..."}],
        }
        self.assertEqual(datalib.validate_refs("crm", data), [])

    def test_orphan_customer_in_contracts(self):
        data = {
            "customers": [],
            "contacts": [],
            "contracts": [{"id": "ct-1", "customer_id": "ghost", "title": "SaaS"}],
            "contract_lines": [],
            "contract_clauses": [],
        }
        errors = datalib.validate_refs("crm", data)
        self.assertTrue(any("ghost" in e for e in errors))

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
