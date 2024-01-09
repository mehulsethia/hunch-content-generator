import re
from typing import Tuple, Dict
from pathlib import Path
import toml
from rich.console import Console
from utils.console import handle_input

console = Console()
config = {}

def crawl(obj: dict, func=lambda x, y: console.print(f"{x}: {y}"), path=None):
    if path is None:
        path = []
    for key in obj.keys():
        if isinstance(obj[key], dict):
            crawl(obj[key], func, path + [key])
        else:
            func(path + [key], obj[key])

def check(value, checks, name):
    def get_check_value(key, default_result):
        return checks[key] if key in checks else default_result

    incorrect = False
    if value == {}:
        incorrect = True
    if not incorrect and "type" in checks:
        try:
            value = eval(checks["type"])(value)
        except:
            incorrect = True
    # Further checks omitted for brevity...
    return value if not incorrect else handle_input(...)  # handle_input() parameters omitted for brevity

def crawl_and_check(obj: dict, path: list, checks: dict = {}, name=""):
    if len(path) == 0:
        return check(obj, checks, name)
    if path[0] not in obj:
        obj[path[0]] = {}
    obj[path[0]] = crawl_and_check(obj[path[0]], path[1:], checks, path[0])
    return obj

def check_vars(path, checks):
    global config
    console.print(f"Checking path: {path} with checks: {checks}")
    crawl_and_check(config, path, checks)

def check_toml(template_file, config_file) -> Tuple[bool, Dict]:
    global config
    try:
        template = toml.load(template_file)
    except Exception as error:
        console.print(f"[red bold]Error loading {template_file}: {error}")
        return False, {}

    try:
        config = toml.load(config_file)
        console.print(f"Configuration loaded from {config_file}")
    except FileNotFoundError:
        console.print(f"{config_file} not found. Creating a new one.")
        config = {}
    except Exception as error:
        console.print(f"Error reading {config_file}: {error}")
        # Additional error handling omitted for brevity

    # Apply checks selectively
    for key in template.keys():
        if key != "reddit":  # Skip checks for reddit
            crawl_and_check(config, [key], template[key])

    try:
        with open(config_file, "w") as f:
            toml.dump(config, f)
        console.print(f"Configuration saved to {config_file}")
    except Exception as error:
        console.print(f"Error writing to {config_file}: {error}")
        return False, config

    return True, config


if __name__ == "__main__":
    directory = Path().absolute()
    console.print("Directory: ", directory)
    success, loaded_config = check_toml(f"{directory}/utils/.config.template.toml", f"{directory}/config.toml")
    if success:
        console.print("Configuration check completed successfully")
    else:
        console.print("[red bold]Configuration check failed")
