"""Container management for agent execution."""

import asyncio
import json
import logging
import os
import subprocess
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class ContainerProvider(ABC):
    """Abstract base class for container providers."""

    @abstractmethod
    async def create_container(
        self,
        session_id: str,
        agent_id: str,
        config: dict,
        api_key: str,
    ) -> dict:
        """Create and start a container for the agent."""
        pass

    @abstractmethod
    async def stop_container(self, container_info: dict) -> None:
        """Stop and remove a container."""
        pass

    @abstractmethod
    async def execute_query(
        self,
        container_info: dict,
        message: str,
        history: list[dict],
    ) -> AsyncIterator[str]:
        """Execute a query against the agent container."""
        pass

    @abstractmethod
    async def health_check(self, container_info: dict) -> bool:
        """Check if the container is healthy."""
        pass


class DockerProvider(ContainerProvider):
    """Docker-based container provider."""

    def __init__(self):
        self.network_name = settings.container_network
        self.image_name = settings.agent_image

    async def create_container(
        self,
        session_id: str,
        agent_id: str,
        config: dict,
        api_key: str,
    ) -> dict:
        """Create a Docker container for the agent."""
        container_name = f"uas-{agent_id}"
        workspace_volume = f"uas-workspace-{agent_id}"

        # Prepare environment variables
        # Use environment variables for API keys, with fallback to provided api_key
        env_vars = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", api_key),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", api_key),
            "AGENT_CONFIG_JSON": json.dumps(config),
            "SESSION_ID": session_id,
        }

        # Get resource limits
        resource_limits = config.get("resource_limits", {})

        # Convert cpu_quota from microseconds to CPUs
        # Preset format: 100000 = 1 CPU, 200000 = 2 CPUs
        cpu_quota = resource_limits.get("cpu_quota", 200000)
        if isinstance(cpu_quota, int) and cpu_quota > 100:
            # Convert from microseconds to CPU count
            cpus = cpu_quota / 100000
        else:
            cpus = float(cpu_quota) if cpu_quota else 2.0

        # Ensure cpus is within valid range
        cpus = max(0.01, min(cpus, 14.0))

        memory_limit = resource_limits.get("memory_limit", "4g")

        # Build docker run command
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--network", self.network_name,
            "-v", f"{workspace_volume}:/workspace",
            "--cpus", str(cpus),
            "--memory", memory_limit,
        ]

        # Add environment variables
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add image name
        cmd.append(self.image_name)

        # Run the container
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            container_id = result.stdout.strip()
            logger.info(f"Created container {container_name} ({container_id[:12]})")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create container: {e.stderr}")
            raise RuntimeError(f"Failed to create container: {e.stderr}")

        # Get container IP
        ip_cmd = [
            "docker", "inspect",
            "-f", "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
            container_name,
        ]
        result = subprocess.run(ip_cmd, capture_output=True, text=True, check=True)
        container_ip = result.stdout.strip()

        # Wait for container to be healthy
        await self._wait_for_healthy(container_ip, 3000)

        return {
            "container_id": container_id,
            "container_name": container_name,
            "container_ip": container_ip,
            "port": 3000,
            "workspace_volume": workspace_volume,
            "provider": "docker",
        }

    async def stop_container(self, container_info: dict) -> None:
        """Stop and remove a Docker container."""
        container_name = container_info.get("container_name")
        workspace_volume = container_info.get("workspace_volume")

        if container_name:
            try:
                # Stop container
                subprocess.run(
                    ["docker", "stop", container_name],
                    capture_output=True,
                    check=False,
                )
                # Remove container
                subprocess.run(
                    ["docker", "rm", container_name],
                    capture_output=True,
                    check=False,
                )
                logger.info(f"Stopped container {container_name}")
            except Exception as e:
                logger.error(f"Error stopping container: {e}")

        if workspace_volume:
            try:
                subprocess.run(
                    ["docker", "volume", "rm", workspace_volume],
                    capture_output=True,
                    check=False,
                )
            except Exception as e:
                logger.error(f"Error removing volume: {e}")

    async def execute_query(
        self,
        container_info: dict,
        message: str,
        history: list[dict],
    ) -> AsyncIterator[str]:
        """Execute a query against the agent container via HTTP."""
        container_ip = container_info["container_ip"]
        port = container_info["port"]
        url = f"http://{container_ip}:{port}/query"

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                url,
                json={"message": message, "history": history},
                headers={"Accept": "text/event-stream"},
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield line

    async def health_check(self, container_info: dict) -> bool:
        """Check if the container is healthy."""
        container_ip = container_info["container_ip"]
        port = container_info["port"]
        url = f"http://{container_ip}:{port}/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def _wait_for_healthy(
        self,
        container_ip: str,
        port: int,
        timeout: int = 60,
    ) -> None:
        """Wait for container to become healthy."""
        url = f"http://{container_ip}:{port}/health"
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        logger.info(f"Container healthy at {container_ip}:{port}")
                        return
            except Exception:
                pass
            await asyncio.sleep(1)

        raise RuntimeError(f"Container failed to become healthy within {timeout}s")


