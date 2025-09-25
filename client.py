from fastmcp import Client
from typing import List
import asyncio
from dotenv import load_dotenv
import httpx
import os
import nest_asyncio
from langchain_google_genai import ChatGoogleGenerativeAI

nest_asyncio.apply()
load_dotenv()

class MCP_ChatBot:
    
    def __init__(self, mcp_server_url: str):
        self.mcp_server = mcp_server_url
        self.client: Client = None
        self.client_context = None
        self.gemini_client = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            max_tokens=2048,
        )
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        message = [
            {
                'role': 'user',
                'content': query
            }
        ]
        
        # Convert tools to gemini-compatible format
        gemini_tools = []
        
        for tool in self.available_tools:
            # Gemini expects tools in a specific format
            gemini_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
            gemini_tools.append(gemini_tool)
        
        try:
            if gemini_tools:
                response = await self.gemini_client.ainvoke(message, tools=gemini_tools)
            else:
                response = await self.gemini_client.ainvoke(message)
            
            process_query = True
            while process_query:
                
                if response.content:
                    print(response.content)
                
                # Handle tool calls (Gemini Format)
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(f"Debug: Found {len(response.tool_calls)} tool calls")
                    
                    message.append({
                        'role': 'assistant',
                        'content': response.content,
                        'tool_calls': response.tool_calls
                    })
                    
                    for i, tool_call in enumerate(response.tool_calls):
                        print(f"Debug: Tool call {i}: {type(tool_call)} - {tool_call}")
                        
                        # Handle different tool_call formats
                        if hasattr(tool_call, 'name'):
                            tool_name = tool_call.name
                            tool_args = tool_call.args
                            tool_id = getattr(tool_call, 'id', f"call_{tool_call.name}")
                        elif isinstance(tool_call, dict):
                            if 'function' in tool_call:
                                tool_name = tool_call['function']['name']
                                tool_args = tool_call['function']['arguments']
                                tool_id = tool_call.get('id', f"call_{tool_name}")
                            else:
                                tool_name = tool_call.get('name', 'unknown')
                                tool_args = tool_call.get('args', {})
                                tool_id = tool_call.get('id', f"call_{tool_name}")
                        else:
                            print(f"Unexpected tool_call format: {type(tool_call)}")
                            continue
                
                        print(f"Debug: Calling tool '{tool_name}' with args: {tool_args}")
                
                        if isinstance(tool_args, str):
                            import json
                            try:
                                tool_args = json.loads(tool_args)
                            except:
                                pass
                        
                        try:
                            # Fixed: Use call_tool instead of ainvoke
                            result = await self.client.call_tool(
                                name=tool_name,
                                arguments=tool_args
                            )
                            
                            message.append({
                                "role": "tool",
                                "content": str(result.content),  # Fixed: access result.content
                                "tool_call_id": tool_id
                            })
                            
                            if gemini_tools:
                                response = await self.gemini_client.ainvoke(message, tools=gemini_tools)
                            else:
                                response = await self.gemini_client.ainvoke(message)
                            
                            if response.content and not (hasattr(response, 'tool_calls') and response.tool_calls):
                                print(response.content)
                                process_query = False
                            
                        except Exception as e:
                            print(f"Error calling the tool {tool_name}: {e}")
                            message.append({
                                "role": "tool",
                                "content": f"Error: {e}",
                                "tool_call_id": tool_id
                            })
                            process_query = False
                else:
                    process_query = False
                    
        except Exception as e:
            print(f"Error processing query: {e}")
    
    async def chat_loop(self):
        print("MCP ChatBot started")
        print("Type your queries or 'quit'/'exit' to stop")
        print("Available Tools:", [tool["name"] for tool in self.available_tools])
        print("-" * 50)
        
        while True:
            try:
                query = input("\nYou: ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                if not query:
                    continue
                
                print("Bot:", end=" ")
                await self.process_query(query)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
    
    async def initialize_connect(self):
        try:
            self.client = Client(self.mcp_server)
            
            # Use the client as an async context manager
            await self.client.__aenter__()
            
            tools_response = await self.client.list_tools()
            
            print(f"Connected to the mcp_server {self.mcp_server}")
            
            print("Available Tools:", [tool.name for tool in tools_response])
            
            self.available_tools = []
            for tool in tools_response:
                self.available_tools.append({
                    "name": tool.name,
                    "description": getattr(tool, "description", ''),
                    "input_schema": getattr(tool, 'inputSchema', {})
                })
            
            return True
        except Exception as e:
            print(f"Error connecting to mcp server: {e}")
            return False
    
    async def close_connection(self):
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                print("Connection closed")
            except Exception as e:
                print(f"Error closing connection: {e}")
            finally:
                self.client = None
    
    async def connect_to_server_and_run(self):
        success = await self.initialize_connect()
        if success:
            try:
                await self.chat_loop()
            finally:
                await self.close_connection()
        return success


async def main():
    mcp_server_url = "http://localhost:8080/mcp"
    chatbot = MCP_ChatBot(mcp_server_url=mcp_server_url)
    await chatbot.connect_to_server_and_run()

if __name__ == "__main__":
    asyncio.run(main())