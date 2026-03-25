from pathlib import Path
from langchain_core.tools import tool
from typing import Annotated

@tool
def read_file(
    file_path: Annotated[str, "The absolute or relative path of the file to be read"]
) -> str:
    """
    Reads the content of a file from the specified path and returns it as a string.
    Use this tool when you need to inspect code, configuration, or logs.
    """
    # 1. Input Validation
    if not file_path:
        return "Error: file_path cannot be empty."

    path = Path(file_path).resolve()
    print(f"DEBUG: Attempting to read file at {path}")

    try:
        # 2. Check if file exists
        if not path.exists():
            return f"Error: The file at {file_path} does not exist."
        
        # 3. Check if it is a file (not a directory)
        if not path.is_file():
            return f"Error: The path {file_path} is a directory, not a file."

        # 4. Perform Read Operation
        # Using 'ignore' for errors to handle potential binary characters gracefully
        with open(path, mode='r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            print(f"DEBUG: Successfully read content from {path}")
            
        # Returning the content directly for the Agent to process
        return content

    except Exception as e:
        error_msg = f"Error: Failed to read file due to {str(e)}"
        print(f"DEBUG: ❌ {error_msg}")
        return error_msg
