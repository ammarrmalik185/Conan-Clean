import json
import os
import subprocess

def delete_packages_from_json():
    json_filename = "conan_cache_analysis.json"
    
    # 1. Verify that the JSON file exists
    if not os.path.exists(json_filename):
        print(f"Error: Target file '{json_filename}' not found.")
        print("Please run your analysis script first to generate it.")
        return

    # 2. Parse the JSON file
    try:
        with open(json_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: '{json_filename}' is corrupted or not valid JSON.")
        return

    # 3. Extract the targets scheduled for deletion
    to_delete = data.get("delete_list_older_versions", [])
    
    if not to_delete:
        print(f"No packages found in 'delete_list_older_versions' inside {json_filename}.")
        print("There is nothing to delete.")
        return

    print(f"Found {len(to_delete)} packages queued for deletion inside '{json_filename}'.")
    
    # 4. Confirmation Prompt
    print("\nPreview of packages to be removed:")
    for sample in to_delete[:5]:
        print(f"  - {sample}")
    if len(to_delete) > 5:
        print(f"  ... and {len(to_delete) - 5} more items.")

    confirm = input(f"\nAre you sure you want to permanently delete these {len(to_delete)} packages? (y/N): ")
    if confirm.lower() != 'y':
        print("Operation canceled. No packages were deleted.")
        return

    # 5. Execute bulk deletion via Conan CLI
    print("\nStarting cache cleanup...")
    success_count = 0
    fail_count = 0

    for pkg_ref in to_delete:
        print(f"Removing: {pkg_ref} ... ", end="", flush=True)
        # Use '-c' to skip Conan's individual confirmation prompts
        cmd = ["conan", "remove", pkg_ref, "-c"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        
        if result.returncode == 0:
            print("SUCCESS")
            success_count += 1
        else:
            print("FAILED")
            print(f"  Reason: {result.stderr.strip()}")
            fail_count += 1

    print(f"\n--- CLEANUP COMPLETE ---")
    print(f"Successfully deleted: {success_count} packages.")
    if fail_count > 0:
        print(f"Failed to delete: {fail_count} packages (check logs above).")

if __name__ == "__main__":
    delete_packages_from_json()