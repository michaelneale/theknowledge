import os
import sys
import heapq

def get_ignored_patterns(project_dir, excluded_paths):
    gitignore_path = os.path.join(project_dir, ".gitignore")
    ignored_patterns = excluded_paths.copy()
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as file:
            ignored_patterns.extend(file.read().splitlines())
    return ignored_patterns

def should_ignore(file_path, ignored_patterns, project_dir):
    for pattern in ignored_patterns:
        if pattern.startswith("/") and file_path.startswith(project_dir + pattern[1:]):
            return True
        elif file_path.endswith("/" + pattern):
            return True
        elif "/" + pattern + "/" in file_path:
            return True
    return False

def get_directory_size_in_kb(directory):
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    return round(total_size / 1024, 2)

def get_file_count(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def get_largest_files(directory, num_files=5):
    largest_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if len(largest_files) < num_files:
                heapq.heappush(largest_files, (file_size, file))
            else:
                heapq.heappushpop(largest_files, (file_size, file))
    return [file for _, file in largest_files]

def prompt_user_for_exclusion(directory, project_dir, file_count_threshold=10, size_threshold=20):
    if directory == project_dir:
        return False, []  # Skip exclusion prompt for the root directory

    file_count = get_file_count(directory)
    directory_size_kb = get_directory_size_in_kb(directory)

    if file_count > file_count_threshold or directory_size_kb > size_threshold:
        print(f"\nDirectory: {directory}")
        print(f"File Count: {file_count}")
        print(f"Total Size: {directory_size_kb} KB")

        largest_files = get_largest_files(directory)
        print("Largest Files:", ", ".join(largest_files))

        while True:
            choice = input("Do you want to (E)xclude, (I)nclude, or (O)nly include specific file extensions? ").lower()
            if choice == 'e':
                return True, []
            elif choice == 'i':
                return False, []
            elif choice == 'o':
                extensions = input("Enter the file extensions to include (comma-separated): ").split(',')
                extensions = [ext.strip() for ext in extensions]
                return False, extensions
            else:
                print("Invalid choice. Please enter 'E', 'I', or 'O'.")

    return False, []

def extract_source_code(project_dirs, excluded_paths):
    file_tree = []
    file_contents = []
    for project_dir in project_dirs:
        ignored_patterns = get_ignored_patterns(project_dir, excluded_paths)
        for root, dirs, files in os.walk(project_dir):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip the .git directory
            exclude, extensions = prompt_user_for_exclusion(root, project_dir)
            if exclude:
                ignored_patterns.append(os.path.relpath(root, project_dir))
                dirs[:] = []  # Skip subdirectories of the excluded directory
                continue
            level = root.replace(project_dir, "").count(os.sep)
            indent = " " * 4 * level
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            for file in files:
                file_path = os.path.join(root, file)
                if not should_ignore(file_path, ignored_patterns, project_dir):
                    if extensions and not any(file.endswith(ext) for ext in extensions):
                        continue  # Skip files that don't match the specified extensions
                    file_tree.append(f"{indent}    {file}")
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
excluded_paths = []
output = extract_source_code(project_dirs, excluded_paths)

# Set the default output file name
output_file = "knowledge.txt"

# Write the output to a file
with open(output_file, "w") as file:
    file.write(output)

print(f"Source code and file tree have been written to {output_file}.")