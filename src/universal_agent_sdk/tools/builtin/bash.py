"""Bash tool for executing shell commands."""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from ...types import ToolDefinition


class BashTool:
    """Execute bash commands in a shell.

    This tool executes shell commands and returns their output.
    It supports timeouts, working directory specification, and
    environment variable customization.
    """

    name = "Bash"
    description = """Executes a bash command in a shell.

Usage:
- Commands run in a bash shell with the specified working directory
- Output includes both stdout and stderr
- Commands have a configurable timeout (default 120 seconds)
- Use for: git, npm, docker, running scripts, etc.
- Do NOT use for file operations - use Read/Write/Edit tools instead
"""

    MAX_OUTPUT_LENGTH = 30000

    def __init__(
        self,
        timeout: float = 120.0,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ):
        """Initialize the Bash tool.

        Args:
            timeout: Command timeout in seconds (default 120)
            cwd: Working directory for commands
            env: Additional environment variables
        """
        self.timeout = timeout
        self.cwd = Path(cwd) if cwd else None
        self.env = env

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional timeout in seconds (max 600)",
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what the command does",
                },
            },
            "required": ["command"],
        }

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for the command."""
        env = os.environ.copy()
        if self.env:
            env.update(self.env)
        return env

    async def __call__(
        self,
        command: str,
        timeout: float | None = None,
        description: str | None = None,
    ) -> str:
        """Execute a bash command.

        Args:
            command: The command to execute
            timeout: Optional timeout override (max 600 seconds)
            description: Optional description (for logging)

        Returns:
            Command output (stdout + stderr) or error message
        """
        # Validate and cap timeout
        cmd_timeout = min(timeout or self.timeout, 600.0)

        # Determine working directory
        cwd = self.cwd or Path.cwd()

        try:
            # Run the command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=self._get_env(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=cmd_timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: Command timed out after {cmd_timeout} seconds"

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Build result
            result_parts = []

            if stdout_str:
                result_parts.append(stdout_str)

            if stderr_str:
                if result_parts:
                    result_parts.append(f"\nSTDERR:\n{stderr_str}")
                else:
                    result_parts.append(f"STDERR:\n{stderr_str}")

            if not result_parts:
                result_parts.append("(no output)")

            result = "".join(result_parts)

            # Add exit code if non-zero
            if process.returncode != 0:
                result = f"Exit code: {process.returncode}\n\n{result}"

            # Truncate if too long
            if len(result) > self.MAX_OUTPUT_LENGTH:
                result = result[: self.MAX_OUTPUT_LENGTH] + "\n\n... (output truncated)"

            return result

        except FileNotFoundError:
            return f"Error: Command not found or working directory doesn't exist: {cwd}"
        except PermissionError:
            return "Error: Permission denied executing command"
        except Exception as e:
            return f"Error executing command: {e}"

    def run_sync(
        self,
        command: str,
        timeout: float | None = None,
    ) -> str:
        """Execute a bash command synchronously.

        This is a convenience method for non-async contexts.

        Args:
            command: The command to execute
            timeout: Optional timeout override

        Returns:
            Command output or error message
        """
        cmd_timeout = min(timeout or self.timeout, 600.0)
        cwd = self.cwd or Path.cwd()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=cmd_timeout,
                cwd=str(cwd),
                env=self._get_env(),
            )

            output = result.stdout
            if result.stderr:
                if output:
                    output += f"\nSTDERR:\n{result.stderr}"
                else:
                    output = f"STDERR:\n{result.stderr}"

            if not output:
                output = "(no output)"

            if result.returncode != 0:
                output = f"Exit code: {result.returncode}\n\n{output}"

            if len(output) > self.MAX_OUTPUT_LENGTH:
                output = output[: self.MAX_OUTPUT_LENGTH] + "\n\n... (output truncated)"

            return output

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {cmd_timeout} seconds"
        except Exception as e:
            return f"Error executing command: {e}"

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
