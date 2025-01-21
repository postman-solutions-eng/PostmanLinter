import os
import argparse
import json
import requests
import subprocess
import sys
from collections import defaultdict
import platform

def fetch_json_from_postman(api_key, uid, resource_type):
    headers = {'x-api-key': api_key}
    if resource_type == "collection":
        url = f"https://api.postman.com/collections/{uid}"
    elif resource_type == "workspace":
        url = f"https://api.postman.com/workspaces/{uid}"
    else:
        raise ValueError("Invalid resource type specified.")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_spectral_command():
    system = platform.system()
    if system == "Windows":
        spectral_cmd = "spectral.cmd"
    else:
        spectral_cmd = "spectral"
    
    # Verify that Spectral is available in PATH
    from shutil import which
    if which(spectral_cmd) is None:
        print(f"Spectral CLI not found. Please ensure 'spectral' is installed and added to your PATH.")
        sys.exit(1)
    
    return spectral_cmd

def lint_json(spectral_cmd, file_path, ruleset_path):
    try:
        result = subprocess.run(
            [spectral_cmd, "lint", file_path, "--ruleset", ruleset_path, "-f", "json", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode != 0 and result.stdout:
            return json.loads(result.stdout)
        elif result.returncode != 0:
            print(f"Spectral linting failed with error: {result.stderr}")
            sys.exit(1)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Spectral linting failed with error: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Spectral output. Please check the output manually.")
        sys.exit(1)

def process_results(source_json, results):
    # Group errors by their message
    grouped_errors = defaultdict(list)
    for error in results:
        if error.get("severity", 0) >= 0:
            grouped_errors[error["message"]].append(error)

    # Format and print the results
    for message, errors in grouped_errors.items():
        print(f"\n{len(errors)} occurrences of: {message}")
        for error in errors:
            path = error["path"]
            try:
                # Traverse the JSON structure to find the parent object
                parent = source_json
                for key in path[:-1]:
                    if isinstance(parent, list):
                        key = int(key)
                    parent = parent[key]

                # Check if the final parent is a list or a dictionary
                if isinstance(parent, dict):
                    name = parent.get("name", None)
                else:
                    name = None

                if name:
                    print(f"Name: {name}")
                else:
                    print(f"Path: {'.'.join(path)}")
            except (KeyError, IndexError, TypeError) as e:
                print(f"Path: {'.'.join(path)}")
                print(f"Error accessing path: {e}")

def main():
    parser = argparse.ArgumentParser(description="Lint a Postman collection or workspace using Spectral rules.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--collection", help="Collection ID")
    group.add_argument("-w", "--workspace", help="Workspace ID")
    parser.add_argument("-r", "--ruleset", help="Path to custom Spectral ruleset file")
    parser.add_argument("-k", "--api-key", help="Postman API Key")

    args = parser.parse_args()

    api_key = args.api_key if args.api_key else os.getenv('POSTMAN_API_KEY')
    if not api_key:
        print("POSTMAN_API_KEY environment variable is not set and no API key was provided via -k.")
        sys.exit(1)

    resource_type = "collection" if args.collection else "workspace"
    uid = args.collection if args.collection else args.workspace

    source_json_file = f"_{resource_type}.json"

    # Determine ruleset path
    if args.ruleset:
        ruleset_path = args.ruleset
        if not os.path.isfile(ruleset_path):
            print(f"Custom ruleset file '{ruleset_path}' does not exist.")
            sys.exit(1)
    else:
        ruleset_path = "rulesets/rules.yaml" if resource_type == "collection" else "rulesets/workspacerules.yaml"
        if not os.path.isfile(ruleset_path):
            print(f"Default ruleset file '{ruleset_path}' not found. Please provide a custom ruleset using -r.")
            sys.exit(1)

    # Fetch JSON data from Postman API
    print("Fetching JSON data from Postman API...")
    try:
        source_json = fetch_json_from_postman(api_key, uid, resource_type)
    except requests.HTTPError as e:
        print(f"Failed to fetch data from Postman API: {e}")
        sys.exit(1)

    # Save the source JSON to a file
    try:
        with open(source_json_file, "w") as f:
            json.dump(source_json, f, indent=4)
    except IOError as e:
        print(f"Failed to write JSON data to file '{source_json_file}': {e}")
        sys.exit(1)

    # Get the appropriate Spectral command based on OS
    spectral_cmd = get_spectral_command()

    # Lint the JSON file using Spectral
    print("Linting JSON data...")
    results = lint_json(spectral_cmd, source_json_file, ruleset_path)

    # Process the results and print the output
    print("Processing linting results...")
    process_results(source_json, results)

if __name__ == "__main__":
    main()
