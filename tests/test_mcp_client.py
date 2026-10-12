"""Offline checks: python -m unittest discover -s tests -p test_mcp_client.py -v."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import httpx
from mcp.server import Server
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent, Tool
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ch06.mcp_client import MCPClient


class MCPClientTests(unittest.IsolatedAsyncioTestCase):
    async def run_query(self, requested_cities):
        server = Server("offline-weather")
        schema = {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "English city name"}},
            "required": ["city"],
        }
        tool = Tool(name="query_weather", description="Look up today's weather", inputSchema=schema)
        executed = []

        @server.list_tools()
        async def list_tools():
            return [tool]

        @server.call_tool()
        async def call_tool(name, arguments):
            executed.append((name, arguments))
            return [TextContent(type="text", text=f"{arguments['city']}: sunny")]

        calls = [
            {"id": f"call_{index}", "type": "function", "function": {
                "name": "query_weather", "arguments": json.dumps({"city": city}),
            }}
            for index, city in enumerate(requested_cities)
        ]
        requests = []

        def respond(request):
            requests.append(json.loads(request.content))
            needs_tools = bool(calls) and len(requests) == 1
            message = {"role": "assistant", "content": None if needs_tools else "Final answer"}
            if needs_tools:
                message["tool_calls"] = calls
            return httpx.Response(200, json={
                "id": f"completion_{len(requests)}", "object": "chat.completion",
                "created": 0, "model": "offline-model",
                "choices": [{"index": 0, "message": message,
                             "finish_reason": "tool_calls" if needs_tools else "stop"}],
            })

        with patch.dict(os.environ, {
            "API_KEY": "offline-test", "BASE_URL": "https://model.invalid/v1", "MODEL": "offline-model",
        }):
            client = MCPClient()
        client.client.close()
        with OpenAI(
            api_key="offline-test", base_url="https://model.invalid/v1", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as model:
            client.client = model
            async with create_connected_server_and_client_session(server) as session:
                client.session = session
                answer = await client.process_query("Compare the requested cities")
        self.assertEqual(answer, "Final answer")
        return requests, executed, tool

    async def test_mcp_input_schema_becomes_function_parameters(self):
        requests, executed, tool = await self.run_query([])
        function = requests[0]["tools"][0]["function"]
        self.assertIn("parameters", function)
        self.assertEqual(function["parameters"], tool.inputSchema)
        self.assertNotIn("input_schema", function)
        self.assertEqual(function["name"], tool.name)
        self.assertEqual(function["description"], tool.description)
        self.assertEqual(executed, [])

    async def test_every_parallel_tool_call_gets_its_matching_result(self):
        requests, executed, _ = await self.run_query(["Beijing", "Shanghai"])
        self.assertEqual(executed, [
            ("query_weather", {"city": "Beijing"}),
            ("query_weather", {"city": "Shanghai"}),
        ])
        self.assertEqual(len(requests), 2)
        messages = requests[1]["messages"]
        self.assertEqual([message["role"] for message in messages], ["user", "assistant", "tool", "tool"])
        self.assertEqual([call["id"] for call in messages[1]["tool_calls"]], ["call_0", "call_1"])
        self.assertEqual(
            [(message["tool_call_id"], message["content"]) for message in messages[2:]],
            [("call_0", "Beijing: sunny"), ("call_1", "Shanghai: sunny")],
        )

    async def test_single_tool_call_keeps_its_result_and_id(self):
        requests, executed, _ = await self.run_query(["Beijing"])
        self.assertEqual(executed, [("query_weather", {"city": "Beijing"})])
        self.assertEqual(len(requests), 2)
        messages = requests[1]["messages"]
        self.assertEqual([message["role"] for message in messages], ["user", "assistant", "tool"])
        self.assertEqual(messages[-1], {"role": "tool", "content": "Beijing: sunny", "tool_call_id": "call_0"})

    async def test_direct_answer_does_not_call_tools(self):
        requests, executed, _ = await self.run_query([])
        self.assertEqual(len(requests), 1)
        self.assertEqual(executed, [])


if __name__ == "__main__":
    unittest.main()
