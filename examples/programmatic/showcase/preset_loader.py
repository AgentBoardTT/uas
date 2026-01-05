#!/usr/bin/env python3
"""Preset Loading Example - Load a preset and start an interactive conversation.

This example demonstrates how to:
1. Load an agent preset from a YAML/JSON file
2. Start an interactive conversation with the loaded agent

Prerequisites:
    pip install pyyaml  # Required for YAML preset loading

Usage:
    # List available presets
    uv run python examples/programmatic/showcase/preset_loader.py --list

    # Use a specific preset file
    uv run python examples/programmatic/showcase/preset_loader.py --preset path/to/preset.yaml

    # Use a preset by ID (searches in examples/programmatic/presets/)
    uv run python examples/programmatic/showcase/preset_loader.py --preset virtual-assistant

    # Show preset info without starting chat
    uv run python examples/programmatic/showcase/preset_loader.py --preset code-assistant --info
"""

import argparse
import asyncio
import sys
from pathlib import Path

from universal_agent_sdk import (
    AgentPreset,
    AssistantMessage,
    StreamEvent,
    UniversalAgentClient,
    discover_presets,
    load_preset,
    preset_to_options_with_tools,
)


def get_default_preset_dir() -> Path:
    """Get the default presets directory."""
    # Presets are at ../presets relative to showcase/
    return Path(__file__).parent.parent / "presets"


def list_available_presets() -> None:
    """List all available presets."""
    preset_dir = get_default_preset_dir()
    presets = discover_presets([preset_dir])

    if not presets:
        print("No presets found in:", preset_dir)
        return

    print("\n" + "=" * 60)
    print("Available Presets")
    print("=" * 60 + "\n")

    for preset_id, preset in sorted(presets.items()):
        print(f"  {preset_id}")
        print(f"    Name: {preset.name}")
        print(f"    Description: {preset.description or 'N/A'}")
        if preset.model:
            print(f"    Model: {preset.model}")
        print()

    print("Usage:")
    print(f"  python {Path(__file__).name} --preset <preset-id>")
    print(f"  python {Path(__file__).name} --preset <path-to-preset.yaml>")
    print()


def show_preset_info(preset: AgentPreset) -> None:
    """Display detailed information about a preset."""
    print("\n" + "=" * 60)
    print(f"Preset: {preset.name}")
    print("=" * 60)

    print(f"\n  ID: {preset.id}")
    print(f"  Description: {preset.description or 'N/A'}")
    print(f"  Version: {preset.version or 'N/A'}")
    print(f"  Model: {preset.model or 'default'}")
    print(f"  Provider: {preset.provider}")
    print(f"  Max Turns: {preset.max_turns or 'default'}")
    print(f"  Permission Mode: {preset.permission_mode or 'default'}")

    if preset.allowed_tools:
        print(f"\n  Allowed Tools ({len(preset.allowed_tools)}):")
        for tool in preset.allowed_tools:
            print(f"    - {tool}")

    if preset.skills:
        print(f"\n  Skills ({len(preset.skills)}):")
        for skill in preset.skills:
            print(f"    - {skill}")

    if preset.agents:
        print(f"\n  Sub-Agents ({len(preset.agents)}):")
        for name, agent in preset.agents.items():
            print(f"    - {name}: {agent.description[:60]}...")

    if preset.resource_limits:
        print("\n  Resource Limits:")
        if preset.resource_limits.cpu_quota:
            print(f"    CPU Quota: {preset.resource_limits.cpu_quota}")
        if preset.resource_limits.memory_limit:
            print(f"    Memory: {preset.resource_limits.memory_limit}")
        if preset.resource_limits.storage_limit:
            print(f"    Storage: {preset.resource_limits.storage_limit}")

    # System prompt info
    print("\n  System Prompt:")
    if isinstance(preset.system_prompt, str):
        preview = preset.system_prompt[:100].replace("\n", " ")
        print(f"    Type: String ({len(preset.system_prompt)} chars)")
        print(f"    Preview: {preview}...")
    elif preset.system_prompt:
        print(f"    Type: Preset ({preset.system_prompt.preset})")
        if preset.system_prompt.append:
            print(f"    Appended: {len(preset.system_prompt.append)} chars")

    print()


