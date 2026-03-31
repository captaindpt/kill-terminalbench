"""Task runner for Terminal-Bench task directories."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .agent import AgentConfig, AgentResult, run_agent, run_bash_in_container


@dataclass
class Task:
    task_id: str
    instruction: str
    difficulty: str
    category: str
    max_agent_timeout_sec: float
    max_test_timeout_sec: float
    task_dir: Path
    parser_name: str = "pytest"
    run_tests_in_same_shell: bool = False


@dataclass
class TaskResult:
    task_id: str
    passed: bool
    agent_result: AgentResult
    test_output: str = ""
    error: Optional[str] = None


@dataclass
class ContainerHandle:
    name: str
    runtime_dir: Path
    compose_file: Path | None = None
    compose_env: dict[str, str] | None = None


def load_task(task_dir: Path) -> Task:
    """Load a task from its directory."""
    task_yaml = task_dir / "task.yaml"
    with open(task_yaml) as f:
        data = yaml.safe_load(f)

    return Task(
        task_id=task_dir.name,
        instruction=data["instruction"],
        difficulty=data.get("difficulty", "unknown"),
        category=data.get("category", "unknown"),
        max_agent_timeout_sec=data.get("max_agent_timeout_sec", 900.0),
        max_test_timeout_sec=data.get("max_test_timeout_sec", 180.0),
        task_dir=task_dir,
        parser_name=data.get("parser_name", "pytest"),
        run_tests_in_same_shell=data.get("run_tests_in_same_shell", False),
    )


def _run_checked(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=timeout,
        check=True,
    )


def _compose_env(task: Task, container_name: str, runtime_dir: Path) -> dict[str, str]:
    return {
        **os.environ,
        "T_BENCH_TASK_DOCKER_CLIENT_CONTAINER_NAME": container_name,
        "T_BENCH_TASK_DOCKER_CLIENT_IMAGE_NAME": f"ktb-{task.task_id}:{container_name}",
        "T_BENCH_TASK_DOCKER_NAME_PREFIX": container_name,
        "T_BENCH_CONTAINER_LOGS_PATH": "/logs",
        "T_BENCH_CONTAINER_AGENT_LOGS_PATH": "/agent-logs",
        "T_BENCH_TEST_DIR": "/tests",
        "T_BENCH_TASK_LOGS_PATH": str((runtime_dir / "logs").resolve()),
        "T_BENCH_TASK_AGENT_LOGS_PATH": str((runtime_dir / "agent-logs").resolve()),
    }


def _copy_to_container(container_name: str, source: Path, destination: str) -> None:
    _run_checked(["docker", "cp", str(source), f"{container_name}:{destination}"])


def _expand_placeholders(value: str, env: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return env.get(key, match.group(0))

    return re.sub(r"\$\{([^}]+)\}", replace, value)


def _compose_command(compose_file: Path, project_name: str) -> list[str] | None:
    docker_compose_v2 = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        text=True,
    )
    if docker_compose_v2.returncode == 0:
        return [
            "docker",
            "compose",
            "-p",
            project_name,
            "-f",
            str(compose_file.resolve()),
        ]

    if shutil.which("docker-compose"):
        return [
            "docker-compose",
            "-p",
            project_name,
            "-f",
            str(compose_file.resolve()),
        ]

    return None


def _start_single_service_without_compose(
    task: Task,
    container_name: str,
    runtime_dir: Path,
    compose_file: Path,
    env: dict[str, str],
) -> ContainerHandle:
    with open(compose_file) as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    if len(services) != 1:
        raise RuntimeError(
            "docker compose is not available and this task requires multiple services"
        )

    _, service = next(iter(services.items()))
    build_config = service.get("build", {})
    if isinstance(build_config, str):
        build_context = task.task_dir / build_config
        dockerfile = build_context / "Dockerfile"
    else:
        build_context = task.task_dir / build_config.get("context", ".")
        dockerfile = task.task_dir / build_config.get("dockerfile", "Dockerfile")

    image_name = env["T_BENCH_TASK_DOCKER_CLIENT_IMAGE_NAME"]
    _run_checked(
        [
            "docker",
            "build",
            "-f",
            str(dockerfile.resolve()),
            "-t",
            image_name,
            str(build_context.resolve()),
        ],
        cwd=task.task_dir,
    )

    command = ["docker", "run", "-d", "--name", container_name]

    for volume in service.get("volumes", []):
        command.extend(["-v", _expand_placeholders(volume, env)])

    for port in service.get("ports", []):
        command.extend(["-p", _expand_placeholders(port, env)])

    environment = service.get("environment", {})
    if isinstance(environment, list):
        for item in environment:
            command.extend(["-e", _expand_placeholders(item, env)])
    elif isinstance(environment, dict):
        for key, value in environment.items():
            expanded = _expand_placeholders(str(value), env)
            command.extend(["-e", f"{key}={expanded}"])

    working_dir = service.get("working_dir")
    if working_dir:
        command.extend(["-w", _expand_placeholders(working_dir, env)])

    command.append(image_name)

    service_command = service.get("command")
    if isinstance(service_command, str):
        command.extend(["bash", "-lc", _expand_placeholders(service_command, env)])
    elif isinstance(service_command, list):
        command.extend(_expand_placeholders(str(part), env) for part in service_command)

    _run_checked(command, cwd=task.task_dir, timeout=30)
    return ContainerHandle(name=container_name, runtime_dir=runtime_dir)


def start_container(task: Task) -> ContainerHandle:
    """Start the task container and return its handle."""
    container_name = f"ktb-{task.task_id}-{uuid.uuid4().hex[:8]}"
    runtime_dir = Path(tempfile.mkdtemp(prefix=f"{container_name}-"))
    (runtime_dir / "logs").mkdir()
    (runtime_dir / "agent-logs").mkdir()

    compose_file = task.task_dir / "docker-compose.yaml"
    if compose_file.exists():
        env = _compose_env(task, container_name, runtime_dir)
        compose_cmd = _compose_command(compose_file, container_name)

        if compose_cmd is None:
            return _start_single_service_without_compose(
                task=task,
                container_name=container_name,
                runtime_dir=runtime_dir,
                compose_file=compose_file,
                env=env,
            )

        try:
            _run_checked([*compose_cmd, "build"], cwd=task.task_dir, env=env)
            _run_checked([*compose_cmd, "up", "-d"], cwd=task.task_dir, env=env)
            _run_checked(["docker", "inspect", container_name], timeout=30)
            return ContainerHandle(
                name=container_name,
                runtime_dir=runtime_dir,
                compose_file=compose_file,
                compose_env=env,
            )
        except Exception:
            stop_container(
                ContainerHandle(
                    name=container_name,
                    runtime_dir=runtime_dir,
                    compose_file=compose_file,
                    compose_env=env,
                )
            )
            raise

    image_name = f"ktb-{task.task_id}:{container_name}"
    try:
        _run_checked(
            ["docker", "build", "-t", image_name, "."],
            cwd=task.task_dir,
        )
        _run_checked(
            ["docker", "run", "-d", "--name", container_name, image_name],
            timeout=30,
        )
        return ContainerHandle(name=container_name, runtime_dir=runtime_dir)
    except Exception:
        stop_container(ContainerHandle(name=container_name, runtime_dir=runtime_dir))
        raise


def stop_container(handle: ContainerHandle) -> None:
    """Stop and remove a container and any compose artifacts."""
    try:
        if handle.compose_file and handle.compose_env:
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-p",
                    handle.name,
                    "-f",
                    str(handle.compose_file.resolve()),
                    "down",
                    "--volumes",
                ],
                capture_output=True,
                text=True,
                env=handle.compose_env,
            )
        else:
            subprocess.run(
                ["docker", "rm", "-f", handle.name],
                capture_output=True,
                text=True,
            )
    finally:
        shutil.rmtree(handle.runtime_dir, ignore_errors=True)


def _run_solution(task: Task, container_name: str) -> AgentResult:
    """Execute the task's reference solution inside the container."""
    solution_path = task.task_dir / "solution.sh"
    if not solution_path.exists():
        raise FileNotFoundError(f"No solution.sh found for task {task.task_id}")

    start = time.time()
    _copy_to_container(container_name, solution_path, "/tmp/solution.sh")
    output = run_bash_in_container(
        container_name,
        "chmod +x /tmp/solution.sh && cd /app && bash /tmp/solution.sh",
        timeout=int(task.max_agent_timeout_sec),
    )
    if "[exit_code=0]" not in output:
        raise RuntimeError(f"Reference solution failed:\n{output}")

    return AgentResult(success=True, num_turns=1, wall_time_sec=time.time() - start)


