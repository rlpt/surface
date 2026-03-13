"""Tests for board module logic."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

board = import_script("board", "board")

BOARD_DATA = {
    "board_meetings": [
        {
            "id": "bm-2026-03-15", "meeting_date": "2026-03-15",
            "title": "Q1 Board Meeting", "location": "London",
            "status": "completed", "called_by": "Alice",
        },
    ],
    "board_attendees": [
        {"meeting_id": "bm-2026-03-15", "person_name": "Alice", "role": "chair"},
    ],
    "board_minutes": [
        {"meeting_id": "bm-2026-03-15", "seq": 1, "item_text": "Meeting called to order"},
    ],
    "board_resolutions": [
        {
            "id": "bm-2026-03-15-r1", "meeting_id": "bm-2026-03-15",
            "resolution_text": "Approve Q1 financials",
            "status": "passed", "proposed_by": "Alice", "voted_date": "2026-03-15",
        },
    ],
}


class TestEsc(unittest.TestCase):
    def test_no_special_chars(self):
        self.assertEqual(board.esc("hello"), "hello")

    def test_ampersand(self):
        self.assertEqual(board.esc("A & B"), "A &amp; B")

    def test_angle_brackets(self):
        self.assertEqual(board.esc("<script>"), "&lt;script&gt;")

    def test_non_string(self):
        self.assertEqual(board.esc(42), "42")


class TestHtmlTable(unittest.TestCase):
    def test_empty_rows(self):
        result = board.html_table([])
        self.assertIn("No data.", result)

    def test_single_row(self):
        rows = [{"name": "Alice", "role": "chair"}]
        result = board.html_table(rows)
        self.assertIn("<table>", result)
        self.assertIn("<th>name</th>", result)
        self.assertIn("<td>Alice</td>", result)

    def test_highlight_column(self):
        rows = [{"name": "Alice", "status": "passed"}]
        result = board.html_table(rows, highlight_col="status")
        self.assertIn('class="highlight"', result)


class TestHtmlPage(unittest.TestCase):
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

    def test_includes_brand_colors(self):
        result = board.html_page("Title", "body")
        self.assertIn(board.COLORS["primary"], result)


class TestMeetingMarkdown(unittest.TestCase):
    @patch("datalib.load")
    def test_unknown_meeting_returns_none(self, mock_load):
        mock_load.return_value = {"board_meetings": [], "board_attendees": [], "board_minutes": [], "board_resolutions": []}
        result = board.meeting_markdown("bm-nonexistent")
        self.assertIsNone(result)

    @patch("datalib.load")
    def test_basic_meeting(self, mock_load):
        mock_load.return_value = BOARD_DATA
        md = board.meeting_markdown("bm-2026-03-15")
        self.assertIn("Q1 Board Meeting", md)
        self.assertIn("2026-03-15", md)
        self.assertIn("Alice", md)
        self.assertIn("Meeting called to order", md)
        self.assertIn("PASSED", md)


class TestCmdNew(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_new(["2026-03-15"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_generates_id_from_date(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = {"board_meetings": [], "board_attendees": [], "board_minutes": [], "board_resolutions": []}
        board.cmd_new(["2026-03-15", "Q1", "Board", "Meeting"])
        saved_data = mock_save.call_args[0][1]
        meeting = saved_data["board_meetings"][-1]
        self.assertEqual(meeting["id"], "bm-2026-03-15")
        self.assertEqual(meeting["title"], "Q1 Board Meeting")


class TestCmdAttend(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_attend(["bm-2026-03-15"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_default_role_director(self, mock_load, mock_save, mock_commit):
        mock_load.return_value = BOARD_DATA
        board.cmd_attend(["bm-2026-03-15", "Bob"])
        saved_data = mock_save.call_args[0][1]
        last = saved_data["board_attendees"][-1]
        self.assertEqual(last["role"], "director")


class TestCmdVote(unittest.TestCase):
    def test_insufficient_args_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_vote(["bm-2026-03-15-r1"])

    def test_invalid_outcome_exits(self):
        with self.assertRaises(SystemExit):
            board.cmd_vote(["bm-2026-03-15-r1", "maybe"])

    @patch("datalib.git_commit")
    @patch("datalib.save")
    @patch("datalib.load")
    def test_vote_passed(self, mock_load, mock_save, mock_commit):
        data = {
            "board_meetings": BOARD_DATA["board_meetings"],
            "board_attendees": [],
            "board_minutes": [],
            "board_resolutions": [
                {"id": "bm-2026-03-15-r1", "meeting_id": "bm-2026-03-15",
                 "resolution_text": "Test", "status": "pending",
                 "proposed_by": "", "voted_date": ""},
            ],
        }
        mock_load.return_value = data
        board.cmd_vote(["bm-2026-03-15-r1", "passed"])
        saved_data = mock_save.call_args[0][1]
        res = saved_data["board_resolutions"][0]
        self.assertEqual(res["status"], "passed")


class TestCmdMeetings(unittest.TestCase):
    @patch("datalib.load")
    def test_no_meetings(self, mock_load):
        mock_load.return_value = {"board_meetings": [], "board_attendees": [], "board_resolutions": []}
        board.cmd_meetings()

    @patch("datalib.load")
    def test_with_meetings(self, mock_load):
        mock_load.return_value = BOARD_DATA
        board.cmd_meetings()


class TestRouting(unittest.TestCase):
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
    @patch("datalib.load")
    def test_build_meetings_page(self, mock_load):
        mock_load.return_value = BOARD_DATA
        html = board.build_meetings_page()
        self.assertIn("Board Meetings", html)
        self.assertIn("Q1 Board Meeting", html)
        self.assertIn("<!DOCTYPE html>", html)

    @patch("datalib.load")
    def test_build_resolutions_page_empty(self, mock_load):
        mock_load.return_value = {"board_meetings": [], "board_attendees": [], "board_minutes": [], "board_resolutions": []}
        html = board.build_resolutions_page()
        self.assertIn("No resolutions recorded", html)

    @patch("datalib.load")
    def test_build_meeting_detail_not_found(self, mock_load):
        mock_load.return_value = {"board_meetings": [], "board_attendees": [], "board_minutes": [], "board_resolutions": []}
        result = board.build_meeting_detail("bm-nonexistent")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
