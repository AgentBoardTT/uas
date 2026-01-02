"""Basic agent example for Universal Agent SDK.

This example shows how to create and use agents for autonomous task execution.
"""

import asyncio

from universal_agent_sdk import Agent, AgentOptions, SubAgent, tool


# Define some tools for the agents
@tool
def analyze_code(code: str) -> str:
    """Analyze Python code for issues.

    Args:
        code: Python code to analyze
    """
    issues = []

    # Simple static analysis (mock)
    if "eval(" in code:
        issues.append("Security: Avoid using eval()")
    if "import *" in code:
        issues.append("Style: Avoid wildcard imports")
    if len(code.split("\n")) > 50:
        issues.append("Complexity: Function is too long")

    if issues:
        return "Issues found:\n" + "\n".join(f"- {i}" for i in issues)
    return "No issues found. Code looks good!"


@tool
def suggest_improvement(issue: str) -> str:
    """Suggest an improvement for a code issue.

    Args:
        issue: The issue to address
    """
    suggestions = {
        "eval": "Use ast.literal_eval() for safe evaluation",
        "import *": "Import specific names: from module import name1, name2",
        "too long": "Break the function into smaller, focused functions",
    }

    for keyword, suggestion in suggestions.items():
        if keyword.lower() in issue.lower():
            return suggestion

    return "Consider refactoring for better readability"


async def basic_agent_example():
    """Create and run a basic agent."""
    print("=== Basic Agent Example ===\n")

    # Create a code review agent
    reviewer = Agent(
        name="code_reviewer",
        description="Reviews Python code for best practices",
        system_prompt="""You are an expert Python code reviewer.
        Analyze code for bugs, style issues, and security concerns.
        Be constructive and provide actionable feedback.""",
        tools=[analyze_code],
        model="claude-sonnet-4-20250514",
        max_turns=3,
    )

    # Run the agent on a task
    code_sample = '''
def process_data(data):
    from os import *
    result = eval(data)
    return result
'''

    print(f"Reviewing code:\n{code_sample}\n")

    result = await reviewer.run(f"Please review this Python code:\n```python{code_sample}```")
    print(f"Review result:\n{result}")


async def subagent_example():
    """Create agents with sub-agents."""
    print("\n=== SubAgent Example ===\n")

    # Parent agent - orchestrator
    orchestrator = Agent(
        name="orchestrator",
        description="Coordinates code review tasks",
        system_prompt="You coordinate code review by delegating to specialized reviewers.",
    )

    # Sub-agents for specialized tasks
    security_reviewer = SubAgent(
        name="security_reviewer",
        description="Reviews code for security issues",
        system_prompt="You focus on security vulnerabilities in code.",
        parent=orchestrator,
        tools=[analyze_code],
    )

    style_reviewer = SubAgent(
        name="style_reviewer",
        description="Reviews code for style issues",
        system_prompt="You focus on code style and readability.",
        parent=orchestrator,
        tools=[suggest_improvement],
    )

    # Run sub-agents
    code = "data = eval(user_input)"

    print(f"Code to review: {code}\n")

    # Security review
    print("--- Security Review ---")
    security_result = await security_reviewer.run(f"Check this code for security issues: {code}")
    print(f"{security_result}\n")

    # Style review
    print("--- Style Review ---")
    style_result = await style_reviewer.run(f"Suggest improvements for: {code}")
    print(f"{style_result}")


async def agent_with_streaming():
    """Agent with streaming responses."""
    print("\n=== Agent with Streaming ===\n")

    from universal_agent_sdk import AssistantMessage, ResultMessage, StreamEvent, TextBlock

    agent = Agent(
        name="writer",
        description="Creative writing assistant",
        system_prompt="You are a creative writer who writes engaging stories.",
        options=AgentOptions(stream=True),
    )

    print("Task: Write a haiku about programming\n")
    print("Response: ", end="", flush=True)

    async for msg in agent.stream("Write a haiku about programming"):
        if isinstance(msg, StreamEvent):
            if msg.delta and msg.delta.get("type") == "text":
                print(msg.delta.get("text", ""), end="", flush=True)
        elif isinstance(msg, AssistantMessage):
            pass  # Final message
        elif isinstance(msg, ResultMessage):
            print(f"\n\n[Completed in {msg.num_turns} turn(s)]")


async def agent_report():
    """SubAgent with structured report."""
    print("\n=== Agent Report ===\n")

    agent = SubAgent(
        name="analyzer",
        description="Analyzes and reports",
        system_prompt="You provide concise analysis.",
    )

    report = await agent.run_and_report("What are 3 benefits of Python?")

    print(f"Agent: {report['agent']}")
    print(f"Task: {report['task']}")
    print(f"Turns: {report['num_turns']}")
    print(f"Result:\n{report['result']}")


if __name__ == "__main__":
    asyncio.run(basic_agent_example())
    asyncio.run(subagent_example())
    asyncio.run(agent_with_streaming())
    asyncio.run(agent_report())
