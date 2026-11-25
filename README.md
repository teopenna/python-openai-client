# Console application to interact with OpenAI-style LLMs

I'm a software architect with many years of experience building enterprise systems, mostly in the Microsoft ecosystem. I'm now spending a lot of time learning how my background translates into AI engineering, and I'm experimenting with languages and tools I know only marginally.

This repository contains a small Python console application for interactive chat against Azure OpenAI compatible endpoints. Both entry points stream replies in the terminal and append prompt/response metadata to `logs/chat_log.jsonl`.

## What's in the project

- `chat_cli.py`: uses the [Chat Completions API](https://developers.openai.com/api/reference/chat-completions/overview/).
- `chat_cli_responses.py`: uses the [Responses API](https://developers.openai.com/api/reference/resources/responses).

The practical difference is simple:

- Use `chat_cli.py` if you want the classic Chat Completions flow.
- Use `chat_cli_responses.py` if you want to work with the newer Responses API.

You can find a comparison between the two APIs [here](https://developers.openai.com/api/docs/guides/migrate-to-responses).

Both scripts support `--top-p` and `--max-output-tokens`; the main difference is the underlying API they call.

## Set up this repository with uv

Install uv using the instructions for your platform, then confirm it is available with `uv --version`. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

These examples use Python 3.15.2, the latest stable release at the time of writing (November 25, 2026). [Python releases](https://www.python.org/downloads/source/)

From the repository root, create `.venv` and install the dependencies listed in `requirements.txt`. uv downloads the requested Python version if it needs to.

```bash
uv venv --python 3.15.2
uv pip install -r requirements.txt
```

If you already have another virtual environment active, run `deactivate` before setup so `uv pip install` finds this repository's `.venv`.

You can run the CLIs with `uv run` directly. To use `python` and installed commands directly in your shell, activate `.venv` on macOS or Linux with the following command.

```bash
source .venv/bin/activate
```

In Windows PowerShell, use `.\.venv\Scripts\Activate.ps1`. Run `deactivate` to leave the environment. [uv environment guide](https://docs.astral.sh/uv/pip/environments/)

To install an individual package, use `uv pip install <package>`. If the application needs the package, add it to `requirements.txt` so other users get it during setup. Rerun `uv pip install -r requirements.txt` after the file changes.

## Configure access

Both scripts read configuration from command-line options or environment variables. For a shell session, you can export these values before running either CLI:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
export AZURE_OPENAI_API_VERSION="2024-10-21"
```

During development, it is usually more convenient to create a `.env` file in the project root:

```dotenv
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-10-21
```

The application loads `.env` automatically when it starts.

`AZURE_OPENAI_ENDPOINT` can be either:

- the Azure resource endpoint, for example `https://your-resource.openai.azure.com`
- a full compatible base URL ending in `/openai/v1/`

### Configure temperature for your deployment

For a model that doesn't support `temperature`, add an entry set to `False` in `DEPLOYMENT_TEMPERATURES_ALLOWED` in each script you use ([`chat_cli.py`](chat_cli.py) or [`chat_cli_responses.py`](chat_cli_responses.py)). Use the exact deployment name you pass via `AZURE_OPENAI_DEPLOYMENT` or `--deployment` as the key. The CLI then omits `temperature` from API requests, even when `--temperature` is set.

Both scripts already include `"gpt-5-mini": False`. If you deployed that model under a custom name such as `my-gpt-5-mini`, add that name to the dictionary as well.

```python
DEPLOYMENT_TEMPERATURES_ALLOWED = {
    "gpt-5-mini": False,
    "my-gpt-5-mini": False,
}
```

Deployments whose models support `temperature` use the CLI's temperature setting by default and need no entry.

## Run the Chat Completions CLI

```bash
uv run python chat_cli.py
```

Example with explicit options:

```bash
uv run python chat_cli.py --system-prompt "You are a concise assistant." --temperature 0.2 --top-p 0.9 --max-output-tokens 400
```

This variant uses the Chat Completions API.

## Run the Responses CLI

```bash
uv run python chat_cli_responses.py
```

Example with explicit options:

```bash
uv run python chat_cli_responses.py --system-prompt "You are a concise assistant." --temperature 0.2 --top-p 0.9 --max-output-tokens 400
```

This variant uses the Responses API.

## Useful help commands

```bash
uv run python chat_cli.py --help
uv run python chat_cli_responses.py --help
```

## Work with a uv-managed project

For a new Python project, `uv init` creates a `pyproject.toml`. In the parent directory where you want to create the new project, run the following commands.

```bash
uv init --python 3.15.2 example-project
cd example-project
uv add click
uv add --dev pytest
uv run python -c "import click; print(click.__name__)"
```

`uv add` records dependencies in `pyproject.toml`, updates `uv.lock`, and installs them in `.venv`. Use `--dev` for development tools such as pytest. Use `uv remove <package>` to remove a dependency.

Commit `pyproject.toml` and `uv.lock` so collaborators can install the same resolved dependencies with `uv sync` after cloning. `uv run` keeps the project environment in sync and runs commands without activation. [uv projects guide](https://docs.astral.sh/uv/guides/projects/)
