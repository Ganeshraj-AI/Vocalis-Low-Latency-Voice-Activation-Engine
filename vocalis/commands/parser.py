import re
from dataclasses import dataclass
from vocalis.commands.registry import CommandIntent, CommandRegistry


@dataclass
class ParsedCommand:
    intent: CommandIntent
    target: str
    action_description: str
    is_valid: bool
    raw_text: str
    normalized_text: str


class CommandParser:
    """
    Parses and normalizes recognized text into structured intent and target objects.
    Enforces strict whitelist security filtering to reject arbitrary shell commands.
    """

    # Dangerous keywords to explicitly block
    BLACK_LIST_KEYWORDS = [
        "delete", "format", "rmdir", "rm ", "drop", "exec", "powershell",
        "cmd.exe", "del ", "system32", "shutdown -", "reg ", "icacls", "net user"
    ]

    # Common polite filler phrases to strip during normalization
    FILLER_PREFIXES = [
        "please ", "can you ", "could you ", "would you ",
        "i want to ", "kindly ", "hey jarvis ", "jarvis "
    ]

    def normalize(self, text: str) -> str:
        """
        Normalizes raw input text by lowercasing, stripping punctuation, and trimming filler phrases.
        """
        if not text:
            return ""

        # Lowercase and trim leading/trailing whitespace
        norm = text.lower().strip()

        # Remove leading/trailing punctuation marks
        norm = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", norm)

        # Strip common filler prefixes
        for prefix in self.FILLER_PREFIXES:
            if norm.startswith(prefix):
                norm = norm[len(prefix):].strip()

        return norm

    def parse(self, text: str) -> ParsedCommand:
        """
        Parses raw text and returns a validated ParsedCommand object.
        """
        if not text or not text.strip():
            return ParsedCommand(
                intent=CommandIntent.UNKNOWN,
                target="NONE",
                action_description="No speech text provided.",
                is_valid=False,
                raw_text=text or "",
                normalized_text=""
            )

        norm_text = self.normalize(text)

        # 1. Security Check: Explicit Blacklist Filter
        for danger in self.BLACK_LIST_KEYWORDS:
            if danger in norm_text:
                return ParsedCommand(
                    intent=CommandIntent.UNKNOWN,
                    target="SECURITY_BLOCKED",
                    action_description="Blocked: Unauthorized command.",
                    is_valid=False,
                    raw_text=text,
                    normalized_text=norm_text
                )

        # 2. Check EXIT Intent
        for alias in CommandRegistry.EXIT_ALIASES:
            if norm_text == alias or norm_text.endswith(" " + alias) or norm_text.startswith(alias + " "):
                return ParsedCommand(
                    intent=CommandIntent.EXIT_APPLICATION,
                    target="VOCALIS",
                    action_description="Exiting Vocalis engine...",
                    is_valid=True,
                    raw_text=text,
                    normalized_text=norm_text
                )

        # 3. Check GET_TIME Intent
        for alias in CommandRegistry.TIME_ALIASES:
            if alias in norm_text:
                return ParsedCommand(
                    intent=CommandIntent.GET_TIME,
                    target="SYSTEM_TIME",
                    action_description="Fetching current system time...",
                    is_valid=True,
                    raw_text=text,
                    normalized_text=norm_text
                )

        # 4. Check GET_DATE Intent
        for alias in CommandRegistry.DATE_ALIASES:
            if alias in norm_text:
                return ParsedCommand(
                    intent=CommandIntent.GET_DATE,
                    target="SYSTEM_DATE",
                    action_description="Fetching current system date...",
                    is_valid=True,
                    raw_text=text,
                    normalized_text=norm_text
                )

        # 5. Check OPEN_APPLICATION Intent
        for app_key, metadata in CommandRegistry.APPLICATIONS.items():
            for alias in metadata["aliases"]:
                # Match exact alias or alias preceded by verb (e.g. "open notepad", "launch calc")
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, norm_text):
                    return ParsedCommand(
                        intent=CommandIntent.OPEN_APPLICATION,
                        target=app_key,
                        action_description=f"Launching {metadata['display_name']}...",
                        is_valid=True,
                        raw_text=text,
                        normalized_text=norm_text
                    )

        # 6. Check OPEN_FOLDER Intent
        for folder_key, metadata in CommandRegistry.FOLDERS.items():
            for alias in metadata["aliases"]:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, norm_text):
                    return ParsedCommand(
                        intent=CommandIntent.OPEN_FOLDER,
                        target=folder_key,
                        action_description=f"Opening {metadata['display_name']}...",
                        is_valid=True,
                        raw_text=text,
                        normalized_text=norm_text
                    )

        # 7. Default / Unknown Command
        return ParsedCommand(
            intent=CommandIntent.UNKNOWN,
            target="NONE",
            action_description="Command not recognized.",
            is_valid=False,
            raw_text=text,
            normalized_text=norm_text
        )
