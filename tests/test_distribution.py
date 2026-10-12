"""Offline distribution checks: python -m unittest discover -s tests -v."""

import asyncio
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import sysconfig
import tempfile
import time
import unittest

from mcp import ClientSession
from mcp.client.sse import sse_client


class DistributionTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.root = Path(cls.workspace.name)
        source = cls.root / "source"
        source.mkdir()
        repository = Path(__file__).resolve().parents[1]
        for filename in ("pyproject.toml", "README.md"):
            shutil.copy2(repository / filename, source / filename)
        shutil.copytree(
            repository / "src", source / "src",
            ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
        )
        cls.run_command(
            [sys.executable, "-c", "from setuptools.build_meta import build_sdist; build_sdist('sdist')"],
            cwd=source,
        )
        cls.installed = {}
        for kind, origin in (("wheel", source), ("sdist", next((source / "sdist").glob("*.tar.gz")))):
            output = cls.root / kind
            cls.run_command([
                sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-index", "--no-cache-dir",
                "--no-build-isolation", "--wheel-dir", str(output), str(origin),
            ], cwd=cls.root)
            target = cls.root / (kind + "-installed")
            cls.run_command([
                sys.executable, "-m", "pip", "install", "--no-deps", "--no-index", "--no-cache-dir",
                "--target", str(target), str(next(output.glob("*.whl"))),
            ], cwd=cls.root)
            cls.installed[kind] = target

    @staticmethod
    def run_command(command, cwd):
        environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        result = subprocess.run(
            command, cwd=cwd, encoding="utf-8", capture_output=True,
            env=environment, timeout=60,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def isolated_command(self, target, code):
        # -S prevents editable-install .pth files from hiding missing wheel modules.
        # Reuse dependencies only; neither the checkout nor its src/ is importable.
        paths = [str(target), sysconfig.get_path("purelib"), sysconfig.get_path("platlib")]
        prefix = (
            f"import sys; sys.path[:0] = {paths!r}\n"
            "from importlib.metadata import distribution\n"
            "entry = next(ep for ep in distribution('mcp-lite-dev').entry_points "
            "if ep.group == 'console_scripts' and ep.name == 'mcp-lite-dev')\n"
        )
        return [sys.executable, "-X", "utf8", "-I", "-S", "-c", prefix + code]

    def test_installed_entry_point_loads_outside_the_checkout(self):
        for kind, target in self.installed.items():
            with self.subTest(artifact=kind):
                self.run_command(self.isolated_command(target,
                    "from pathlib import Path\n"
                    "assert callable(entry.load())\n"
                    "import weather\n"
                    f"assert Path(weather.__file__).parent == Path({str(target)!r})\n"
                ), cwd=self.root)

    async def test_installed_entry_point_serves_the_weather_tool(self):
        for kind, target in self.installed.items():
            with self.subTest(artifact=kind):
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", 0))
                    port = listener.getsockname()[1]
                command = self.isolated_command(target,
                    "start = entry.load()\n"
                    "import weather\n"
                    "weather.mcp.settings.host = '127.0.0.1'\n"
                    f"weather.mcp.settings.port = {port}\n"
                    "start()\n"
                )
                log_path = self.root / (kind + ".log")
                environment = {**os.environ, "OPENWEATHER_API_KEY": "offline-test", "PYTHONIOENCODING": "utf-8"}
                with log_path.open("w", encoding="utf-8") as log:
                    process = subprocess.Popen(command, cwd=self.root, env=environment, stdout=log, stderr=log)
                    try:
                        deadline = time.monotonic() + 10
                        while True:
                            if process.poll() is not None or time.monotonic() > deadline:
                                self.fail(log_path.read_text(encoding="utf-8"))
                            try:
                                _, writer = await asyncio.open_connection("127.0.0.1", port)
                                writer.close()
                                await writer.wait_closed()
                                break
                            except OSError:
                                await asyncio.sleep(0.05)
                        tools = await asyncio.wait_for(self.list_tools(port), timeout=10)
                        weather = next(tool for tool in tools if tool.name == "query_weather")
                        self.assertIn("city", weather.inputSchema["required"])
                        self.assertEqual(weather.inputSchema["properties"]["city"]["type"], "string")
                    finally:
                        if process.poll() is None:
                            process.terminate()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=10)

    @staticmethod
    async def list_tools(port):
        async with sse_client(f"http://127.0.0.1:{port}/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return (await session.list_tools()).tools


if __name__ == "__main__":
    unittest.main()
