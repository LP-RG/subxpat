import os.path as path


def extract_name(file_path: str) -> str:
    return path.splitext(path.basename(file_path))[0]
