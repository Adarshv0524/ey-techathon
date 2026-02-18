import os
import fnmatch

def load_gitignore_patterns(target_dir):
    """
    Reads the .gitignore file in the target directory and returns a list of patterns.
    """
    gitignore_path = os.path.join(target_dir, ".gitignore")
    patterns = []
    
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .gitignore: {e}")
            
    return patterns

def should_ignore(name, root_path, base_dir, patterns):
    """
    Determines if a file or folder should be ignored based on:
    1. Hardcoded system ignores (.venv, .git, etc.)
    2. .gitignore patterns
    """
    # 1. HARDCODED IGNORES (Strictly enforced)
    system_ignores = {'.venv', 'venv', 'env', '.git', '__pycache__', '.idea', '.vscode'}
    if name in system_ignores:
        return True

    # 2. GITIGNORE PATTERNS
    # We check against the name (e.g., "secret.py") and the relative path (e.g., "utils/secret.py")
    full_path = os.path.join(root_path, name)
    relative_path = os.path.relpath(full_path, base_dir)
    
    # Normalize path separators for Windows compatibility
    relative_path = relative_path.replace(os.sep, "/")

    for pattern in patterns:
        # Handle directory-specific patterns (ending in /)
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            
        # fnmatch allows wildcards (*.pyc, node_modules, etc.)
        # Check if the name matches (e.g., *.log) OR if the full relative path matches (e.g., src/temp/*)
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative_path, pattern):
            return True
            
    return False

def create_code_context(target_directory):
    output_filename = "code_context.txt"
    output_path = os.path.join(target_directory, output_filename)
    separator = "======================================================="
    
    # Load gitignore patterns once
    ignore_patterns = load_gitignore_patterns(target_directory)
    
    print(f"Scanning: {target_directory}")
    print(f"Ignoring system folders (.venv, .git) and {len(ignore_patterns)} .gitignore patterns.")

    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            
            # Walk the directory tree
            for root, dirs, files in os.walk(target_directory):
                
                # --- MODIFY DIRS IN-PLACE TO PREVENT RECURSION INTO IGNORED FOLDERS ---
                # This is crucial so we don't even look inside .venv or .git
                dirs[:] = [d for d in dirs if not should_ignore(d, root, target_directory, ignore_patterns)]
                
                for filename in files:
                    # check if the file itself should be ignored
                    if should_ignore(filename, root, target_directory, ignore_patterns):
                        continue
                    
                    # Only process .py files (and avoid reading the file we are currently writing)
                    if filename.endswith(".py") and filename != output_filename:
                        full_path = os.path.join(root, filename)
                        
                        try:
                            with open(full_path, "r", encoding="utf-8") as infile:
                                content = infile.read()
                            
                            # Write relative path for cleaner reading
                            display_path = os.path.relpath(full_path, target_directory)
                            
                            outfile.write(f"{separator}\n")
                            outfile.write(f"{display_path}\n")
                            outfile.write(f"{content}\n\n")
                            
                            print(f"Added: {display_path}")
                            
                        except Exception as e:
                            print(f"Error reading {full_path}: {e}")
                            
        print(f"\n[Success] Context file created at: {output_path}")

    except Exception as e:
        print(f"Critical Error: {e}")

# --- Execution ---
if __name__ == "__main__":
    target_dir = input("Enter the relative directory path (e.g., ./backend): ").strip()
    
    if os.path.isdir(target_dir):
        create_code_context(target_dir)
    else:
        print("Error: Directory not found.")