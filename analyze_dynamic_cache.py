import json
import os
import platform
import re
import subprocess

def analyze_dynamic_cache():
    print("Executing dynamic scan of Conan 2.14 cache...")
    
    # 1. Dynamically pull JSON cache from the Conan CLI
    cmd = ["conan", "list", "*/*", "--format=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    
    if result.returncode != 0:
        print(f"Error executing conan: {result.stderr}")
        return

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Failed to parse Conan JSON output. Make sure you are using Conan 2.x.")
        return

    local_cache = data.get("Local Cache", {})
    if not local_cache:
        print("No packages found in your Conan local cache.")
        return

    from collections import defaultdict
    packages = defaultdict(list)
    
    # 2. Extract full references regardless of how Conan keys them
    for key in local_cache.keys():
        # Conan 2.x keys can be full references (e.g., "zcm/0.3.22-master.2@zixel")
        if "/" in key:
            pkg_name = key.split('/')[0]
            packages[pkg_name].append(key)

    to_keep = []
    to_delete = []

    # 3. Dynamic Natural/Semantic Sorting Parser (No third-party packages required)
    def natural_sort_key(ref):
        # Isolate the version segment (between '/' and Optional '@')
        ver_part = ref.split('/')[1].split('@')[0]
        # Tokenize strings and integers so "0.14.10" sorts higher than "0.14.2"
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', ver_part)]

    # 4. Group targets
    for name, refs in packages.items():
        if len(refs) == 1:
            to_keep.append(refs[0])
            continue
            
        # Dynamically sort references based on their version segment
        sorted_refs = sorted(refs, key=natural_sort_key)
        
        latest = sorted_refs[-1]
        older = sorted_refs[:-1]
        
        to_keep.append(latest)
        to_delete.extend(older)

    # 5. Format output JSON
    output_data = {
        "summary": {
            "total_unique_packages": len(packages),
            "count_to_keep": len(to_keep),
            "count_to_delete": len(to_delete)
        },
        "keep_list_latest_versions": sorted(to_keep),
        "delete_list_older_versions": sorted(to_delete)
    }

    output_file = "conan_cache_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\nAnalysis complete. Targets saved to: {output_file}")

    # 6. Pop open in system editor
    if platform.system() == "Windows":
        os.system(f"notepad.exe {output_file}")
    elif platform.system() == "Darwin":
        os.system(f"open -t {output_file}")
    else:
        os.system(f"xdg-open {output_file}")

if __name__ == "__main__":
    analyze_dynamic_cache()