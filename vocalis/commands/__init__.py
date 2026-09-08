"""
Command understanding and execution package for Vocalis V4.
"""
from vocalis.commands.registry import CommandIntent, CommandRegistry
from vocalis.commands.parser import CommandParser, ParsedCommand
from vocalis.commands.executor import CommandExecutor, ExecutionResult

__all__ = [
    "CommandIntent",
    "CommandRegistry",
    "CommandParser",
    "ParsedCommand",
    "CommandExecutor",
    "ExecutionResult",
]
