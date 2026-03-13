"""Tests for accounts module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

accounts = import_script("accounts", "accounts")

ACCT_DATA = {
    "accounts": [
        {"path": "assets:bank:tide", "account_type": "assets"},
        {"path": "expenses:infra:hosting", "account_type": "expenses"},
        {"path": "revenue:sales", "account_type": "revenue"},
    ],
    "transactions": [
        {"id": 1, "txn_date": "2026-03-01", "payee": "AWS", "description": "Hosting"},
    ],
    "postings": [
        {"txn_id": 1, "account_path": "expenses:infra:hosting", "amount": 45.0, "currency": "GBP"},
        {"txn_id": 1, "account_path": "assets:bank:tide", "amount": -45.0, "currency": "GBP"},
    ],
}


class TestCmdCheck(unittest.TestCase):
    @patch("datalib.load")
    def test_clean_check_passes(self, mock_load):
        mock_load.return_value = ACCT_DATA
        accounts.cmd_check()

    @patch("datalib.load")
    def test_orphan_accounts_fail(self, mock_load):
        data = dict(ACCT_DATA)
        data["postings"] = [
            {"txn_id": 1, "account_path": "expenses:unknown", "amount": 45.0, "currency": "GBP"},
            {"txn_id": 1, "account_path": "assets:bank:tide", "amount": -45.0, "currency": "GBP"},
        ]
        mock_load.return_value = data
        with self.assertRaises(SystemExit):
            accounts.cmd_check()

    @patch("datalib.load")
    def test_unbalanced_transactions_fail(self, mock_load):
        data = dict(ACCT_DATA)
        data["postings"] = [
            {"txn_id": 1, "account_path": "expenses:infra:hosting", "amount": 45.0, "currency": "GBP"},
            {"txn_id": 1, "account_path": "assets:bank:tide", "amount": -40.0, "currency": "GBP"},
        ]
        mock_load.return_value = data
        with self.assertRaises(SystemExit):
            accounts.cmd_check()


class TestCmdBal(unittest.TestCase):
    @patch("datalib.account_balances")
    def test_bal_no_filter(self, mock_bals):
        mock_bals.return_value = [
            {"account_path": "expenses:infra:hosting", "account_type": "expenses", "balance": 45.0, "currency": "GBP"},
        ]
        accounts.cmd_bal("")

    @patch("datalib.account_balances")
    def test_bal_with_filter(self, mock_bals):
        mock_bals.return_value = [
            {"account_path": "expenses:infra:hosting", "account_type": "expenses", "balance": 45.0, "currency": "GBP"},
            {"account_path": "assets:bank:tide", "account_type": "assets", "balance": -45.0, "currency": "GBP"},
        ]
        accounts.cmd_bal("expenses")


class TestCmdReg(unittest.TestCase):
    def test_reg_no_account_exits(self):
        with self.assertRaises(SystemExit):
            accounts.cmd_reg("")


class TestRouting(unittest.TestCase):
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
