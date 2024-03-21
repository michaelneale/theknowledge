import os
import sys

def get_ignored_patterns(project_dir):
    gitignore_path = os.path.join(project_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as file:
            return file.read().splitlines()
    return []

def should_ignore(file_path, ignored_patterns):
    for pattern in ignored_patterns:
        if pattern.startswith("/") and file_path.startswith(project_dir + pattern[1:]):
            return True
        elif file_path.endswith("/" + pattern):
            return True
        elif "/" + pattern + "/" in file_path:
            return True
    return False

def extract_source_code(project_dirs):
    file_tree = []
    file_contents = []

    for project_dir in project_dirs:
        ignored_patterns = get_ignored_patterns(project_dir)
        for root, dirs, files in os.walk(project_dir):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip the .git directory
            level = root.replace(project_dir, "").count(os.sep)
            indent = " " * 4 * level
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            for file in files:
                file_path = os.path.join(root, file)
                if not should_ignore(file_path, ignored_patterns):
                    file_tree.append(f"{indent} {file}")
                    try:
                        with open(file_path, "r") as f:
                            content = f.read()
                        file_contents.append(f"\n{'=' * 80}\nFile: {file_path}\n{'=' * 80}\n{content}\n")
                    except UnicodeDecodeError:
                        file_contents.append(f"\n{'=' * 80}\nFile: {file_path}\n{'=' * 80}\nUnable to decode file contents.\n")

    output = "File Tree:\n"
    output += "\n".join(file_tree)
    output += "\n\nFile Contents:\n"
    output += "".join(file_contents)
    return output

# Get the project directories from command line arguments
if len(sys.argv) < 2:
    print("Please provide one or more directory paths as command line arguments.")
    sys.exit(1)

project_dirs = sys.argv[1:]
for i, project_dir in enumerate(project_dirs):
    project_dirs[i] = os.path.abspath(project_dir)
    if not os.path.isdir(project_dirs[i]):
        print(f"The provided directory does not exist: {project_dirs[i]}")
        sys.exit(1)

# Extract the source code and file tree
output = extract_source_code(project_dirs)

# Set the default output file name
output_file = "knowledge.txt"

# Write the output to a file
with open(output_file, "w") as file:
    file.write(output)

print(f"Source code and file tree have been written to {output_file}.")