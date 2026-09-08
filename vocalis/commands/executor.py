import os
import shutil
import subprocess
from datetime import datetime
from dataclasses import dataclass
from vocalis.commands.registry import CommandIntent, CommandRegistry
from vocalis.commands.parser import ParsedCommand


@dataclass
class ExecutionResult:
    success: bool
    result_message: str
    should_exit: bool = False


class CommandExecutor:
    """
    Safely executes validated, whitelisted commands without invoking raw shell strings.
    """

    def execute(self, command: ParsedCommand) -> ExecutionResult:
        """
        Executes a parsed command and returns an ExecutionResult object.
        """
        if not command or not command.is_valid:
            return ExecutionResult(
                success=False,
                result_message=command.action_description if command else "Command not recognized.",
                should_exit=False
            )

        intent = command.intent

        # 1. Exit Application Intent
        if intent == CommandIntent.EXIT_APPLICATION:
            return ExecutionResult(
                success=True,
                result_message="✓ Stopping Vocalis V4... Goodbye!",
                should_exit=True
            )

        # 2. Get Time Intent
        if intent == CommandIntent.GET_TIME:
            now_time = datetime.now().strftime("%I:%M %p").lstrip("0")
            return ExecutionResult(
                success=True,
                result_message=f"✓ Current Time: {now_time}",
                should_exit=False
            )

        # 3. Get Date Intent
        if intent == CommandIntent.GET_DATE:
            now_date = datetime.now().strftime("%A, %B %d, %Y")
            return ExecutionResult(
                success=True,
                result_message=f"✓ Current Date: {now_date}",
                should_exit=False
            )

        # 4. Open Application Intent
        if intent == CommandIntent.OPEN_APPLICATION:
            app_info = CommandRegistry.APPLICATIONS.get(command.target)
            if not app_info:
                return ExecutionResult(
                    success=False,
                    result_message=f"{command.target} configuration not found.",
                    should_exit=False
                )

            display_name = app_info["display_name"]
            executables = app_info["executables"]

            launched = False
            for exe in executables:
                try:
                    # Check if executable exists in PATH or is a standard system binary
                    exe_path = shutil.which(exe) or exe
                    subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched = True
                    break
                except Exception:
                    continue

            if launched:
                return ExecutionResult(
                    success=True,
                    result_message=f"✓ {display_name} opened",
                    should_exit=False
                )
            else:
                return ExecutionResult(
                    success=False,
                    result_message=f"{display_name} was not found on this computer.",
                    should_exit=False
                )

        # 5. Open Folder Intent
        if intent == CommandIntent.OPEN_FOLDER:
            folder_info = CommandRegistry.FOLDERS.get(command.target)
            if not folder_info:
                return ExecutionResult(
                    success=False,
                    result_message=f"{command.target} folder configuration not found.",
                    should_exit=False
                )

            display_name = folder_info["display_name"]
            folder_name = folder_info["folder_name"]
            target_path = os.path.abspath(os.path.expanduser(f"~/{folder_name}"))

            if os.path.exists(target_path):
                try:
                    if hasattr(os, "startfile"):
                        os.startfile(target_path)
                    else:
                        subprocess.Popen(["explorer.exe", target_path])
                    return ExecutionResult(
                        success=True,
                        result_message=f"✓ {display_name} opened",
                        should_exit=False
                    )
                except Exception as err:
                    return ExecutionResult(
                        success=False,
                        result_message=f"Failed to open {display_name}: {err}",
                        should_exit=False
                    )
            else:
                return ExecutionResult(
                    success=False,
                    result_message=f"{display_name} path not found.",
                    should_exit=False
                )

        # Fallback
        return ExecutionResult(
            success=False,
            result_message="Command not recognized.",
            should_exit=False
        )
