"""Tests for CRM module logic."""

import copy
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

crm = import_script("crm", "crm")

CRM_DATA = {
    "customers": [
        {"id": "acme", "company": "Acme Corp", "company_number": "12345678",
         "address": "123 Main St", "notes": "", "created_at": "2026-03-01"},
    ],
    "contacts": [
        {"id": "acme-jane", "customer_id": "acme", "name": "Jane Smith",
         "email": "jane@acme.com", "role": "CTO", "notes": "", "created_at": "2026-03-01"},
    ],
    "contracts": [
        {"id": "ct-acme-1", "customer_id": "acme", "title": "SaaS Agreement",
         "status": "draft", "effective_date": "2026-04-01", "term_months": 12,
         "auto_renew": False, "payment_terms": "net-30", "currency": "GBP",
         "governing_law": "England and Wales", "jurisdiction": "Courts of England and Wales",
         "notice_period_days": 30, "notes": "", "created_at": "2026-03-01"},
    ],
    "contract_lines": [
        {"contract_id": "ct-acme-1", "seq": 1, "description": "Platform licence",
         "quantity": 1, "unit_price": 200.0, "frequency": "monthly"},
    ],
    "contract_clauses": [],
}


class TestEsc(unittest.TestCase):
    def test_no_quotes(self):
        self.assertEqual(crm.esc("hello"), "hello")

    def test_single_quote(self):
        self.assertEqual(crm.esc("O'Brien"), "O''Brien")

    def test_empty_string(self):
        self.assertEqual(crm.esc(""), "")


class TestStandardClauses(unittest.TestCase):
    def test_has_12_clauses(self):
        self.assertEqual(len(crm.STANDARD_CLAUSES), 12)

    def test_each_clause_has_heading_and_body(self):
        for heading, body in crm.STANDARD_CLAUSES:
            self.assertIsInstance(heading, str)
            self.assertIsInstance(body, str)
            self.assertTrue(len(heading) > 0)

    def test_expected_clause_headings(self):
        headings = [h for h, _ in crm.STANDARD_CLAUSES]
        self.assertIn("Definitions", headings)
        self.assertIn("Termination", headings)
        self.assertIn("Data Protection", headings)


class TestContractMarkdown(unittest.TestCase):
    @patch("datalib.load")
    def test_unknown_contract_returns_none(self, mock_load):
        mock_load.return_value = {"customers": [], "contracts": [], "contract_lines": [], "contract_clauses": []}
        result = crm.contract_markdown("ct-nonexistent-1")
        self.assertIsNone(result)

    @patch("datalib.load")
    def test_draft_contract_shows_warning(self, mock_load):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("DRAFT", md)
        self.assertIn("NOT YET EXECUTED", md)

    @patch("datalib.load")
    def test_contract_with_lines_calculates_annual(self, mock_load):
        data = dict(CRM_DATA)
        data["contracts"] = [dict(CRM_DATA["contracts"][0], status="active")]
        data["contract_lines"] = [
            {"contract_id": "ct-acme-1", "seq": 1, "description": "Platform licence",
             "quantity": 1, "unit_price": 200.0, "frequency": "monthly"},
            {"contract_id": "ct-acme-1", "seq": 2, "description": "Onboarding",
             "quantity": 1, "unit_price": 1500.0, "frequency": "one-off"},
        ]
        mock_load.return_value = data
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("Platform licence", md)
        # Monthly: 200 * 12 = 2400, One-off: 1500, Total: 3900
        self.assertIn("3,900.00", md)

    @patch("datalib.load")
    def test_contract_includes_signature_blocks(self, mock_load):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("Formabi Ltd", md)
        self.assertIn("Acme Corp", md)
        self.assertIn("Signature:", md)

    @patch("datalib.load")
    def test_company_number_shown(self, mock_load):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("Company No. 12345678", md)


