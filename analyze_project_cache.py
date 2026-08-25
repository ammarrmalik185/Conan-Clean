import argparse
import json
import os
import platform
import re
import subprocess

def analyze_project_cache():
    # 1. Setup argument parsing for flexible paths
    parser = argparse.ArgumentParser(description="Analyze Conan cache based on a project conanfile.py.")
    parser.add_argument(
        "-p", "--path", 
        type=str, 
        default=".", 
        help="Path to the directory containing conanfile.py (default: current directory)"
    )
    args = parser.parse_args()

    # Normalize the target project path
    target_dir = os.path.abspath(args.path)
    conanfile = os.path.join(target_dir, "conanfile.py")
    
    # 2. Verify conanfile.py exists at the specified path
    if not os.path.exists(conanfile):
        print(f"Error: 'conanfile.py' not found at target path: {target_dir}")
        return

    print(f"Analyzing project dependencies from: {conanfile}...")

    # 3. Resolve required dependencies via Conan CLI (pointing to target directory)
    graph_cmd = ["conan", "graph", "info", target_dir, "--format=json"]
    graph_result = subprocess.run(graph_cmd, capture_output=True, text=True, encoding="utf-8")
    
    project_required_packages = set()

    if graph_result.returncode == 0:
        try:
            graph_data = json.loads(graph_result.stdout)
            nodes = graph_data.get("nodes", {})
            for node_id, node_info in nodes.items():
                ref = node_info.get("ref")
                if ref and ref != "conanfile.py":
                    project_required_packages.add(ref)
        except json.JSONDecodeError:
            print("Warning: Failed to parse graph JSON. Falling back to regex.")

    # Static fallback logic if graph command fails (running parsing directly on target path)
    if not project_required_packages:
        print("Falling back to static regex parsing of conanfile.py...")
        try:
            with open(conanfile, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = r'self\.requires\s*\(\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content)
            for match in matches:
                project_required_packages.add(match)
        except Exception as e:
            print(f"Static parse error: {e}")

    if not project_required_packages:
        print("Error: Could not identify any project requirements inside conanfile.py.")
        return

    # 4. Pull the entire local cache state dynamically
    print("Scanning system local cache...")
    list_cmd = ["conan", "list", "*/*", "--format=json"]
    list_result = subprocess.run(list_cmd, capture_output=True, text=True, encoding="utf-8")
    
    if list_result.returncode != 0:
        print(f"Error scanning local cache: {list_result.stderr}")
        return

    try:
        cache_data = json.loads(list_result.stdout)
    except json.JSONDecodeError:
        print("Failed to read system local cache JSON.")
        return

    local_cache = cache_data.get("Local Cache", {})
    
    to_keep = []
    to_delete = []

    # 5. Filter global cache keys against project requirements
    for key in local_cache.keys():
        if "/" in key:
            if key in project_required_packages:
                to_keep.append(key)
            else:
                to_delete.append(key)

    # 6. Format layout explicitly matching your standard format
    output_data = {
        "summary": {
            "total_packages_scanned": len(local_cache),
            "count_to_keep": len(to_keep),
            "count_to_delete": len(to_delete)
        },
        "keep_list_latest_versions": sorted(to_keep),
        "delete_list_older_versions": sorted(to_delete)
    }

    # Saves to the same file in your current execution directory
    output_file = "conan_cache_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\nAnalysis complete. Targets saved to current directory as: {output_file}")

    # 7. Open the output file automatically
    if platform.system() == "Windows":
        os.system(f"notepad.exe {output_file}")
    elif platform.system() == "Darwin":
        os.system(f"open -t {output_file}")
    else:
        os.system(f"xdg-open {output_file}")

if __name__ == "__main__":
    analyze_project_cache()