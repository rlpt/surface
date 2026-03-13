"""Tests for board module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

board = import_script("board", "board")


class TestEsc(unittest.TestCase):
    """Test HTML escaping."""

    def test_no_special_chars(self):
        self.assertEqual(board.esc("hello"), "hello")

    def test_ampersand(self):
        self.assertEqual(board.esc("A & B"), "A &amp; B")

    def test_angle_brackets(self):
        self.assertEqual(board.esc("<script>"), "&lt;script&gt;")

    def test_all_special(self):
        self.assertEqual(board.esc("a < b & c > d"), "a &lt; b &amp; c &gt; d")

    def test_non_string(self):
        self.assertEqual(board.esc(42), "42")

    def test_none(self):
        self.assertEqual(board.esc(None), "None")


class TestHtmlTable(unittest.TestCase):
    """Test HTML table generation."""

    def test_empty_rows(self):
        result = board.html_table([])
        self.assertIn("No data.", result)

    def test_single_row(self):
        rows = [{"name": "Alice", "role": "chair"}]
        result = board.html_table(rows)
        self.assertIn("<table>", result)
        self.assertIn("<th>name</th>", result)
        self.assertIn("<th>role</th>", result)
        self.assertIn("<td>Alice</td>", result)
        self.assertIn("<td>chair</td>", result)

    def test_multiple_rows(self):
        rows = [
            {"name": "Alice", "role": "chair"},
            {"name": "Bob", "role": "director"},
        ]
        result = board.html_table(rows)
        self.assertIn("Alice", result)
        self.assertIn("Bob", result)
        self.assertEqual(result.count("<tr>"), 3)  # 1 header + 2 data

    def test_escapes_values(self):
        rows = [{"name": "O'Brien & Co <Ltd>"}]
        result = board.html_table(rows)
        # board.esc handles &, <, > but not single quotes
        self.assertIn("O'Brien &amp; Co &lt;Ltd&gt;", result)

    def test_highlight_column(self):
        rows = [{"name": "Alice", "status": "passed"}]
        result = board.html_table(rows, highlight_col="status")
        self.assertIn('class="highlight"', result)


class TestHtmlPage(unittest.TestCase):
    """Test full page HTML generation."""

    def test_includes_title(self):
        result = board.html_page("Test Title", "<p>content</p>")
        self.assertIn("Test Title", result)
        self.assertIn("<p>content</p>", result)

    def test_includes_nav(self):
        result = board.html_page("Title", "body")
        self.assertIn("Meetings", result)
        self.assertIn("Resolutions", result)

    def test_active_nav(self):
        result = board.html_page("Title", "body", "index")
        self.assertIn('class="active"', result)

    def test_escapes_title(self):
        result = board.html_page("A & B <C>", "body")
        self.assertIn("A &amp; B &lt;C&gt;", result)

    def test_includes_brand_colors(self):
        result = board.html_page("Title", "body")
        self.assertIn(board.COLORS["primary"], result)
        self.assertIn(board.COLORS["accent"], result)


class TestMeetingMarkdown(unittest.TestCase):
    """Test meeting markdown generation."""

    @patch.object(board, "dsql_rows")
    def test_unknown_meeting_returns_none(self, mock_rows):
        mock_rows.return_value = []
        result = board.meeting_markdown("bm-nonexistent")
        self.assertIsNone(result)

    @patch.object(board, "dsql_rows")
    def test_basic_meeting(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "bm-2026-03-15", "meeting_date": "2026-03-15",
                "title": "Q1 Board Meeting", "location": "London",
                "status": "completed", "called_by": "Alice",
            }],
            [{"person_name": "Alice", "role": "chair"}],
            [{"seq": "1", "item_text": "Meeting called to order"}],
            [{
                "id": "bm-2026-03-15-r1", "resolution_text": "Approve Q1 financials",
                "status": "passed", "proposed_by": "Alice", "voted_date": "2026-03-15",
            }],
        ]
        md = board.meeting_markdown("bm-2026-03-15")
        self.assertIn("Q1 Board Meeting", md)
        self.assertIn("2026-03-15", md)
        self.assertIn("London", md)
        self.assertIn("Alice", md)
        self.assertIn("Meeting called to order", md)
        self.assertIn("Approve Q1 financials", md)
        self.assertIn("PASSED", md)

    @patch.object(board, "dsql_rows")
    def test_meeting_without_optional_fields(self, mock_rows):
        mock_rows.side_effect = [
            [{
                "id": "bm-2026-03-15", "meeting_date": "2026-03-15",
                "title": "Quick Meeting", "location": "",
                "status": "scheduled", "called_by": "",
            }],
            [],  # no attendees
            [],  # no minutes
            [],  # no resolutions
        ]
        md = board.meeting_markdown("bm-2026-03-15")
        self.assertIn("Quick Meeting", md)
        self.assertNotIn("Location", md)
        self.assertNotIn("Called by", md)


class TestCmdNew(unittest.TestCase):
    """Test new meeting command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_new(["2026-03-15"])

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    def test_generates_id_from_date(self, mock_dsql, mock_commit):
        board.cmd_new(["2026-03-15", "Q1", "Board", "Meeting"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'bm-2026-03-15'", sql)
        self.assertIn("'Q1 Board Meeting'", sql)
        self.assertIn("'scheduled'", sql)


class TestCmdAttend(unittest.TestCase):
    """Test attend command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_attend(["bm-2026-03-15"])

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    def test_default_role_director(self, mock_dsql, mock_commit):
        board.cmd_attend(["bm-2026-03-15", "Alice"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'director'", sql)

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    def test_custom_role(self, mock_dsql, mock_commit):
        board.cmd_attend(["bm-2026-03-15", "Alice", "chair"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'chair'", sql)


class TestCmdMinute(unittest.TestCase):
    """Test minute command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_minute(["bm-2026-03-15", "1"])

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    def test_escapes_quotes_in_text(self, mock_dsql, mock_commit):
        board.cmd_minute(["bm-2026-03-15", "1", "Alice's", "proposal"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("Alice''s proposal", sql)


class TestCmdResolve(unittest.TestCase):
    """Test resolve command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_resolve(["bm-2026-03-15"])

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    @patch.object(board, "dsql_val")
    def test_generates_resolution_id(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "2"  # 2 existing resolutions
        board.cmd_resolve(["bm-2026-03-15", "Approve budget"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'bm-2026-03-15-r3'", sql)
        self.assertIn("'pending'", sql)

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    @patch.object(board, "dsql_val")
    def test_first_resolution(self, mock_val, mock_dsql, mock_commit):
        mock_val.return_value = "0"
        board.cmd_resolve(["bm-2026-03-15", "First resolution"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("'bm-2026-03-15-r1'", sql)


class TestCmdVote(unittest.TestCase):
    """Test vote command."""

    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_vote(["bm-2026-03-15-r1"])

    def test_invalid_outcome_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_vote(["bm-2026-03-15-r1", "maybe"])

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    def test_vote_passed(self, mock_dsql, mock_commit):
        board.cmd_vote(["bm-2026-03-15-r1", "passed"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("status = 'passed'", sql)
        self.assertIn("voted_date = CURRENT_DATE", sql)

    @patch.object(board, "dolt_commit")
    @patch.object(board, "dsql")
    def test_vote_failed(self, mock_dsql, mock_commit):
        board.cmd_vote(["bm-2026-03-15-r1", "failed"])
        sql = mock_dsql.call_args[0][0]
        self.assertIn("status = 'failed'", sql)


class TestCmdMeetings(unittest.TestCase):
    """Test meetings list command."""

    @patch.object(board, "dsql_csv")
    def test_no_meetings(self, mock_csv):
        mock_csv.return_value = []
        board.cmd_meetings()  # should print "No meetings found."

    @patch.object(board, "dsql_csv")
    def test_parses_csv_rows(self, mock_csv):
        mock_csv.return_value = [
            "bm-2026-03-15,2026-03-15,Q1 Meeting,completed,3,2"
        ]
        board.cmd_meetings()  # should not raise


class TestCmdResolutions(unittest.TestCase):
    """Test resolutions list command."""

    @patch.object(board, "dsql_rows")
    def test_no_resolutions(self, mock_rows):
        mock_rows.return_value = []
        board.cmd_resolutions("all")

    @patch.object(board, "dsql_rows")
    def test_pending_filter(self, mock_rows):
        mock_rows.return_value = []
        board.cmd_resolutions("pending")
        sql = mock_rows.call_args[0][0]
        self.assertIn("status = 'pending'", sql)

    @patch.object(board, "dsql_rows")
    def test_passed_filter(self, mock_rows):
        mock_rows.return_value = []
        board.cmd_resolutions("passed")
        sql = mock_rows.call_args[0][0]
        self.assertIn("status = 'passed'", sql)

    @patch.object(board, "dsql_rows")
    def test_truncates_long_text(self, mock_rows):
        mock_rows.return_value = [{
            "id": "r1", "meeting_date": "2026-03-15",
            "resolution_text": "A" * 60,
            "status": "passed", "proposed_by": "", "voted_date": "",
        }]
        board.cmd_resolutions("all")


class TestRouting(unittest.TestCase):
    """Test main() dispatch."""

    @patch.object(board, "cmd_meetings")
    def test_route_meetings(self, mock_cmd):
        with patch("sys.argv", ["board", "meetings"]):
            board.main()
        mock_cmd.assert_called_once()

    @patch.object(board, "cmd_new")
    def test_route_new(self, mock_cmd):
        with patch("sys.argv", ["board", "new", "2026-03-15", "Meeting"]):
            board.main()
        mock_cmd.assert_called_once_with(["2026-03-15", "Meeting"])

    @patch.object(board, "cmd_vote")
    def test_route_vote(self, mock_cmd):
        with patch("sys.argv", ["board", "vote", "r1", "passed"]):
            board.main()
        mock_cmd.assert_called_once_with(["r1", "passed"])

    @patch.object(board, "cmd_help")
    def test_route_unknown_shows_help(self, mock_cmd):
        with patch("sys.argv", ["board", "garbage"]):
            board.main()
        mock_cmd.assert_called_once()

    def test_meeting_no_id_exits(self):
        with patch("sys.argv", ["board", "meeting"]):
            with self.assertRaises(SystemExit):
                board.main()


class TestBuildPages(unittest.TestCase):
    """Test HTML page builders."""

    @patch.object(board, "dsql_rows")
    @patch.object(board, "dsql_val")
    def test_build_meetings_page(self, mock_val, mock_rows):
        mock_val.side_effect = ["1", "1", "0"]  # total, passed, pending
        mock_rows.side_effect = [
            # meetings query
            [{
                "id": "bm-2026-03-15", "meeting_date": "2026-03-15",
                "title": "Q1 Meeting", "status": "completed",
                "location": "", "called_by": "",
            }],
            # attendees for bm-2026-03-15
            [{"person_name": "Alice", "role": "chair"}],
            # resolutions for bm-2026-03-15
            [],
        ]
        html = board.build_meetings_page()
        self.assertIn("Board Meetings", html)
        self.assertIn("Q1 Meeting", html)
        self.assertIn("<!DOCTYPE html>", html)

    @patch.object(board, "dsql_rows")
    def test_build_resolutions_page_empty(self, mock_rows):
        mock_rows.return_value = []
        html = board.build_resolutions_page()
        self.assertIn("No resolutions recorded", html)

    @patch.object(board, "dsql_rows")
    def test_build_meeting_detail_not_found(self, mock_rows):
        mock_rows.return_value = []
        result = board.build_meeting_detail("bm-nonexistent")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
