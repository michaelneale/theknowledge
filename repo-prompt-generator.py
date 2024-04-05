import os
import sys
import heapq
import fnmatch

def get_ignored_patterns(project_dir, excluded_paths):
    gitignore_path = os.path.join(project_dir, ".gitignore")
    ignored_patterns = excluded_paths.copy()
    # Always ignore node_modules
    ignored_patterns.append('node_modules')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as file:
            ignored_patterns.extend(file.read().splitlines())
    return ignored_patterns

def should_ignore(path, ignored_patterns, project_dir):
    relative_path = os.path.relpath(path, project_dir)
    for pattern in ignored_patterns:
        if fnmatch.fnmatch(relative_path, pattern) or 'node_modules' in path.split(os.sep):
            return True
    return False

def get_directory_size_in_kb(directory, ignored_patterns, project_dir, specified_extensions):
    total_size = 0
    for root, dirs, files in os.walk(directory):
        # Explicitly remove node_modules from dirs to not walk into it
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        for file in files:
            file_path = os.path.join(root, file)
            if not should_ignore(file_path, ignored_patterns, project_dir):
                _, extension = os.path.splitext(file)
                if not specified_extensions or extension in specified_extensions:
                    total_size += os.path.getsize(file_path)
    return round(total_size / 1024, 2)

def get_file_count(directory, ignored_patterns, project_dir, specified_extensions):
    count = 0
    for root, dirs, files in os.walk(directory):
        # Explicitly remove node_modules from dirs to not walk into it
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        for file in files:
            file_path = os.path.join(root, file)
            if not should_ignore(file_path, ignored_patterns, project_dir):
                _, extension = os.path.splitext(file)
                if not specified_extensions or extension in specified_extensions:
                    count += 1
    return count

def get_largest_files(directory, num_files=5):
    largest_files = []
    for root, dirs, files in os.walk(directory):
        # Explicitly remove node_modules from dirs to not walk into it
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if len(largest_files) < num_files:
                heapq.heappush(largest_files, (file_size, file))
            else:
                heapq.heappushpop(largest_files, (file_size, file))
    return [file for _, file in largest_files]

def prompt_user_for_exclusion(directory, project_dir, ignored_patterns, specified_extensions, total_size, file_count_threshold=10, size_threshold=20):
    if directory == project_dir or 'node_modules' in directory.split(os.sep):
        return False, []  # Skip exclusion prompt for the root directory and node_modules

    file_count = get_file_count(directory, ignored_patterns, project_dir, specified_extensions)
    directory_size_kb = get_directory_size_in_kb(directory, ignored_patterns, project_dir, specified_extensions)

    if file_count > file_count_threshold or directory_size_kb > size_threshold:
        print(f"\nDirectory: {directory}")
        print(f"File Count: {file_count}")
        print(f"Total Size: {directory_size_kb} KB")

        largest_files = get_largest_files(directory)
        print("Largest Files:", ", ".join(largest_files))

        while True:
            choice = input(f"Do you want to (E)xclude, (I)nclude, (G)enerate the whole file ({total_size} KB), or (O)nly include specific file extensions? (default: Include) ").lower()
            if choice == 'e':
                return True, []
            elif choice == 'i' or choice == '':  # Accept empty input as 'I'
                return False, []
            elif choice == 'g':
                return False, specified_extensions
            elif choice == 'o':
                extensions = input("Enter the file extensions to include (comma-separated): ").split(',')
                extensions = [ext.strip() for ext in extensions]
                return False, extensions
            else:
                print("Invalid choice. Please enter 'E', 'I', 'G', 'O', or press Enter for Include.")

    return False, []

def get_extension_sizes(project_dirs, excluded_paths):
    extension_sizes = {}
    total_size = 0
    for project_dir in project_dirs:
        ignored_patterns = get_ignored_patterns(project_dir, excluded_paths)
        for root, dirs, files in os.walk(project_dir):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip the .git directory
            if 'node_modules' in dirs:
                dirs.remove('node_modules')  # Always skip node_modules
            for file in files:
                file_path = os.path.join(root, file)
                if not should_ignore(file_path, ignored_patterns, project_dir):
                    _, extension = os.path.splitext(file)
                    extension_sizes[extension] = extension_sizes.get(extension, 0) + os.path.getsize(file_path)
                    total_size += os.path.getsize(file_path)
    for extension, size in extension_sizes.items():
        extension_sizes[extension] = round(size / 1024, 2)  # Convert to KB
    total_size = round(total_size / 1024, 2)  # Convert to KB
    return extension_sizes, total_size

