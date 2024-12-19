import zlib
import time
from datetime import datetime, timezone
import sys
import os
import hashlib


def main():
    try:
        command = sys.argv[1]
        if command == "init":
            initialize_git_dir()
        elif command == "cat-file" and sys.argv[2] == "-p":
            print(read_blob(sys.argv[3]), end="")
        elif command == "hash-object" and sys.argv[2] == "-w":
            print(create_blob(sys.argv[3]))
        elif command == "ls-tree":
            if sys.argv[2] == "--name-only":
                print(read_tree(sys.argv[3]), end="")
            else:
                print(read_tree(sys.argv[3], False), end="")
        elif command == "write-tree":
            print(write_tree())
        elif command == "commit-tree":
            print(create_commit(sys.argv[2], sys.argv[4], sys.argv[6]))
        else:
            raise IndexError
    except IndexError:
        raise RuntimeError("Unknown command")


def initialize_git_dir() -> None:
    """Initializes a git directory in the directory that this program was called in. This
      program keeps it simple by only creating the 'objects', 'refs', and 'HEAD' subdirectories
      in the '.git' directory"""
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")


def get_object_content(sha_hash: str):
    with open(f".git/objects/{sha_hash[:2]}/{sha_hash[2:]}", "rb") as file:
        content = zlib.decompress(file.read())
    return content.split(b"\x00", maxsplit=1)[1]


def read_blob(sha_hash: str) -> str:
    """Given a blob object's sha_hash, this method will return the contents of the file that
     the blob object refers to"""
    return get_object_content(sha_hash).decode()


def _create_object_file(decompressed_content: bytes):
    sha_hash = hashlib.sha1()
    sha_hash.update(decompressed_content)
    hash_output = sha_hash.hexdigest()
    dir_path = f".git/objects/{hash_output[:2]}"
    os.makedirs(dir_path, exist_ok=True)
    with open(f"{dir_path}/{hash_output[2:]}", "wb") as file:
        file.write(zlib.compress(decompressed_content))
    return hash_output


def create_blob(file_path: str) -> str:
    """Given the path to a file, this method will create a blob object that stores the file's content
    and return the blob's sha hash"""
    with open(file_path, 'r') as file:
        content = file.read()
    decompressed_content = f"blob {len(content)}\0{content}".encode()
    return _create_object_file(decompressed_content)


def code_to_type(code: str) -> str:
    if code in ('100644', '100755', '120000'):
        return 'blob'
    elif code == '40000':
        return 'directory'


def read_tree(sha_hash: str, name_only: bool =True) -> str:
    tree_content = get_object_content(sha_hash)
    index = 0
    output = ""
    while index < len(tree_content):
        null_index = tree_content.index(b"\0", index)
        file_code, file_name = tree_content[index: null_index].decode().split()
        file_sha = tree_content[null_index + 1: null_index + 21].hex()
        if name_only:
            output += file_name + "\n"
        else:
            output += f"{file_code} {code_to_type(file_code)} {file_sha}\t{file_name}\n"
        index = null_index + 21
    return output


def write_tree(path: str = "./"):
    files = os.listdir(path)
    files.sort()
    decompressed_content = b""
    for element in files:
        file_path = os.path.join(path, element)
        if element == ".git":
            continue
        if os.path.isfile(file_path):
            decompressed_content += f"100644 {element}\0".encode() + bytes.fromhex(create_blob(file_path))
        if os.path.isdir(file_path):
            decompressed_content += f"40000 {element}\0".encode() + bytes.fromhex(write_tree(file_path))
    decompressed_content = f"tree {len(decompressed_content)}\0".encode() + decompressed_content
    return _create_object_file(decompressed_content)

def create_commit(tree_sha, commit_sha, commit_message):
    info = f"Jisha Rajala <jrajala@uci.edu> {int(time.time())} {datetime.now(timezone.utc).astimezone().strftime('%z')}"
    decompressed_content = f"tree {tree_sha}\nparent {commit_sha}\nauthor {info}\ncommitter {info}\n\n{commit_message}\n"
    decompressed_content = f"commit {len(decompressed_content)}\0{decompressed_content}".encode()
    return _create_object_file(decompressed_content)

if __name__ == "__main__":
    main()

      

       
   
