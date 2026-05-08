# Console application to interact with OpenAI-style LLMs

I'm a software architect with more than 20 years of experience building enterprise systems, mostly in the Microsoft ecosystem. I'm now spending a lot of time learning how my background translates into AI engineering, and I'm experimenting with languages and tools I know only marginally.

This repository contains a small Python console application for interactive chat against Azure OpenAI compatible endpoints. Both entry points stream replies in the terminal and append prompt/response metadata to `logs/chat_log.jsonl`.

## What's in the project

- `chat_cli.py`: uses the Chat Completions API.
- `chat_cli_responses.py`: uses the Responses API.

The practical difference is simple:

- Use `chat_cli.py` if you want the classic Chat Completions flow.
- Use `chat_cli_responses.py` if you want to work with the newer Responses API.

Both scripts support `--top-p` and `--max-output-tokens`; the main difference is the underlying API they call.

## Create a virtual environment

From the project root (replace myenv with your virtual environment name):

```bash
python3 -m venv myenv
source myenv/bin/activate
```

If `python3.x` is not available on your machine, please refer to the [official site](https://www.python.org/) to install it.

## Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

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

## Run the Chat Completions CLI

```bash
python chat_cli.py
```

Example with explicit options:

```bash
python chat_cli.py --system-prompt "You are a concise assistant." --temperature 0.2 --top-p 0.9 --max-output-tokens 400
```

This variant uses the Chat Completions API.

## Run the Responses CLI

```bash
python chat_cli_responses.py
```

Example with explicit options:

```bash
python chat_cli_responses.py --system-prompt "You are a concise assistant." --temperature 0.2 --top-p 0.9 --max-output-tokens 400
```

This variant uses the Responses API.

## Useful help commands

```bash
python chat_cli.py --help
python chat_cli_responses.py --help
```