def get_total_source_code_size(project_dirs, excluded_paths, specified_extensions):
    total_size = 0
    for project_dir in project_dirs:
        ignored_patterns = get_ignored_patterns(project_dir, excluded_paths)
        for root, dirs, files in os.walk(project_dir):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip the .git directory
            if 'node_modules' in dirs:
                dirs.remove('node_modules')  # Always skip node_modules
            for file in files:
                file_path = os.path.join(root, file)
                if not should_ignore(file_path, ignored_patterns, project_dir):
                    _, extension = os.path.splitext(file)
                    if not specified_extensions or extension in specified_extensions:
                        total_size += os.path.getsize(file_path)
    return total_size

def extract_source_code(project_dirs, excluded_paths, specified_extensions, file_size_limit):
    file_tree = []
    file_contents = []
    current_file_size = 0
    file_index = 0

    def write_output_file(content, index):
        output_file = f"knowledge_{index}.txt"
        with open(output_file, "w") as file:
            if index == 0:
                file.write("File Tree:\n")
                file.write("\n".join(file_tree))
                file.write("\n\nFile Contents:\n")
            file.write(content)
        print(f"Source code has been written to {output_file}.")

    for project_dir in project_dirs:
        ignored_patterns = get_ignored_patterns(project_dir, excluded_paths)
        for root, dirs, files in os.walk(project_dir):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip the .git directory
            if 'node_modules' in dirs:
                dirs.remove('node_modules')  # Always skip node_modules
            if should_ignore(root, ignored_patterns, project_dir):
                dirs[:] = []  # Skip subdirectories of the ignored directory
                continue
            level = root.replace(project_dir, "").count(os.sep)
            indent = " " * 4 * level
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            for file in files:
                file_path = os.path.join(root, file)
                if not should_ignore(file_path, ignored_patterns, project_dir):
                    _, extension = os.path.splitext(file)
                    if not specified_extensions or extension in specified_extensions:
                        file_tree.append(f"{indent}    {file}")
                        try:
                            with open(file_path, "r") as f:
                                content = f.read()
                            file_content = f"\n{'=' * 80}\nFile: {file_path}\n{'=' * 80}\n{content}\n"
                            file_content_size = len(file_content) / 1024  # Convert to KB
                            current_file_size += file_content_size
                            if current_file_size > file_size_limit:
                                write_output_file("".join(file_contents), file_index)
                                file_contents = [file_content]
                                current_file_size = file_content_size
                                file_index += 1
                            else:
                                file_contents.append(file_content)
                        except UnicodeDecodeError:
                            file_content = f"\n{'=' * 80}\nFile: {file_path}\n{'=' * 80}\nUnable to decode file contents.\n"
                            file_content_size = len(file_content) / 1024  # Convert to KB
                            current_file_size += file_content_size
                            if current_file_size > file_size_limit:
                                write_output_file("".join(file_contents), file_index)
                                file_contents = [file_content]
                                current_file_size = file_content_size
                                file_index += 1
                            else:
                                file_contents.append(file_content)

    if file_contents:
        write_output_file("".join(file_contents), file_index)

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

# Ask for the file size limit in KB
file_size_limit = float(input("Enter the file size limit in KB (default: 1000): ") or "1000")

# Calculate the total size of the source code files
excluded_paths = []
extension_sizes, total_size = get_extension_sizes(project_dirs, excluded_paths)
print("File sizes per extension (KB):")
for extension, size in extension_sizes.items():
    print(f"{extension}: {size} KB")
print(f"Total size: {total_size} KB")

specified_extensions = input("Enter the file extensions to include (comma-separated, leave empty to include all): ").split(',')
specified_extensions = [ext.strip() for ext in specified_extensions if ext.strip()]

total_size = get_total_source_code_size(project_dirs, excluded_paths, specified_extensions)
# convert to KB
total_size_kb = round(total_size / 1024, 2)
print(f"Estimated size of knowledge.txt: {total_size_kb} KB")

generate_file = False
for project_dir in project_dirs:
    ignored_patterns = get_ignored_patterns(project_dir, excluded_paths)
    for root, dirs, files in os.walk(project_dir):
        if '.git' in dirs:
            dirs.remove('.git')  # Skip the .git directory
        exclude, extensions = prompt_user_for_exclusion(root, project_dir, ignored_patterns, specified_extensions, total_size_kb)
        if exclude:
            ignored_patterns.append(os.path.relpath(root, project_dir))
            dirs[:] = []  # Skip subdirectories of the excluded directory
        elif extensions == specified_extensions:
            generate_file = True
            break
    if generate_file:
        break

if generate_file:
    # Extract the source code
    extract_source_code(project_dirs, excluded_paths, specified_extensions, file_size_limit)
else:
    print("Generation of knowledge.txt was not confirmed.")