class SubprocessProvider(ContainerProvider):
    """Subprocess-based provider for local development without Docker."""

    def __init__(self):
        self.processes: dict[str, subprocess.Popen] = {}
        self.base_port = 3100

    async def create_container(
        self,
        session_id: str,
        agent_id: str,
        config: dict,
        api_key: str,
    ) -> dict:
        """Create a subprocess for the agent."""
        # Find available port
        port = self.base_port + len(self.processes)

        # Create workspace directory
        workspace_dir = settings.workspace_base_dir / agent_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # Prepare environment
        # Use environment variables for API keys, with fallback to provided api_key
        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", api_key)
        env["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", api_key)
        env["AGENT_CONFIG_JSON"] = json.dumps(config)
        env["SESSION_ID"] = session_id
        env["WORKSPACE_DIR"] = str(workspace_dir)
        env["PORT"] = str(port)

        # Start the agent server subprocess
        container_dir = Path(__file__).parent.parent / "container"
        cmd = [
            "python", "-m", "uvicorn",
            "agent_server:app",
            "--host", "0.0.0.0",
            "--port", str(port),
        ]

        process = subprocess.Popen(
            cmd,
            cwd=container_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.processes[agent_id] = process

        # Wait for server to be ready
        await self._wait_for_healthy("127.0.0.1", port)

        logger.info(f"Started subprocess agent on port {port}")

        return {
            "process_id": process.pid,
            "agent_id": agent_id,
            "container_ip": "127.0.0.1",
            "port": port,
            "workspace_dir": str(workspace_dir),
            "provider": "subprocess",
        }

    async def stop_container(self, container_info: dict) -> None:
        """Stop a subprocess agent."""
        agent_id = container_info.get("agent_id")
        process = self.processes.pop(agent_id, None)

        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info(f"Stopped subprocess agent {agent_id}")

    async def execute_query(
        self,
        container_info: dict,
        message: str,
        history: list[dict],
    ) -> AsyncIterator[str]:
        """Execute a query against the subprocess agent."""
        container_ip = container_info["container_ip"]
        port = container_info["port"]
        url = f"http://{container_ip}:{port}/query"

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                url,
                json={"message": message, "history": history},
                headers={"Accept": "text/event-stream"},
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield line

    async def health_check(self, container_info: dict) -> bool:
        """Check if the subprocess agent is healthy."""
        container_ip = container_info["container_ip"]
        port = container_info["port"]
        url = f"http://{container_ip}:{port}/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def _wait_for_healthy(
        self,
        host: str,
        port: int,
        timeout: int = 30,
    ) -> None:
        """Wait for subprocess to become healthy."""
        url = f"http://{host}:{port}/health"
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        logger.info(f"Subprocess healthy at {host}:{port}")
                        return
            except Exception:
                pass
            await asyncio.sleep(0.5)

        raise RuntimeError(f"Subprocess failed to become healthy within {timeout}s")


class ContainerManager:
    """Manages container lifecycle using the configured provider."""

    def __init__(self):
        self.provider = self._get_provider()

    def _get_provider(self) -> ContainerProvider:
        """Get the configured container provider."""
        provider_type = settings.container_provider

        if provider_type == "docker":
            return DockerProvider()
        elif provider_type == "subprocess":
            return SubprocessProvider()
        else:
            raise ValueError(f"Unknown container provider: {provider_type}")

    async def create_agent_container(
        self,
        session_id: str,
        agent_id: str,
        config: dict,
        api_key: str,
    ) -> dict:
        """Create an agent container."""
        return await self.provider.create_container(
            session_id=session_id,
            agent_id=agent_id,
            config=config,
            api_key=api_key,
        )

    async def stop_container(self, container_info: dict) -> None:
        """Stop a container."""
        await self.provider.stop_container(container_info)

    async def execute_query(
        self,
        container_info: dict,
        message: str,
        history: list[dict],
    ) -> AsyncIterator[str]:
        """Execute a query against a container."""
        async for line in self.provider.execute_query(
            container_info=container_info,
            message=message,
            history=history,
        ):
            yield line

    async def health_check(self, container_info: dict) -> bool:
        """Check container health."""
        return await self.provider.health_check(container_info)


# Global container manager instance
container_manager = ContainerManager()
