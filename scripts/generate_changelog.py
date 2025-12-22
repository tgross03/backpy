import subprocess
from pathlib import Path

import backpy
from backpy import TOMLConfiguration

# FIXME: The changelog has to be generated without the
# --draft option in order to delete the fragments

if __name__ == "__main__":
    backpy_dir = Path(backpy.__file__).parent.parent
    pyproject = TOMLConfiguration(backpy_dir / "pyproject.toml")
    changelog_location = pyproject["tool.towncrier.filename"]

    changelog_path = backpy_dir / changelog_location

    if not changelog_path.is_file():
        print(f"No changelog found at {changelog_location} ... Generating new file.")
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        changelog_path.touch(exist_ok=True)

    result = subprocess.run(
        ["towncrier", "--draft"],
        cwd=backpy_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise ChildProcessError(f"Error generating changelog draft: {result.stderr}")
    else:
        draft_content = result.stdout

        with open(changelog_path, "r+") as changelog_file:
            content = changelog_file.read()
            changelog_file.seek(0)
            changelog_file.write(draft_content + "\n" + content)

        print(f"Changelog updated at {changelog_location}")
