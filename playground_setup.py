#!/usr/bin/env python3

import os
import sys
import apt
import subprocess
import shutil
import hashlib
from collections import OrderedDict

current_path = os.path.abspath(os.curdir)

# Name,  (URL, Recursive clone, Develop, SHA1)
repos = [
    # HDL
    ("migen",        ("https://github.com/m-labs/",        True,  True, None)),
    # ("nmigen",       ("https://github.com/nmigen/",        True,  True, None)),

    # LiteX SoC builder
    ("pythondata-software-picolibc",    ("https://github.com/litex-hub/",   True,  True, None)),
    ("pythondata-software-compiler_rt", ("https://github.com/litex-hub/",   False, True, None)),
    ("litex",                           ("https://github.com/navan93/",     False, True, None)),

    # LiteX cores ecosystem
    # ("liteeth",      ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litedram",     ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litepcie",     ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litesata",     ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litesdcard",   ("https://github.com/enjoy-digital/", False, True, None)),
    # ("liteiclink",   ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litevideo",    ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litescope",    ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litejesd204b", ("https://github.com/enjoy-digital/", False, True, None)),
    # ("litespi",      ("https://github.com/litex-hub/",     False, True, None)),
    # ("litehyperbus", ("https://github.com/litex-hub/",     False, True, None)),

    # LiteX boards support
    # ("litex-boards", ("https://github.com/litex-hub/",     False, True, None)),

    # Optional LiteX data
    ("pythondata-misc-tapcfg",     ("https://github.com/litex-hub/", False, True, None)),
    ("pythondata-misc-opentitan",  ("https://github.com/litex-hub/", False, True, None)),
    ("pythondata-cpu-vexriscv",    ("https://github.com/litex-hub/", False, True, None)),
    ("pythondata-cpu-cv32e40p",    ("https://github.com/litex-hub/", True,  True, None)),
]

system_deps = [
    "libevent-dev",
    "libjson-c-dev",
    "gtkwave",
    "gcc-riscv64-unknown-elf"
]

verilator_deps = [
    "perl",
    "make",
    "autoconf",
    "g++",
    "flex",
    "bison",
    "ccache",
    "libgoogle-perftools-dev",
    "numactl",
    "perl-doc",
    "libfl2",
    "libfl-dev",
    "zlibc",
    "zlib1g",
    "zlib1g-dev",
]

repos = OrderedDict(repos)

# Repositories cloning
if "init" in sys.argv[1:]:
    for name in repos.keys():
        os.chdir(os.path.join(current_path, "deps"))
        if not os.path.exists(name):
            url, need_recursive, need_develop, sha1 = repos[name]
            # clone repo (recursive if needed)
            print("[cloning " + name + "]...")
            full_url = url + name
            opts = "--recursive" if need_recursive else ""
            subprocess.check_call("git clone " + full_url + " " + opts, shell=True)
            if sha1 is not None:
                os.chdir(os.path.join(current_path, name))
                os.system("git checkout {:040x}".format(sha1))

# Repositories installation
if "install" in sys.argv[1:]:
    for name in repos.keys():
        os.chdir(os.path.join(current_path))
        url, need_recursive, need_develop, sha1 = repos[name]
        # develop if needed
        print("[installing " + name + "]...")
        if need_develop:
            os.chdir(os.path.join(current_path, "deps", name))
            if "--user" in sys.argv[1:]:
                subprocess.check_call("pip3 install -e --user .", shell=True)
            else:
                subprocess.check_call("pip3 install -e .", shell=True)

    if "--user" in sys.argv[1:]:
        if ".local/bin" not in os.environ.get("PATH", ""):
            print("Make sure that ~/.local/bin is in your PATH")
            print("export PATH=$PATH:~/.local/bin")

    for pkg_name in system_deps:
        subprocess.check_call("sudo apt-get install "+pkg_name, shell=True)


# Verilator installation
if "verilator" in sys.argv[1:]:
    os.chdir(os.path.join(current_path, "deps"))
    name = "verilator"
    url = "https://github.com/verilator/"
    full_url = url + name
    if not os.path.exists(name):
        print("[cloning " + name + "]...")
        subprocess.check_call("git clone " + full_url, shell=True)
    for pkg_name in verilator_deps:
        subprocess.check_call("sudo apt-get install " + pkg_name, shell=True)
    os.chdir(os.path.join(current_path, "deps", name))
    subprocess.check_call("git pull", shell=True)
    subprocess.check_call("git checkout stable", shell=True)
    subprocess.check_call("autoconf", shell=True)
    subprocess.check_call("./configure", shell=True)
    subprocess.check_call("make -j `nproc`", shell=True)
    subprocess.check_call("make test", shell=True)
    subprocess.check_call("sudo make install", shell=True)

    


    
