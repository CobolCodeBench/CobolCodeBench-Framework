import os
import json
import pandas as pd

def read_file(file_path: str) -> str:
    """Read the contents of a file and return it as a string."""
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path: str, content: str) -> None:
    """Write the given content to a file."""
    with open(file_path, 'w') as file:
        file.write(content)

def append_to_file(file_path: str, content: str) -> None:
    """Append the given content to a file."""
    with open(file_path, 'a') as file:
        file.write(content)

def file_exists(file_path: str) -> bool:
    """Check if a file exists at the given path."""
    return os.path.isfile(file_path)

def delete_file(file_path: str) -> None:
    """Delete the file at the given path if it exists."""
    if file_exists(file_path):
        os.remove(file_path)

def json_to_csv(json_file_path, csv_file_path):
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = [json.loads(line) for line in file]
        # Convert JSON data to DataFrame
        df = pd.DataFrame(data)

        # Save DataFrame to CSV
        df.to_csv(csv_file_path, index=False)
        print(f"JSON data successfully converted to CSV and saved to: {csv_file_path}")
        return csv_file_path
    except Exception as e:
        print(f"Error converting JSON to CSV: {str(e)}")
        return None