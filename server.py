from fastmcp import FastMCP
import sys
# import arxiv
import os

from typing import List, Dict, Optional
from pathlib import Path
import requests



mcp = FastMCP(name="MCP-Server")

@mcp.tool
def add(a: int, b: int) -> int:
    """
    Add function 

    Args:
        a (int): integer
        b (int): integer

    Returns:
        int: addition of a and b
    """
    return a + b


@mcp.tool
def multiple(a: int, b: int) -> int:
    """multiply two numbers

    Args:
        a (int): number 
        b (int): integer

    Returns:
        int: multiple a and b, if it is valid integer.
    """
    try:
        c = a * b
        return c
    except Exception as ex:
        raise Exception("Error in multiplication")

@mcp.resource("api://total_profit")
def get_total_profit() -> dict:
    """Fetches total profit data from the REST API."""
    try:
        response = requests.get("http://127.0.0.1:8000/total_profit")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
    
  
    



# @mcp.tool
# def search_knowledge_base(
#     query: str, 
#     kb_path: str = "./knowledge_base", 
#     file_extensions: List[str] = [".txt", ".md", ".py", ".json"]
# ) -> Dict:
#     """
#     Search through a knowledge base of files for relevant content
    
#     Args:
#         query (str): Search query to find relevant content
#         kb_path (str): Path to the knowledge base directory (default: ./knowledge_base)
#         file_extensions (List[str]): File extensions to search through
        
#     Returns:
#         Dict: Dictionary containing search results with file paths and matching content
#     """
#     try:
#         if not os.path.exists(kb_path):
#             return {"error": f"Knowledge base path '{kb_path}' does not exist"}
        
#         results = {
#             "query": query,
#             "matches": [],
#             "total_files_searched": 0,
#             "files_with_matches": 0
#         }
        
#         query_lower = query.lower()
        
#         # Walk through all files in the knowledge base
#         for root, dirs, files in os.walk(kb_path):
#             for file in files:
#                 if any(file.endswith(ext) for ext in file_extensions):
#                     results["total_files_searched"] += 1
#                     file_path = os.path.join(root, file)
                    
#                     try:
#                         with open(file_path, 'r', encoding='utf-8') as f:
#                             content = f.read()
                            
#                         # Search for query in file content
#                         if query_lower in content.lower():
#                             results["files_with_matches"] += 1
                            
#                             # Find matching lines with context
#                             lines = content.split('\n')
#                             matching_lines = []
                            
#                             for i, line in enumerate(lines):
#                                 if query_lower in line.lower():
#                                     # Include some context (previous and next lines)
#                                     context_start = max(0, i - 1)
#                                     context_end = min(len(lines), i + 2)
#                                     context = lines[context_start:context_end]
                                    
#                                     matching_lines.append({
#                                         "line_number": i + 1,
#                                         "line": line.strip(),
#                                         "context": context
#                                     })
                            
#                             results["matches"].append({
#                                 "file_path": file_path,
#                                 "relative_path": os.path.relpath(file_path, kb_path),
#                                 "matching_lines": matching_lines[:5]  # Limit to first 5 matches per file
#                             })
                            
#                     except (UnicodeDecodeError, PermissionError) as e:
#                         # Skip files that can't be read
#                         continue
        
#         return results
        
#     except Exception as e:
#         return {"error": f"Error searching knowledge base: {str(e)}"}


# @mcp.tool  
# def get_file_content(file_path: str, kb_path: str = "./knowledge_base") -> Dict:
#     """
#     Retrieve the full content of a specific file from the knowledge base
    
#     Args:
#         file_path (str): Relative path to the file within the knowledge base
#         kb_path (str): Path to the knowledge base directory (default: ./knowledge_base)
        
#     Returns:
#         Dict: Dictionary containing file content and metadata
#     """
#     try:
#         full_path = os.path.join(kb_path, file_path)
        
#         if not os.path.exists(full_path):
#             return {"error": f"File '{file_path}' not found in knowledge base"}
            
#         if not os.path.isfile(full_path):
#             return {"error": f"'{file_path}' is not a file"}
            
#         # Check if file is within the knowledge base directory (security check)
#         if not os.path.abspath(full_path).startswith(os.path.abspath(kb_path)):
#             return {"error": "Access denied: file is outside knowledge base"}
            
#         try:
#             with open(full_path, 'r', encoding='utf-8') as f:
#                 content = f.read()
                
#             return {
#                 "file_path": file_path,
#                 "full_path": full_path,
#                 "content": content,
#                 "size_bytes": len(content.encode('utf-8')),
#                 "line_count": len(content.split('\n')),
#                 "file_extension": os.path.splitext(file_path)[1]
#             }
            
#         except UnicodeDecodeError:
#             return {"error": "Cannot read file: not a text file or encoding issue"}
            
#     except Exception as e:
#         return {"error": f"Error retrieving file content: {str(e)}"}


# @mcp.tool
# def list_knowledge_base_files(
#     kb_path: str = "./knowledge_base",
#     file_extensions: List[str] = [".txt", ".md", ".py", ".json"]
# ) -> Dict:
#     """
#     List all files in the knowledge base directory
    
#     Args:
#         kb_path (str): Path to the knowledge base directory (default: ./knowledge_base)
#         file_extensions (List[str]): File extensions to include in listing
        
#     Returns:
#         Dict: Dictionary containing list of files and directory structure
#     """
#     try:
#         if not os.path.exists(kb_path):
#             return {"error": f"Knowledge base path '{kb_path}' does not exist"}
            
#         files = []
#         total_size = 0
        
#         for root, dirs, filenames in os.walk(kb_path):
#             for filename in filenames:
#                 if any(filename.endswith(ext) for ext in file_extensions):
#                     file_path = os.path.join(root, filename)
#                     relative_path = os.path.relpath(file_path, kb_path)
#                     file_size = os.path.getsize(file_path)
#                     total_size += file_size
                    
#                     files.append({
#                         "name": filename,
#                         "relative_path": relative_path,
#                         "size_bytes": file_size,
#                         "extension": os.path.splitext(filename)[1],
#                         "directory": os.path.dirname(relative_path)
#                     })
        
#         return {
#             "knowledge_base_path": kb_path,
#             "total_files": len(files),
#             "total_size_bytes": total_size,
#             "file_extensions": file_extensions,
#             "files": sorted(files, key=lambda x: x["relative_path"])
#         }
        
#     except Exception as e:
#         return {"error": f"Error listing knowledge base files: {str(e)}"}


if __name__ == "__main__":
    mcp.run()