## Conan Cache Optimizer Utility Suite
This suite contains Python tools designed to manage your local Conan 2.14 cache [Conan Documentation](https://docs.conan.io/2/reference/commands/list.html). They help you identify and safely delete duplicate package versions or unneeded dependencies, preventing disk bloat while protecting the packages your active development work relies on [Conan Documentation](https://docs.conan.io/2/reference/commands/remove.html).
------------------------------
## Data Pipeline Architecture
Both analyzer scripts use a data pipeline that communicates directly with your deletion tool. Rather than deleting files immediately, they output a standardized intermediate JSON file: conan_cache_analysis.json.

[ analyze_dynamic_cache.py ] -----\
                                  +--> [ conan_cache_analysis.json ] --> [ delete_from_json.py ]
[ analyze_project_cache.py ] -----/

Because the output file uses a standard data format, you can safely review or manually edit the target list in Notepad before executing the final deletion command.
------------------------------
## Prerequisites & Installation
The script suite relies strictly on standard Python libraries (json, os, subprocess, re, argparse).

* No third-party packages are required (e.g., pip install packaging is not needed).
* Works across Windows, macOS, and Linux environments.
* Requires Conan 2.x configured and accessible in your system's PATH.

------------------------------
## Component Scripts## 1. System-Wide Version Analyzer (analyze_dynamic_cache.py)
This script dynamically scans your entire global local cache Conan Documentation. It groups packages by name, applies a natural numeric sort to handle complex string version keys (such as development branches or custom server variants like @zixel), identifies the single highest version to keep, and flags all historical versions for cleanup.
## 2. Project Dependency Analyzer (analyze_project_cache.py)
This script isolates the exact dependencies of a specific software project Conan Documentation. It runs Conan's internal graph evaluation to discover both direct dependencies and background transitive requirements mapped inside a target conanfile.py. Everything matching the project's dependency structure is marked to keep; all other packages in the global cache are flagged to delete.
## 3. JSON Purge Orchestrator (delete_from_json.py)
This script functions as the execution tool. It reads the shared conan_cache_analysis.json file, parses the list under delete_list_older_versions, displays a preview, and triggers automated, individual package purges via Conan Conan Documentation.
------------------------------
## Step-by-Step Execution Workflows## Workflow A: Global Cache Cleanup (Keep Latest Versions System-Wide)
Use this workflow to optimize disk space by dropping old package iterations while maintaining the newest version of everything.

   1. Open your terminal and navigate to the directory where your utility scripts are saved.
   2. Generate the cache report:
   
   python analyze_dynamic_cache.py
   
   3. A text editor will open displaying conan_cache_analysis.json. Verify the targets under "delete_list_older_versions".
   4. Run the cleanup script to remove the older versions:
   
   python delete_from_json.py
   
   
## Workflow B: Dedicated Project Isolation (Delete Everything Unrelated)
Use this workflow when working on a specific project and you want to purge all other cached packages on your system.

   1. Open your terminal and ensure you are in the folder containing your cleanup tools.
   2. Analyze your project's dependencies by passing the path to the directory containing your conanfile.py:
   
   # Target a project folder in another directory
   python analyze_project_cache.py --path /path/to/my/cpp_project
   # Alternative: If running directly inside the project directory
   python analyze_project_cache.py --path .
   
   3. Review the generated conan_cache_analysis.json file to confirm that only your current project's dependencies are preserved.
   4. Execute the deletion sequence:
   
   python delete_from_json.py
   
   
------------------------------
## Manual Safeguards
If you want to protect a specific package version from being deleted during a cleanup loop, open the generated conan_cache_analysis.json file before running the final script. Manually delete the corresponding line from the "delete_list_older_versions" array and save the file. The orchestrator script will only delete the packages that remain listed in that array.
If you would like to generate this directly as a markdown file, let me know if you need to add custom command-line arguments to the deletion script as well!

