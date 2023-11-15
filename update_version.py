import re
import subprocess
import configparser


def get_git_tag():
    return subprocess.check_output(["git", "describe", "--tags"]).strip().decode()


def update_version_in_setup_cfg(version):
    config = configparser.ConfigParser()
    config.read("setup.cfg")
    version = version.replace("-", ".")
    config["metadata"]["version"] = version
    with open("setup.cfg", "w") as configfile:
        config.write(configfile)


if __name__ == "__main__":
    git_version = get_git_tag()
    update_version_in_setup_cfg(git_version)
