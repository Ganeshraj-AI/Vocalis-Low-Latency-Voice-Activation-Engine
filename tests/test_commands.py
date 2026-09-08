import unittest
from vocalis.commands.parser import CommandParser
from vocalis.commands.registry import CommandIntent
from vocalis.commands.executor import CommandExecutor


class TestCommandParser(unittest.TestCase):
    def setUp(self):
        self.parser = CommandParser()
        self.executor = CommandExecutor()

    def test_open_application_notepad(self):
        cmd = self.parser.parse("open notepad")
        self.assertTrue(cmd.is_valid)
        self.assertEqual(cmd.intent, CommandIntent.OPEN_APPLICATION)
        self.assertEqual(cmd.target, "NOTEPAD")

    def test_open_application_variations(self):
        variations = [
            ("launch calculator", "CALCULATOR"),
            ("start paint", "PAINT"),
            ("can you open file explorer", "EXPLORER"),
            ("open chrome", "CHROME"),
            ("open vs code", "VSCODE"),
        ]
        for phrase, expected_target in variations:
            cmd = self.parser.parse(phrase)
            self.assertTrue(cmd.is_valid, f"Failed for phrase: '{phrase}'")
            self.assertEqual(cmd.intent, CommandIntent.OPEN_APPLICATION)
            self.assertEqual(cmd.target, expected_target)

    def test_open_folder(self):
        cmd_downloads = self.parser.parse("open downloads folder")
        self.assertTrue(cmd_downloads.is_valid)
        self.assertEqual(cmd_downloads.intent, CommandIntent.OPEN_FOLDER)
        self.assertEqual(cmd_downloads.target, "DOWNLOADS")

        cmd_desktop = self.parser.parse("open desktop")
        self.assertTrue(cmd_desktop.is_valid)
        self.assertEqual(cmd_desktop.intent, CommandIntent.OPEN_FOLDER)
        self.assertEqual(cmd_desktop.target, "DESKTOP")

    def test_get_time(self):
        phrases = ["what time is it", "tell current time", "time"]
        for phrase in phrases:
            cmd = self.parser.parse(phrase)
            self.assertTrue(cmd.is_valid)
            self.assertEqual(cmd.intent, CommandIntent.GET_TIME)

    def test_get_date(self):
        phrases = ["what date is it", "tell current date", "date"]
        for phrase in phrases:
            cmd = self.parser.parse(phrase)
            self.assertTrue(cmd.is_valid)
            self.assertEqual(cmd.intent, CommandIntent.GET_DATE)

    def test_exit(self):
        cmd = self.parser.parse("exit vocalis")
        self.assertTrue(cmd.is_valid)
        self.assertEqual(cmd.intent, CommandIntent.EXIT_APPLICATION)

    def test_security_whitelist(self):
        dangerous_commands = [
            "delete all files",
            "format my drive",
            "run powershell script",
            "exec cmd.exe",
            "del C:\\System32",
        ]
        for danger in dangerous_commands:
            cmd = self.parser.parse(danger)
            self.assertFalse(cmd.is_valid, f"Security breach: Dangerous command accepted: '{danger}'")

    def test_unknown_command(self):
        cmd = self.parser.parse("what is the meaning of life")
        self.assertFalse(cmd.is_valid)
        self.assertEqual(cmd.intent, CommandIntent.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
