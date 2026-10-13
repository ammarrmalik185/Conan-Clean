import argparse
import json
import os
import platform
import re
import subprocess

def analyze_project_cache():
    parser = argparse.ArgumentParser(description="Analyze Conan cache based on a project conanfile.py.")
    parser.add_argument(
        "-p", "--path", 
        type=str, 
        default=".", 
        help="Path to the directory containing conanfile.py (default: current directory)"
    )
    args = parser.parse_args()

    target_dir = os.path.abspath(args.path)
    conanfile = os.path.join(target_dir, "conanfile.py")
    
    if not os.path.exists(conanfile):
        print(f"Error: 'conanfile.py' not found at target path: {target_dir}")
        return

    print(f"Analyzing project dependencies from: {conanfile}...")

    # 1. First Pass: Attempt dynamic graph evaluation via Conan CLI
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
            print("Warning: Failed to parse graph JSON. Forcing static parsing aggregation.")

    # 2. Safety Layer: Always run robust regex aggregation to preserve ALL packages listed across all if/else blocks
    print("Running comprehensive conditional check on conanfile.py contents...")
    try:
        with open(conanfile, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skips commented-out blocks cleanly
                if line.startswith("#"):
                    continue
                
                # Matches patterns like self.requires("pkg/ver") or self.requires('pkg/ver', override=True)
                match = re.search(r'self\.requires\s*\(\s*["\']([^"\']+)["\']', line)
                if match:
                    extracted_reference = match.group(1).strip()
                    project_required_packages.add(extracted_reference)
    except Exception as e:
        print(f"Static file parsing warning: {e}")

    if not project_required_packages:
        print("Error: Could not identify any project requirements inside conanfile.py.")
        return

    print(f"Aggregated {len(project_required_packages)} total packages to safeguard across all logical environments.")

    # 3. Scan the Local System Cache
    print("Scanning system local cache...")
    list_cmd = ["conan", "list", "*/*", "--format=json"]
    list_result = subprocess.run(list_cmd, capture_output=True, text=True, encoding="utf-8")
    
    if list_result.returncode != 0:
        print(f"Error scanning local cache: {list_result.stderr}")
        return

    try:
        cache_data = json.loads(list_result.stdout)
    except json.JSONDecodeError:
        print("Failed to read system local cache JSON structure.")
        return

    local_cache = cache_data.get("Local Cache", {})
    
    to_keep = []
    to_delete = []

    # 4. Compare system cache versions against aggregated rules
    for key in local_cache.keys():
        if "/" in key:
            # Safe protection: if the package string matches any declaration in conanfile, protect it
            if key in project_required_packages:
                to_keep.append(key)
            else:
                to_delete.append(key)

    # 5. Build standard structured output layout
    output_data = {
        "summary": {
            "total_packages_scanned": len(local_cache),
            "count_to_keep": len(to_keep),
            "count_to_delete": len(to_delete)
        },
        "keep_list_latest_versions": sorted(to_keep),
        "delete_list_older_versions": sorted(to_delete)
    }

    output_file = "conan_cache_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\nAnalysis complete. Targets written to output pipeline file: {output_file}")

    # 6. Automatic File Launcher Check
    if platform.system() == "Windows":
        os.system(f"notepad.exe {output_file}")
    elif platform.system() == "Darwin":
        os.system(f"open -t {output_file}")
    else:
        os.system(f"xdg-open {output_file}")

if __name__ == "__main__":
    analyze_project_cache()