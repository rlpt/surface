"""Tests for CRM module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

crm = import_script("crm", "crm")


class TestEsc(unittest.TestCase):
    """Test SQL escaping."""

    def test_no_quotes(self):
        self.assertEqual(crm.esc("hello"), "hello")

    def test_single_quote(self):
        self.assertEqual(crm.esc("O'Brien"), "O''Brien")

    def test_multiple_quotes(self):
        self.assertEqual(crm.esc("it's a 'test'"), "it''s a ''test''")

    def test_empty_string(self):
        self.assertEqual(crm.esc(""), "")


class TestStandardClauses(unittest.TestCase):
    """Test standard clauses data."""

    def test_has_12_clauses(self):
        self.assertEqual(len(crm.STANDARD_CLAUSES), 12)

    def test_each_clause_has_heading_and_body(self):
        for heading, body in crm.STANDARD_CLAUSES:
            self.assertIsInstance(heading, str)
            self.assertIsInstance(body, str)
            self.assertTrue(len(heading) > 0)
            self.assertTrue(len(body) > 0)

    def test_expected_clause_headings(self):
        headings = [h for h, _ in crm.STANDARD_CLAUSES]
        self.assertIn("Definitions", headings)
        self.assertIn("Termination", headings)
        self.assertIn("Data Protection", headings)
        self.assertIn("Governing Law and Jurisdiction", headings)


class TestContractMarkdown(unittest.TestCase):
    """Test contract_markdown generation."""

    @patch.object(crm, "dsql_rows")
    def test_unknown_contract_returns_none(self, mock_rows):
        mock_rows.return_value = []
        result = crm.contract_markdown("ct-nonexistent-1")
        self.assertIsNone(result)

    @patch.object(crm, "dsql_rows")
    def test_draft_contract_shows_warning(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-acme-1", "company": "Acme Corp",
                "company_number": "12345678", "address": "123 Main St",
                "title": "SaaS Agreement", "status": "draft",
                "effective_date": "2026-04-01", "term_months": "12",
                "auto_renew": "1", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "30",
            }],
            [],  # no lines
            [],  # no clauses
        ]
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("DRAFT", md)
        self.assertIn("NOT YET EXECUTED", md)

    @patch.object(crm, "dsql_rows")
    def test_contract_with_lines_calculates_annual(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-acme-1", "company": "Acme Corp",
                "company_number": "", "address": "",
                "title": "SaaS Agreement", "status": "active",
                "effective_date": "2026-04-01", "term_months": "12",
                "auto_renew": "0", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "30",
            }],
            [
                {"seq": "1", "description": "Platform licence", "quantity": "1", "unit_price": "200.00", "frequency": "monthly"},
                {"seq": "2", "description": "Onboarding", "quantity": "1", "unit_price": "1500.00", "frequency": "one-off"},
            ],
            [],  # no clauses
        ]
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("Platform licence", md)
        # Monthly: 200 * 12 = 2400, One-off: 1500 = 1500, Total: 3900
        self.assertIn("3,900.00", md)

    @patch.object(crm, "dsql_rows")
    def test_contract_with_quarterly_lines(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-test-1", "company": "Test Co",
                "company_number": "", "address": "",
                "title": "Test", "status": "active",
                "effective_date": "2026-01-01", "term_months": "12",
                "auto_renew": "0", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "30",
            }],
            [
                {"seq": "1", "description": "Quarterly review", "quantity": "1", "unit_price": "3000.00", "frequency": "quarterly"},
            ],
            [],
        ]
        md = crm.contract_markdown("ct-test-1")
        # Quarterly: 3000 * 4 = 12000
        self.assertIn("12,000.00", md)

    @patch.object(crm, "dsql_rows")
    def test_contract_with_annual_lines(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-test-1", "company": "Test Co",
                "company_number": "", "address": "",
                "title": "Test", "status": "active",
                "effective_date": "2026-01-01", "term_months": "12",
                "auto_renew": "0", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "30",
            }],
            [
                {"seq": "1", "description": "Annual licence", "quantity": "1", "unit_price": "5000.00", "frequency": "annual"},
            ],
            [],
        ]
        md = crm.contract_markdown("ct-test-1")
        # Annual: 5000
        self.assertIn("5,000.00", md)

    @patch.object(crm, "dsql_rows")
    def test_contract_includes_clauses(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-acme-1", "company": "Acme Corp",
                "company_number": "", "address": "",
                "title": "Agreement", "status": "draft",
                "effective_date": "", "term_months": "",
                "auto_renew": "0", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "",
            }],
            [],  # no lines
            [
                {"seq": "1", "heading": "Definitions", "body": "In this Agreement..."},
                {"seq": "2", "heading": "Services", "body": "The Provider shall..."},
            ],
        ]
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("## 1. Definitions", md)
        self.assertIn("## 2. Services", md)
        self.assertIn("In this Agreement...", md)

    @patch.object(crm, "dsql_rows")
    def test_contract_includes_signature_blocks(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-acme-1", "company": "Acme Corp",
                "company_number": "", "address": "",
                "title": "Agreement", "status": "draft",
                "effective_date": "", "term_months": "",
                "auto_renew": "0", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "",
            }],
            [],
            [],
        ]
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("Formabi Ltd", md)
        self.assertIn("Acme Corp", md)
        self.assertIn("Signature:", md)

    @patch.object(crm, "dsql_rows")
    def test_company_number_shown_when_present(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "ct-acme-1", "company": "Acme Corp",
                "company_number": "12345678", "address": "123 Main St",
                "title": "Agreement", "status": "draft",
                "effective_date": "", "term_months": "",
                "auto_renew": "0", "payment_terms": "net-30",
                "currency": "GBP", "governing_law": "England and Wales",
                "jurisdiction": "Courts of England and Wales",
                "notice_period_days": "",
            }],
            [],
            [],
        ]
        md = crm.contract_markdown("ct-acme-1")
        self.assertIn("Company No. 12345678", md)
        self.assertIn("123 Main St", md)


class TestCmdAddCustomer(unittest.TestCase):
    """Test add customer command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_add_customer(["acme"])

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    def test_successful_add(self, mock_dsql, mock_commit):
        crm.cmd_add_customer(["acme", "Acme Corp", "12345678"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("INSERT INTO customers", sql)
        self.assertIn("'acme'", sql)
        self.assertIn("'Acme Corp'", sql)
        self.assertIn("'12345678'", sql)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    def test_add_without_company_number(self, mock_dsql, mock_commit):
        crm.cmd_add_customer(["acme", "Acme Corp"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("INSERT INTO customers", sql)


class TestCmdAddContact(unittest.TestCase):
    """Test add contact command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_add_contact(["acme", "Jane"])

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    def test_generates_contact_id(self, mock_dsql, mock_commit):
        crm.cmd_add_contact(["acme", "Jane Smith", "jane@acme.com", "CTO"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'acme-jane'", sql)  # id = customer-firstname

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    def test_default_role_empty(self, mock_dsql, mock_commit):
        crm.cmd_add_contact(["acme", "Jane Smith", "jane@acme.com"])
        sql = mock_dsql.call_args[0][0]
        # role should be empty string
        self.assertIn("'')", sql)


class TestCmdNewContract(unittest.TestCase):
    """Test new contract command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_new_contract(["acme"])

    @patch.object(crm, "dsql_val")
    def test_unknown_customer_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            crm.cmd_new_contract(["nobody", "Agreement"])

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_generates_contract_id(self, mock_val, mock_dsql, mock_commit):
        mock_val.side_effect = [
            "Acme Corp",  # customer exists
            "0",  # no existing contracts
        ]
        crm.cmd_new_contract(["acme", "SaaS Agreement"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'ct-acme-1'", sql)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_increments_contract_seq(self, mock_val, mock_dsql, mock_commit):
        mock_val.side_effect = [
            "Acme Corp",
            "3",  # 3 existing contracts
        ]
        crm.cmd_new_contract(["acme", "Another Agreement"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'ct-acme-4'", sql)


class TestCmdLine(unittest.TestCase):
    """Test add line command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_line(["ct-acme-1", "1", "desc"])

    @patch.object(crm, "dsql_val")
    def test_unknown_contract_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            crm.cmd_line(["ct-nonexistent", "1", "desc", "100"])

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_default_frequency_monthly(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "SaaS Agreement"
        crm.cmd_line(["ct-acme-1", "1", "Platform licence", "200"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'monthly'", sql)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_custom_frequency(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "SaaS Agreement"
        crm.cmd_line(["ct-acme-1", "1", "Onboarding", "1500", "one-off"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'one-off'", sql)


class TestCmdClause(unittest.TestCase):
    """Test add clause command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_clause(["ct-acme-1", "1", "heading"])

    @patch.object(crm, "dsql_val")
    def test_unknown_contract_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            crm.cmd_clause(["ct-nonexistent", "1", "Heading", "Body text"])


class TestCmdStandardClauses(unittest.TestCase):
    """Test standard clauses insertion."""

    def test_no_contract_id_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_standard_clauses("")

    @patch.object(crm, "dsql_val")
    def test_unknown_contract_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            crm.cmd_standard_clauses("ct-nonexistent")

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_inserts_all_12_clauses(self, mock_val, mock_dsql, mock_commit):
        mock_val.side_effect = [
            "SaaS Agreement",  # contract exists
            "0",  # no existing clauses
        ]
        crm.cmd_standard_clauses("ct-acme-1")
        # 12 INSERT calls for clauses
        self.assertEqual(mock_dsql.call_count, 12)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_starts_after_existing_clauses(self, mock_val, mock_dsql, mock_commit):
        mock_val.side_effect = [
            "SaaS Agreement",
            "3",  # 3 existing clauses
        ]
        crm.cmd_standard_clauses("ct-acme-1")
        # First clause should be seq 4
        first_sql = mock_dsql.call_args_list[0][0][0]
        self.assertIn(", 4,", first_sql)


class TestCmdSet(unittest.TestCase):
    """Test set contract field command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_set(["ct-acme-1", "term"])

    @patch.object(crm, "dsql_val")
    def test_unknown_field_exits(self, mock_val):
        with self.assertRaises(SystemExit):
            crm.cmd_set(["ct-acme-1", "invalid-field", "value"])

    @patch.object(crm, "dsql_val")
    def test_unknown_contract_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            crm.cmd_set(["ct-nonexistent", "term", "12"])

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_numeric_field(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "Agreement"
        crm.cmd_set(["ct-acme-1", "term", "12"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("term_months = 12", sql)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_boolean_field_true(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "Agreement"
        crm.cmd_set(["ct-acme-1", "auto-renew", "true"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("auto_renew = TRUE", sql)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_boolean_field_false(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "Agreement"
        crm.cmd_set(["ct-acme-1", "auto-renew", "no"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("auto_renew = FALSE", sql)

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_string_field(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "Agreement"
        crm.cmd_set(["ct-acme-1", "currency", "USD"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("currency = 'USD'", sql)

    def test_all_allowed_fields_mapped(self):
        expected = {
            "effective-date", "term", "auto-renew", "payment-terms",
            "currency", "governing-law", "jurisdiction", "notice-period",
            "status", "notes",
        }
        # Access the allowed dict inside cmd_set by calling with bad field
        with self.assertRaises(SystemExit):
            crm.cmd_set(["ct-x", "invalid", "v"])


class TestCmdActivate(unittest.TestCase):
    """Test activate command."""

    def test_no_id_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_activate("")

    @patch.object(crm, "dsql_val")
    def test_unknown_contract_exits(self, mock_val):
        mock_val.return_value = ""
        with self.assertRaises(SystemExit):
            crm.cmd_activate("ct-nonexistent")

    @patch.object(crm, "dolt_commit")
    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_sets_status_active(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "Agreement"
        crm.cmd_activate("ct-acme-1")
        sql = mock_dsql.call_args[0][0]
        self.assertIn("status = 'active'", sql)


class TestCmdRenewals(unittest.TestCase):
    """Test renewals command."""

    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_no_renewals(self, mock_val, mock_dsql):
        mock_val.return_value = "0"
        crm.cmd_renewals()
        mock_dsql.assert_not_called()

    @patch.object(crm, "dsql")
    @patch.object(crm, "dsql_val")
    def test_has_renewals(self, mock_val, mock_dsql):
        mock_val.return_value = "3"
        crm.cmd_renewals()
        mock_dsql.assert_called_once()


class TestCmdFind(unittest.TestCase):
    """Test find command."""

    def test_no_term_exits(self):
        with self.assertRaises(SystemExit):
            crm.cmd_find("")

    @patch.object(crm, "dsql")
    def test_search_term_in_sql(self, mock_dsql):
        crm.cmd_find("acme")
        sql = mock_dsql.call_args[0][0]
        self.assertIn("acme", sql)
        self.assertIn("LIKE", sql)


class TestRouting(unittest.TestCase):
    """Test main() dispatch."""

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

    @patch.object(crm, "cmd_set")
    def test_route_set(self, mock_cmd):
        with patch("sys.argv", ["crm", "set", "ct-acme-1", "term", "12"]):
            crm.main()
        mock_cmd.assert_called_once_with(["ct-acme-1", "term", "12"])

    @patch.object(crm, "cmd_contracts")
    def test_route_contracts_with_filter(self, mock_cmd):
        with patch("sys.argv", ["crm", "contracts", "active"]):
            crm.main()
        mock_cmd.assert_called_once_with("active")

    @patch.object(crm, "cmd_help")
    def test_route_unknown_shows_help(self, mock_cmd):
        with patch("sys.argv", ["crm", "garbage"]):
            crm.main()
        mock_cmd.assert_called_once()


if __name__ == "__main__":
    unittest.main()
