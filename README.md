# OwnGit – A Git Implementation in Python

**OwnGit** is a custom Git implementation built from scratch in Python, inspired by how Git actually works under the hood.  
This project is part of the [Codecrafters Git Challenge](https://codecrafters.io), where developers recreate core Git features step-by-step.

---

## Features Implemented

- `init`: Initialize a new Git repository.
- `hash-object`: Create Git blob objects from files and store them.
- `cat-file`: Read and print the content of Git objects.
- `write-tree`: Build a tree object from the current working directory.
- `commit-tree`: Create a commit object referencing a tree (and optionally a parent).
- `ls-tree`: List files/directories in a tree object.
- `clone`: Clone a remote Git repository via Smart HTTP and display remote references.

---

##  Installation

```bash
git clone https://github.com/yourusername/OwnGit.git
cd OwnGit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```



##  Usage

You can use OwnGit by invoking its functionality from the command line using the following commands.

```bash
# Initialize a new Git repository
python3 app/main.py init

# Hash a file and store it as a Git object
python3 app/main.py hash-object -w example.txt

# Print the content of a Git object (blob) by SHA
python3 app/main.py cat-file -p <sha>

# Write a tree object from current directory contents
python3 app/main.py write-tree

# List files in a tree object by SHA
python3 app/main.py ls-tree --name-only <tree_sha>

# Commit a tree with a message
python3 app/main.py commit-tree <tree_sha> -m "Initial commit"

# Clone a remote Git repository over HTTPS
python3 app/main.py clone https://github.com/user/repo.git my_local_repo