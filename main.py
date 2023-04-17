import os


def get_env_path() -> str:
    shell_path = os.environ.get("SHELL")

    match shell_path:
        case "/bin/bash":
            return "Greeting bash"
        case _:
            return f"Hello {shell_path}"


if __name__ == "__main__":
    print(get_env_path())
