from fastmcp import Client
from typing import List, Dict
import asyncio
from dotenv import load_dotenv
import os
import nest_asyncio
from termcolor import colored
from langchain_google_genai import ChatGoogleGenerativeAI

nest_asyncio.apply()
load_dotenv()

class MCP_ChatBot:
    
    def __init__(self, mcp_server_url: str):
        self.mcp_server = mcp_server_url
        self.client: Client = None
        self.gemini_client = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            max_tokens=2048,
        )
        self.available_tools: List[dict] = []
        self.resource_cache: Dict[str, str] = {}  # Cache resource data

    async def load_all_resources(self):
        """Fetch all resources on startup and cache them."""
        try:
            resources_response = await self.client.list_resources()
            
            for resource in resources_response:
                # Convert uri to string
                uri_str = str(resource.uri)
                print(f"Loading resource: {uri_str}")
                try:
                    result = await self.client.read_resource(uri=uri_str)
                    
                    # Extract content
                    if hasattr(result, 'contents') and result.contents:
                        content = result.contents[0]
                        if hasattr(content, 'text'):
                            self.resource_cache[uri_str] = content.text
                        elif hasattr(content, 'blob'):
                            self.resource_cache[uri_str] = str(content.blob)
                    else:
                        self.resource_cache[uri_str] = str(result)
                    
                    print(f"✓ Loaded: {uri_str}")
                except Exception as e:
                    print(f"✗ Error loading {uri_str}: {e}")
            
            print(f"\nCached {len(self.resource_cache)} resources")
        except Exception as e:
            print(f"Error loading resources: {e}")

    def get_resource_context(self) -> str:
        """Build context from all cached resources."""
        if not self.resource_cache:
            return ""
        
        context_parts = ["Available Data Sources:"]
        for uri, content in self.resource_cache.items():
            # Convert uri to string if it's not already
            uri_str = str(uri)
            resource_name = uri_str.split("://")[-1]
            context_parts.append(f"\n[{resource_name}]:\n{content}")
        print("----"*10)
        print(colored(f"The get_resource_context function \n : value - {context_parts}","red"))
        # print("\n".join(context_parts))
        print("----"*10)
        
        return "\n".join(context_parts)

    async def process_query(self, query):
        # Add resource context to every query
        resource_context = self.get_resource_context()
        
        if resource_context:
            enhanced_query = f"{query}\n\n{resource_context}"
        else:
            enhanced_query = query
            
        message = [
            {
                'role': 'user',
                'content': enhanced_query
            }
        ]
        
        # Convert tools to gemini-compatible format
        gemini_tools = []
        for tool in self.available_tools:
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
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    message.append({
                        'role': 'assistant',
                        'content': response.content,
                        'tool_calls': response.tool_calls
                    })
                    
                    for tool_call in response.tool_calls:
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
                            continue
                
                        if isinstance(tool_args, str):
                            import json
                            try:
                                tool_args = json.loads(tool_args)
                            except:
                                pass
                        
                        try:
                            result = await self.client.call_tool(
                                name=tool_name,
                                arguments=tool_args
                            )
                            
                            message.append({
                                "role": "tool",
                                "content": str(result.content),
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
        print("\n" + "="*50)
        print("MCP ChatBot Started")
        print("="*50)
        print("Available Tools:", [tool["name"] for tool in self.available_tools])
        print("Cached Resources:", list(self.resource_cache.keys()))
        print("\nType your queries or 'quit'/'exit' to stop")
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
            await self.client.__aenter__()
            
            # Fetch tools
            tools_response = await self.client.list_tools()
            print(f"Connected to MCP Server: {self.mcp_server}")
            
            self.available_tools = []
            for tool in tools_response:
                self.available_tools.append({
                    "name": tool.name,
                    "description": getattr(tool, "description", ''),
                    "input_schema": getattr(tool, 'inputSchema', {})
                })
            
            # AUTO-LOAD ALL RESOURCES
            await self.load_all_resources()
            
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