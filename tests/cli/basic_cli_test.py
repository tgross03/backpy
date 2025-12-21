import subprocess


def test_cli():
    subprocess.run(["backpy"])
    subprocess.run(["backpy", "--version"])
    output = subprocess.run(["backpy", "--info"])
    print("output", output)
