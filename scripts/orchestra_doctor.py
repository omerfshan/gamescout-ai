"""Check local agent clients; never edits the product or reads credentials."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def locate(name, fallbacks):
    found = shutil.which(name)
    if found:
        return found
    return next((str(p) for p in fallbacks if p.is_file()), None)


def run(command, timeout=45):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        return -1, "", str(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="Make one small model call per provider (uses account quota).")
    args = parser.parse_args()
    clients = {
        "codex": locate("codex", [Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")]),
        "antigravity": locate("agy", [Path.home() / ".local/bin/agy"]),
    }
    failed = False
    for name, executable in clients.items():
        if not executable:
            print(f"{name}: MISSING")
            failed = True
            continue
        code, output, error = run([executable, "--version"])
        print(f"{name}: {output if code == 0 else 'FAILED'}")
        if code:
            print(error)
            failed = True
            continue
        if not args.smoke:
            continue
        prompt = "Do not use tools or change files. Reply exactly READY."
        command = ([executable, "exec", "--sandbox", "read-only", "--ephemeral", prompt]
                   if name == "codex" else
                   [executable, "-p", prompt, "--output-format", "json", "--print-timeout", "30s"])
        code, output, error = run(command)
        if name == "antigravity" and code == 0:
            try:
                result = json.loads(output)
                valid = (result.get("status") == "SUCCESS"
                         and result.get("response", "").strip() == "READY"
                         and not result.get("denied_actions"))
            except (ValueError, AttributeError):
                valid = False
        else:
            valid = code == 0 and output.strip() == "READY"
        print(f"  smoke: {'PASS' if valid else 'FAIL'}")
        if not valid:
            failed = True
            print((error or output)[-2000:])
    print("READY FOR ORCHESTRATOR SETUP" if not failed else "SETUP BLOCKED: see failures above")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
