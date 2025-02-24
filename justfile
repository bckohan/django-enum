set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set unstable := true
set script-interpreter := ['uv', 'run', '--script']

export PYTHONPATH := source_directory()

[private]
default:
    @just --list --list-submodules

# run the django admin
[script]
manage *COMMAND:
    import os
    import sys
    from django.core import management
    sys.path.append(os.getcwd())
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    management.execute_from_command_line(sys.argv + "{{ COMMAND }}".split(" "))

# install the uv package manager
[linux]
[macos]
install_uv:
    curl -LsSf https://astral.sh/uv/install.sh | sh

# install the uv package manager
[windows]
install_uv:
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# setup the venv and pre-commit hooks
setup python="python":
    uv venv -p {{ python }}
    @just run pre-commit install

# install git pre-commit hooks
install-precommit:
    @just run pre-commit install

# update and install development dependencies
install *OPTS:
    uv sync {{ OPTS }}
    @just run pre-commit install

# install documentation dependencies
install-docs:
    uv sync --group docs --all-extras

[script]
_lock-python:
    import tomlkit
    import sys
    f='pyproject.toml'
    d=tomlkit.parse(open(f).read())
    d['project']['requires-python']='=={}'.format(sys.version.split()[0])
    open(f,'w').write(tomlkit.dumps(d))

# lock to specific python and versions of given dependencies
test-lock +PACKAGES: _lock-python
    uv add {{ PACKAGES }}

# run static type checking
check-types:
    @just run mypy src/django_enum

# run package checks
check-package:
    @just run pip check

# remove doc build artifacts
[script]
clean-docs:
    import shutil
    shutil.rmtree('./doc/build', ignore_errors=True)

# remove the virtual environment
[script]
clean-env:
    import shutil
    import sys
    shutil.rmtree(".venv", ignore_errors=True)

# remove all git ignored files
clean-git-ignored:
    git clean -fdX

# remove all non repository artifacts
clean: clean-docs clean-env clean-git-ignored

# build html documentation
build-docs-html: install-docs
    @just run sphinx-build --fresh-env --builder html --doctree-dir ./doc/build/doctrees ./doc/source ./doc/build/html

# build pdf documentation
build-docs-pdf: install-docs
    @just run sphinx-build --fresh-env --builder latexpdf --doctree-dir ./doc/build/doctrees ./doc/source ./doc/build/pdf

# build the docs
build-docs: build-docs-html

# build docs and package
build: build-docs-html
    uv build

# open the html documentation
[script]
open-docs:
    import os
    import webbrowser
    webbrowser.open(f'file://{os.getcwd()}/doc/build/html/index.html')

# build and open the documentation
docs: build-docs-html open-docs

# serve the documentation, with auto-reload
docs-live: install-docs
    @just run sphinx-autobuild doc/source doc/build --open-browser --watch src --port 8000 --delay 1

_link_check:
    -uv run sphinx-build -b linkcheck -Q -D linkcheck_timeout=10 ./doc/source ./doc/build

# check the documentation links for broken links
[script]
check-docs-links: _link_check
    import os
    import sys
    import json
    from pathlib import Path
    # The json output isn't valid, so we have to fix it before we can process.
    data = json.loads(f"[{','.join((Path(os.getcwd()) / 'doc/build/output.json').read_text().splitlines())}]")
    broken_links = [link for link in data if link["status"] not in {"working", "redirected", "unchecked", "ignored"}]
    if broken_links:
        for link in broken_links:
            print(f"[{link['status']}] {link['filename']}:{link['lineno']} -> {link['uri']}", file=sys.stderr)
        sys.exit(1)

# lint the documentation
check-docs:
    @just run doc8 --ignore-path ./doc/build --max-line-length 100 -q ./doc

# lint the code
check-lint:
    @just run ruff check --select I
    @just run ruff check

# check if the code needs formatting
check-format:
    @just run ruff format --check

# check that the readme renders
check-readme:
    @just run -m readme_renderer ./README.md -o /tmp/README.html

# sort the python imports
sort-imports:
    @just run ruff check --fix --select I

# format the code and sort imports
format: sort-imports
    just --fmt --unstable
    @just run ruff format

# sort the imports and fix linting issues
lint: sort-imports
    @just run ruff check --fix

# fix formatting, linting issues and import sorting
fix: lint format

# run all static checks
check: check-lint check-format check-types check-package check-docs check-docs-links check-readme

# run all tests
test-all DB_CLIENT="dev":
    # No Optional Dependency Unit Tests
    # todo clean this up, rerunning a lot of tests
    uv sync --group {{ DB_CLIENT }}
    @just manage makemigrations
    @just run pytest --cov-append
    uv sync --extra properties --group {{ DB_CLIENT }}
    @just manage makemigrations
    @just run pytest --cov-append
    uv sync --extra rest --group {{ DB_CLIENT }}
    @just manage makemigrations
    @just run pytest --cov-append
    uv sync --all-extras --group {{ DB_CLIENT }}
    @just manage makemigrations
    @just run pytest --cov-append

# run tests
test *TESTS:
    @just run pytest --cov-append {{ TESTS }}

# run the pre-commit checks
precommit:
    @just run pre-commit

# generate the test coverage report
coverage:
    @just run coverage combine --keep *.coverage
    @just run coverage report
    @just run coverage xml

# run the command in the virtual environment
run +ARGS:
    uv run {{ ARGS }}

# validate the given version string against the lib version
[script]
validate_version VERSION:
    import re
    import tomllib
    import django_enum
    version = re.match(r"v?(\d+[.]\d+[.]\w+)", "{{ VERSION }}").groups()[0]
    assert version == tomllib.load(open('pyproject.toml', 'rb'))['project']['version']
    assert version == django_enum.__version__
    print(version)

# issue a relase for the given semver string (e.g. 2.1.0)
release VERSION:
    @just validate_version v{{ VERSION }}
    git tag -s v{{ VERSION }} -m "{{ VERSION }} Release"
    git push origin v{{ VERSION }}
