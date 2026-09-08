from enum import Enum
from typing import Dict, List, Optional


class CommandIntent(Enum):
    OPEN_APPLICATION = "OPEN_APPLICATION"
    OPEN_FOLDER = "OPEN_FOLDER"
    GET_TIME = "GET_TIME"
    GET_DATE = "GET_DATE"
    EXIT_APPLICATION = "EXIT_APPLICATION"
    UNKNOWN = "UNKNOWN"


class CommandRegistry:
    """
    Registry of pre-registered, whitelisted voice commands, intents, and phrase aliases.
    """

    # Whitelist map of application keys to executable names / launch targets
    APPLICATIONS = {
        "NOTEPAD": {
            "aliases": ["notepad", "notes", "text editor"],
            "executables": ["notepad.exe"],
            "display_name": "Notepad",
        },
        "CALCULATOR": {
            "aliases": ["calculator", "calc"],
            "executables": ["calc.exe"],
            "display_name": "Calculator",
        },
        "PAINT": {
            "aliases": ["paint", "mspaint", "drawing"],
            "executables": ["mspaint.exe"],
            "display_name": "Paint",
        },
        "EXPLORER": {
            "aliases": ["file explorer", "explorer", "my computer", "this pc", "files"],
            "executables": ["explorer.exe"],
            "display_name": "File Explorer",
        },
        "CHROME": {
            "aliases": ["chrome", "google chrome", "browser", "web browser"],
            "executables": ["chrome.exe"],
            "display_name": "Google Chrome",
        },
        "VSCODE": {
            "aliases": ["vs code", "vscode", "code", "visual studio code"],
            "executables": ["code.cmd", "code.exe", "code"],
            "display_name": "VS Code",
        },
    }

    # Whitelist map of folder keys to special folder names / environment variables
    FOLDERS = {
        "DOWNLOADS": {
            "aliases": ["downloads", "download folder", "downloads folder", "my downloads"],
            "folder_name": "Downloads",
            "display_name": "Downloads Folder",
        },
        "DESKTOP": {
            "aliases": ["desktop", "desktop folder", "my desktop"],
            "folder_name": "Desktop",
            "display_name": "Desktop Folder",
        },
    }

    # Time command aliases
    TIME_ALIASES = [
        "time", "current time", "what time is it", "tell current time",
        "tell me the time", "what is the time", "clock"
    ]

    # Date command aliases
    DATE_ALIASES = [
        "date", "current date", "what date is it", "tell current date",
        "tell me the date", "what is the date", "today's date", "todays date"
    ]

    # Exit command aliases
    EXIT_ALIASES = [
        "exit", "quit", "stop", "close", "shutdown", "exit vocalis",
        "close vocalis", "stop vocalis", "bye", "goodbye"
    ]
