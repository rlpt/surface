"""Tests for datalib — shared TOML data layer."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules", "data", "scripts"))
import datalib


# ---------------------------------------------------------------------------
# dump_toml / round-trip
# ---------------------------------------------------------------------------

class TestDumpToml(unittest.TestCase):
    def test_empty_data(self):
        self.assertEqual(datalib.dump_toml({}), "")

    def test_array_of_tables(self):
        data = {"items": [{"name": "a", "value": 1}]}
        result = datalib.dump_toml(data)
        self.assertIn("[[items]]", result)
        self.assertIn('name = "a"', result)
        self.assertIn("value = 1", result)

    def test_single_table(self):
        data = {"meta": {"version": 1, "name": "test"}}
        result = datalib.dump_toml(data)
        self.assertIn("[meta]", result)
        self.assertIn("version = 1", result)

    def test_bool_values(self):
        data = {"items": [{"flag": True, "other": False}]}
        result = datalib.dump_toml(data)
        self.assertIn("flag = true", result)
        self.assertIn("other = false", result)

    def test_float_values(self):
        data = {"items": [{"price": 19.99}]}
        result = datalib.dump_toml(data)
        self.assertIn("price = 19.99", result)

    def test_string_escaping(self):
        data = {"items": [{"name": 'O"Brien'}]}
        result = datalib.dump_toml(data)
        self.assertIn('name = "O\\"Brien"', result)

    def test_backslash_escaping(self):
        data = {"items": [{"path": "C:\\Users\\test"}]}
        result = datalib.dump_toml(data)
        self.assertIn("C:\\\\Users\\\\test", result)

    def test_multiple_tables(self):
        data = {
            "holders": [{"id": "a"}, {"id": "b"}],
            "events": [{"type": "grant"}],
        }
        result = datalib.dump_toml(data)
        self.assertEqual(result.count("[[holders]]"), 2)
        self.assertEqual(result.count("[[events]]"), 1)


class TestRoundTrip(unittest.TestCase):
    """Verify dump_toml output can be re-parsed by tomllib."""

    def test_round_trip_simple(self):
        import tomllib
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice Smith"}],
        }
        toml_str = datalib.dump_toml(data)
        parsed = tomllib.loads(toml_str)
        self.assertEqual(parsed["share_classes"][0]["name"], "ordinary")
        self.assertAlmostEqual(parsed["share_classes"][0]["nominal_value"], 0.01)
        self.assertEqual(parsed["holders"][0]["id"], "alice")

    def test_round_trip_booleans(self):
        import tomllib
        data = {"contracts": [{"auto_renew": True, "active": False}]}
        parsed = tomllib.loads(datalib.dump_toml(data))
        self.assertIs(parsed["contracts"][0]["auto_renew"], True)
        self.assertIs(parsed["contracts"][0]["active"], False)

    def test_round_trip_special_chars(self):
        import tomllib
        data = {"items": [{"text": 'He said "hello" & goodbye'}]}
        parsed = tomllib.loads(datalib.dump_toml(data))
        self.assertEqual(parsed["items"][0]["text"], 'He said "hello" & goodbye')


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
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_missing_file(self):
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
        errors = datalib.validate_refs("shares", data)
        self.assertEqual(errors, [])

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
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [
                {"event_date": "2024-01-01", "event_type": "grant",
                 "holder_id": "alice", "share_class": "phantom", "quantity": 100},
            ],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("phantom" in e for e in errors))

    def test_orphan_pool_class(self):
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "authorised": 10000}],
            "holders": [],
            "share_events": [],
            "pools": [{"name": "esop", "share_class": "phantom", "budget": 1000}],
            "pool_members": [],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("phantom" in e for e in errors))

    def test_orphan_pool_member(self):
        data = {
            "share_classes": [{"name": "ordinary", "nominal_value": 0.01, "authorised": 10000}],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [],
            "pools": [{"name": "founder", "share_class": "ordinary", "budget": 8000}],
            "pool_members": [{"pool_name": "founder", "holder_id": "ghost"}],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("ghost" in e for e in errors))

    def test_orphan_pool_name_in_members(self):
        data = {
            "share_classes": [],
            "holders": [{"id": "alice", "display_name": "Alice"}],
            "share_events": [],
            "pools": [],
            "pool_members": [{"pool_name": "nonexistent", "holder_id": "alice"}],
        }
        errors = datalib.validate_refs("shares", data)
        self.assertTrue(any("nonexistent" in e for e in errors))

    def test_clean_accounts_data(self):
        data = {
            "accounts": [{"path": "expenses:hosting", "account_type": "expenses"}],
            "transactions": [{"id": 1, "txn_date": "2026-01-01", "payee": "AWS", "description": "Hosting"}],
            "postings": [
                {"txn_id": 1, "account_path": "expenses:hosting", "amount": 45.0, "currency": "GBP"},
            ],
        }
        errors = datalib.validate_refs("accounts", data)
        self.assertEqual(errors, [])

    def test_orphan_account_in_postings(self):
        data = {
            "accounts": [{"path": "expenses:hosting", "account_type": "expenses"}],
            "transactions": [{"id": 1, "txn_date": "2026-01-01", "payee": "AWS", "description": "Hosting"}],
            "postings": [
                {"txn_id": 1, "account_path": "expenses:unknown", "amount": 45.0, "currency": "GBP"},
            ],
        }
        errors = datalib.validate_refs("accounts", data)
        self.assertTrue(any("expenses:unknown" in e for e in errors))

    def test_orphan_txn_in_postings(self):
        data = {
            "accounts": [{"path": "expenses:hosting", "account_type": "expenses"}],
            "transactions": [],
            "postings": [
                {"txn_id": 99, "account_path": "expenses:hosting", "amount": 45.0, "currency": "GBP"},
            ],
        }
        errors = datalib.validate_refs("accounts", data)
        self.assertTrue(any("99" in e for e in errors))

    def test_clean_crm_data(self):
        data = {
            "customers": [{"id": "acme", "company": "Acme Corp"}],
            "contacts": [{"id": "acme-jane", "customer_id": "acme", "name": "Jane"}],
            "contracts": [{"id": "ct-acme-1", "customer_id": "acme", "title": "SaaS"}],
            "contract_lines": [{"contract_id": "ct-acme-1", "seq": 1, "description": "Licence",
                                "quantity": 1, "unit_price": 100, "frequency": "monthly"}],
            "contract_clauses": [{"contract_id": "ct-acme-1", "seq": 1, "heading": "Terms", "body": "..."}],
        }
        errors = datalib.validate_refs("crm", data)
        self.assertEqual(errors, [])

    def test_orphan_customer_in_contacts(self):
        data = {
            "customers": [],
            "contacts": [{"id": "acme-jane", "customer_id": "acme", "name": "Jane"}],
            "contracts": [],
            "contract_lines": [],
            "contract_clauses": [],
        }
        errors = datalib.validate_refs("crm", data)
        self.assertTrue(any("acme" in e for e in errors))

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

    def test_orphan_contract_in_lines(self):
        data = {
            "customers": [],
            "contacts": [],
            "contracts": [],
            "contract_lines": [{"contract_id": "ct-nope", "seq": 1, "description": "X",
                                "quantity": 1, "unit_price": 100, "frequency": "monthly"}],
            "contract_clauses": [],
        }
        errors = datalib.validate_refs("crm", data)
        self.assertTrue(any("ct-nope" in e for e in errors))

    def test_clean_board_data(self):
        data = {
            "board_meetings": [{"id": "bm-2026-01-01", "meeting_date": "2026-01-01", "title": "Q1"}],
            "board_attendees": [{"meeting_id": "bm-2026-01-01", "person_name": "Alice", "role": "chair"}],
            "board_minutes": [{"meeting_id": "bm-2026-01-01", "seq": 1, "item_text": "Called to order"}],
            "board_resolutions": [{"id": "bm-2026-01-01-r1", "meeting_id": "bm-2026-01-01",
                                   "resolution_text": "Approve", "status": "passed"}],
        }
        errors = datalib.validate_refs("board", data)
        self.assertEqual(errors, [])

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
        errors = datalib.validate_refs("unknown", {})
        self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# print_table()
# ---------------------------------------------------------------------------

class TestPrintTable(unittest.TestCase):
    def test_empty_rows(self, ):
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