def load_preset_by_id_or_path(preset_arg: str) -> AgentPreset:
    """Load a preset by ID or file path."""
    # First, try as a file path
    path = Path(preset_arg)
    if path.exists():
        return load_preset(path)

    # Try in the default presets directory
    preset_dir = get_default_preset_dir()

    # Try with extension
    for ext in [".yaml", ".yml", ".json"]:
        preset_file = preset_dir / f"{preset_arg}{ext}"
        if preset_file.exists():
            return load_preset(preset_file)

    # Try to find by ID in discovered presets
    presets = discover_presets([preset_dir])
    if preset_arg in presets:
        return presets[preset_arg]

    # Not found
    raise FileNotFoundError(
        f"Preset not found: {preset_arg}\n"
        f"Searched in: {preset_dir}\n"
        f"Use --list to see available presets."
    )


async def run_conversation(preset: AgentPreset) -> None:
    """Run an interactive conversation with the loaded preset."""
    print("\n" + "=" * 60)
    print(f"  {preset.name}")
    print("=" * 60)
    if preset.description:
        print(f"\n  {preset.description}")
    print("\n  Type 'quit', 'exit', or 'q' to end the conversation.")
    print("  Type 'info' to show preset details.")
    print("=" * 60 + "\n")

    # Convert preset to options with tools auto-loaded
    options = preset_to_options_with_tools(preset)
    options.stream = True

    # Show tools info
    if options.tools:
        print(f"  Loaded {len(options.tools)} tool(s): {', '.join(t.name for t in options.tools)}\n")

    async with UniversalAgentClient(options) as client:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break

            if user_input.lower() == "info":
                show_preset_info(preset)
                continue

            await client.send(user_input)

            print("\nAssistant: ", end="", flush=True)

            async for msg in client.receive():
                if isinstance(msg, StreamEvent):
                    # Print streaming text as it arrives (handle both "text" and "text_delta" types)
                    delta_type = msg.delta.get("type") if msg.delta else None
                    if delta_type in ("text", "text_delta"):
                        print(msg.delta.get("text", ""), end="", flush=True)
                elif isinstance(msg, AssistantMessage):
                    # If not streaming, print the full response
                    pass

            print("\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load an agent preset and start an interactive conversation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                              List available presets
  %(prog)s --preset code-assistant             Use preset by ID
  %(prog)s --preset presets/custom.yaml        Use preset file
  %(prog)s --preset code-assistant --info      Show preset info only

Available presets (in examples/presets/):
  code-assistant      Full-stack development agent
  data-analysis       Statistical analysis specialist
  fullstack-team      Multi-agent development team
  research-agent      Web research specialist
  creative-developer  Creative coding agent
  developer-assistant Developer assistant (example)
""",
    )

    parser.add_argument(
        "--preset",
        "-p",
        type=str,
        help="Preset ID or path to preset file (YAML/JSON)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available presets",
    )
    parser.add_argument(
        "--info",
        "-i",
        action="store_true",
        help="Show preset info without starting conversation",
    )

    args = parser.parse_args()

    # List presets
    if args.list:
        list_available_presets()
        return

    # No preset specified
    if not args.preset:
        parser.print_help()
        print("\n" + "-" * 60)
        list_available_presets()
        return

    # Load preset
    try:
        preset = load_preset_by_id_or_path(args.preset)
    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError loading preset: {e}", file=sys.stderr)
        sys.exit(1)

    # Show info only
    if args.info:
        show_preset_info(preset)
        return

    # Run conversation
    try:
        asyncio.run(run_conversation(preset))
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")


if __name__ == "__main__":
    main()