def run_tests(task: Task, container_name: str) -> tuple[bool, str]:
    """Run the task's test script inside the container."""
    tests_dir = task.task_dir / "tests"
    run_tests_script = task.task_dir / "run-tests.sh"

    if tests_dir.exists():
        _copy_to_container(container_name, tests_dir, "/tests")

    if run_tests_script.exists():
        _copy_to_container(container_name, run_tests_script, "/tests/run-tests.sh")

    output = run_bash_in_container(
        container_name,
        "export TEST_DIR=/tests && chmod +x /tests/run-tests.sh && cd /app && bash /tests/run-tests.sh",
        timeout=int(task.max_test_timeout_sec),
    )

    normalized = output.lower()
    if task.parser_name == "exact_match":
        passed = "PASS" in output
    else:
        passed = (
            "[exit_code=0]" in output
            and "failed" not in normalized
            and "error" not in normalized
            and " passed" in normalized
        )

    return passed, output


def run_task(
    task: Task,
    config: Optional[AgentConfig] = None,
) -> TaskResult:
    """Run a single task end-to-end: start container, run agent, test, cleanup."""
    handle = None
    config = config or AgentConfig()

    try:
        print(f"  [{task.task_id}] Starting container...")
        handle = start_container(task)

        print(f"  [{task.task_id}] Running agent...")
        if config.backend == "solution":
            agent_result = _run_solution(task, handle.name)
        else:
            agent_result = run_agent(
                instruction=task.instruction,
                container_name=handle.name,
                config=config,
            )

        print(f"  [{task.task_id}] Running tests...")
        passed, test_output = run_tests(task, handle.name)

        print(
            f"  [{task.task_id}] {'PASS' if passed else 'FAIL'} "
            f"({agent_result.num_turns} turns, {agent_result.wall_time_sec:.0f}s)"
        )

        return TaskResult(
            task_id=task.task_id,
            passed=passed,
            agent_result=agent_result,
            test_output=test_output,
        )

    except Exception as e:
        print(f"  [{task.task_id}] ERROR: {e}")
        return TaskResult(
            task_id=task.task_id,
            passed=False,
            agent_result=AgentResult(),
            error=str(e),
        )
    finally:
        if handle:
            stop_container(handle)
