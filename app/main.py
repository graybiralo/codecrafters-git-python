import sys
import os
import zlib
import hashlib
import time
import requests

GITHUB_API_URL = "https://github.com/{}/{}.git"

def init():
    """Initialize the git directory structure."""
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs/heads", exist_ok=True)

    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")

    print("Initialized git directory")

def get_object_path(sha):
    """Return the file path for a given SHA-1 hash in the .git/objects directory."""
    return os.path.join(".git", "objects", sha[0:2], sha[2:])

def write_object(data):
    """Write a compressed Git object to .git/objects and return its SHA-1 hash."""
    sha = hashlib.sha1(data).hexdigest()
    object_path = get_object_path(sha)

    os.makedirs(os.path.dirname(object_path), exist_ok=True)
    
    with open(object_path, "wb") as f:
        f.write(zlib.compress(data))

    return sha

def cat_file(sha):
    """Display the content of a Git object (blob) given its SHA-1 hash."""
    path = get_object_path(sha)
    
    try:
        with open(path, "rb") as file:
            file_contents = file.read()
        
        decompressed_file = zlib.decompress(file_contents)
        null_value = decompressed_file.find(b"\x00")
        content = decompressed_file[null_value + 1:].decode("utf-8", errors="ignore")
        
        print(content, end="")  
    except FileNotFoundError:
        print(f"Object {sha} not found!", file=sys.stderr)
        sys.exit(1)

def hash_object(file_name):
    """Create a blob object for a file and store it in the .git/objects directory."""
    try:
        with open(file_name, "rb") as file:
            file_content = file.read()

        if not file_content:
            print(f"Error: {file_name} is empty!", file=sys.stderr)
            sys.exit(1)

        header = f"blob {len(file_content)}\x00".encode("utf-8")
        store = header + file_content
        return write_object(store)
    except FileNotFoundError:
        print(f"Error: {file_name} not found!", file=sys.stderr)
        sys.exit(1)

def write_tree(directory="."):
    """Create a tree object from the working directory and return its SHA-1 hash."""
    entries = []

    for entry in sorted(os.listdir(directory)):
        path = os.path.join(directory, entry)

        # Skip .git directory
        if ".git" in path:
            continue

        if os.path.isfile(path):
            mode = "100644"  # Regular file mode
            sha = hash_object(path)
        elif os.path.isdir(path):
            mode = "040000"  # Directory mode
            sha = write_tree(path)

        if sha:
            entries.append(f"{mode} {entry}\x00".encode() + bytes.fromhex(sha))
        else:
            print(f"Error: Failed to create SHA for {path}", file=sys.stderr)
            sys.exit(1)

    tree_data = b"tree " + str(len(b"".join(entries))).encode() + b"\x00" + b"".join(entries)
    return write_object(tree_data)

def ls_tree(tree_sha):
    """List file and directory names in a tree object given its SHA hash."""
    object_path = get_object_path(tree_sha)

    try:
        with open(object_path, "rb") as file:
            compressed_data = file.read()

        decompressed_data = zlib.decompress(compressed_data)
        null_idx = decompressed_data.find(b'\x00') + 1
        data = decompressed_data[null_idx:]

        entries = []
        while data:
            space_idx = data.find(b' ')  
            null_idx = data.find(b'\x00', space_idx)  

            if space_idx == -1 or null_idx == -1:
                break  

            name = data[space_idx + 1:null_idx].decode()
            entries.append(name)

            data = data[null_idx + 21:]

        for entry in sorted(entries):
            print(entry)

    except FileNotFoundError:
        print(f"Tree object {tree_sha} not found!", file=sys.stderr)
        sys.exit(1)

def commit_tree(tree_sha, parent_sha=None, message=""):
    """Create a commit object referencing the given tree SHA."""
    author = "Your Name <your.email@example.com>"
    timestamp = int(time.time())
    timezone = "+0000"

    commit_content = f"tree {tree_sha}\n"
    if parent_sha:
        commit_content += f"parent {parent_sha}\n"
    commit_content += f"author {author} {timestamp} {timezone}\n"
    commit_content += f"committer {author} {timestamp} {timezone}\n\n"
    commit_content += f"{message}\n"

    header = f"commit {len(commit_content)}\x00".encode("utf-8")
    store = header + commit_content.encode("utf-8")

    return write_object(store)

def fetch_refs(remote_url):
    """Fetch references from a remote Git repository (e.g., GitHub)."""
    # Request the refs from the remote Git repository
    url = remote_url + "/info/refs?service=git-upload-pack"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: Failed to fetch refs from {remote_url}", file=sys.stderr)
        sys.exit(1)

    return response.text

def clone_repository(remote_url, destination_dir):
    """Clone a remote Git repository to the local machine."""
    print(f"Cloning from {remote_url} to {destination_dir}")
    os.makedirs(destination_dir, exist_ok=True)
    os.chdir(destination_dir)

    # Initialize local repository
    init()

    # Fetch refs from the remote repository
    refs = fetch_refs(remote_url)
    print(refs)  # Show fetched refs

    # At this point, you would fetch the necessary objects (e.g., packfiles) and unpack them
    # For now, we just print the fetched refs.
    print("Repository cloned successfully!")

def main():
    """Main function to parse commands and call appropriate methods."""
    if len(sys.argv) < 2:
        print("Usage: python your_program.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init()
    elif command == "write-tree":
        print(write_tree())
    elif command == "cat-file":
        if len(sys.argv) != 4:
            print("Usage: git cat-file <type> <object>", file=sys.stderr)
            sys.exit(1)
        sha = sys.argv[3]
        cat_file(sha)
    elif command == "hash-object":
        if len(sys.argv) != 4 or sys.argv[2] != "-w":
            print("Usage: hash-object -w <file>", file=sys.stderr)
            sys.exit(1)
        file_name = sys.argv[3]
        # print(hash_object(file_name))
    elif command == "ls-tree":
        if len(sys.argv) < 4 or sys.argv[2] != "--name-only":
            print("Usage: ls-tree --name-only <tree_sha>", file=sys.stderr)
            sys.exit(1)
        tree_sha = sys.argv[3]
        ls_tree(tree_sha)
    elif command == "commit-tree":
        if len(sys.argv) < 5 or sys.argv[2] != "-m":
            print("Usage: commit-tree <tree_sha> -m <message> [-p <parent_sha>]", file=sys.stderr)
            sys.exit(1)
        tree_sha = sys.argv[3]
        message = sys.argv[4]
        parent_sha = None
        if len(sys.argv) > 6 and sys.argv[5] == "-p":
            parent_sha = sys.argv[6]
        print(commit_tree(tree_sha, parent_sha, message))
    elif command == "clone":
        if len(sys.argv) != 4:
            print("Usage: clone <remote_url> <destination_dir>", file=sys.stderr)
            sys.exit(1)
        remote_url = sys.argv[2]
        destination_dir = sys.argv[3]
        clone_repository(remote_url, destination_dir)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