class TestCmdAddCustomer(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_add_customer(["acme"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_successful_add(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = {"customers": [], "contacts": [], "contracts": [], "contract_lines": [], "contract_clauses": []}
        crm.cmd_add_customer(["acme", "Acme Corp", "12345678"])
        saved_data = mock_save.call_args[0][1]
        self.assertTrue(any(c["id"] == "acme" for c in saved_data["customers"]))


class TestCmdAddContact(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_add_contact(["acme", "Jane"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_generates_contact_id(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        crm.cmd_add_contact(["acme", "Bob Smith", "bob@acme.com", "CTO"])
        saved_data = mock_save.call_args[0][1]
        last_contact = saved_data["contacts"][-1]
        self.assertIn("bob", last_contact["id"])


class TestCmdNewContract(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_new_contract(["acme"])

    @patch("datalib.load")
    def test_unknown_customer_exits(self, mock_load):
        mock_load.return_value = {"customers": [], "contracts": [], "contacts": [], "contract_lines": [], "contract_clauses": []}
        with self.assertRaises(SystemExit):
            crm.cmd_new_contract(["nobody", "Agreement"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_generates_contract_id(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        crm.cmd_new_contract(["acme", "New Agreement"])
        saved_data = mock_save.call_args[0][1]
        last_contract = saved_data["contracts"][-1]
        self.assertEqual(last_contract["id"], "ct-acme-2")


class TestCmdSet(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_set(["ct-acme-1", "term"])

    @patch("datalib.load")
    def test_unknown_field_exits(self, mock_load):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        with self.assertRaises(SystemExit):
            crm.cmd_set(["ct-acme-1", "invalid-field", "value"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_numeric_field(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        crm.cmd_set(["ct-acme-1", "term", "24"])
        saved_data = mock_save.call_args[0][1]
        ct = next(c for c in saved_data["contracts"] if c["id"] == "ct-acme-1")
        self.assertEqual(ct["term_months"], 24)

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_boolean_field_true(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        crm.cmd_set(["ct-acme-1", "auto-renew", "true"])
        saved_data = mock_save.call_args[0][1]
        ct = next(c for c in saved_data["contracts"] if c["id"] == "ct-acme-1")
        self.assertTrue(ct["auto_renew"])


class TestCmdActivate(unittest.TestCase):
    def test_no_id_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_activate("")

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_sets_status_active(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = copy.deepcopy(CRM_DATA)
        crm.cmd_activate("ct-acme-1")
        saved_data = mock_save.call_args[0][1]
        ct = next(c for c in saved_data["contracts"] if c["id"] == "ct-acme-1")
        self.assertEqual(ct["status"], "active")


class TestCmdFind(unittest.TestCase):
    def test_no_term_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_find("")


class TestRouting(unittest.TestCase):
    @patch.object(crm, "cmd_customers")
    def test_route_customers(self, mock_cmd):
        with patch("sys.argv", ["crm", "customers"]):
            crm.main()
        mock_cmd.assert_called_once()

    @patch.object(crm, "cmd_add_customer")
    def test_route_add(self, mock_cmd):
        with patch("sys.argv", ["crm", "add", "acme", "Acme Corp"]):
            crm.main()
        mock_cmd.assert_called_once_with(["acme", "Acme Corp"])

    @patch.object(crm, "cmd_new_contract")
    def test_route_new(self, mock_cmd):
        with patch("sys.argv", ["crm", "new", "acme", "Agreement"]):
            crm.main()
        mock_cmd.assert_called_once_with(["acme", "Agreement"])

    @patch.object(crm, "cmd_activate")
    def test_route_activate(self, mock_cmd):
        with patch("sys.argv", ["crm", "activate", "ct-acme-1"]):
            crm.main()
        mock_cmd.assert_called_once_with("ct-acme-1")

    @patch.object(crm, "cmd_help")
    def test_route_unknown_shows_help(self, mock_cmd):
        with patch("sys.argv", ["crm", "garbage"]):
            crm.main()
        mock_cmd.assert_called_once()


if __name__ == "__main__":
    unittest.main()
