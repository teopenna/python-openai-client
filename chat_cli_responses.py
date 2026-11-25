from __future__ import annotations

import asyncio
from pathlib import Path
from time import perf_counter

import click
from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AsyncAzureOpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.completion_usage import CompletionUsage

from utility import ReplyResult, append_chat_log, build_client, serialize_usage

load_dotenv()

DEFAULT_API_VERSION = "2024-10-21"
EXIT_COMMANDS = {"exit", "quit", ":q"}
DEFAULT_TEMPERATURE = 0.1
DEFAULT_LOG_FILE = Path("logs", "chat_log.jsonl")

async def stream_reply(
    *,
    client: AsyncAzureOpenAI | AsyncOpenAI,
    deployment: str,
    messages: list[ChatCompletionMessageParam],
    temperature: float,
    top_p: float | None,
    max_output_tokens: int | None
) -> ReplyResult:
    """Stream the assistant reply to the terminal and return the full text."""
    request_started_at = perf_counter()
    
    stream = await client.responses.create(
        model=deployment,
        input=messages,
        stream=True,
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
    )

    parts: list[str] = []
    usage: CompletionUsage | None = None
    click.secho("Assistant: ", fg="green", nl=False)
    async for event in stream:
        if event.type == "response.output_text.delta":
            parts.append(event.delta)
            for character in event.delta:
                click.echo(character, nl=False)

        if event.type == "response.completed":
            usage = event.response.usage

    click.echo()
    reply = "".join(parts).strip()
    if not reply:
        raise click.ClickException("The model returned an empty response.")
    latency_seconds = perf_counter() - request_started_at
    return ReplyResult(reply, serialize_usage(usage), latency_seconds)


async def run_chat(
    *,
    endpoint: str,
    api_key: str,
    deployment: str,
    api_version: str,
    system_prompt: str,
    log_file: Path,
    temperature: float,
    top_p: float | None,
    max_output_tokens: int | None
) -> None:
    valid, client, error_message = build_client(endpoint=endpoint, api_key=api_key, api_version=api_version)

    if not valid:
        raise click.BadParameter(error_message)

    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    click.echo("Connected. Type 'exit' or 'quit' to end the session.")

    try:
        while True:
            try:
                question = click.prompt("You").strip()
            except (EOFError, KeyboardInterrupt):
                click.echo()
                break

            if not question:
                continue
            if question.lower() in EXIT_COMMANDS:
                break

            messages.append({"role": "user", "content": question})
            try:
                reply = await stream_reply(
                    client=client,
                    deployment=deployment,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_output_tokens,
                )
            except APIConnectionError as exc:
                messages.pop()
                click.secho(f"Connection error: {exc}", fg="red", err=True)
                continue
            except APIStatusError as exc:
                messages.pop()
                click.secho(f"API error {exc.status_code}: {exc.message}", fg="red", err=True)
                continue

            messages.append({"role": "assistant", "content": reply.text})
            append_chat_log(
                log_file=log_file,
                prompt=question,
                response=reply.text,
                token_usage=reply.token_usage,
                latency_seconds=reply.latency_seconds,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )
    finally:
        await client.close()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--endpoint",
    prompt="Azure OpenAI endpoint",
    envvar="AZURE_OPENAI_ENDPOINT",
    help="Azure resource endpoint or full /openai/v1/ base URL.",
)
@click.option(
    "--api-key",
    prompt="Azure OpenAI API key",
    hide_input=True,
    envvar="AZURE_OPENAI_API_KEY",
    help="API key for the Azure OpenAI resource.",
)
@click.option(
    "--deployment",
    prompt="Deployment name",
    envvar="AZURE_OPENAI_DEPLOYMENT",
    help="Azure OpenAI deployment name. This is usually not the raw model name.",
)
@click.option(
    "--api-version",
    default=DEFAULT_API_VERSION,
    show_default=True,
    envvar="AZURE_OPENAI_API_VERSION",
    help="Azure OpenAI API version. Ignored when you pass a full /openai/v1/ base URL.",
)
@click.option(
    "--system-prompt",
    default="You are a helpful assistant.",
    show_default=True,
    help="Initial system prompt for the chat session.",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path, dir_okay=False, writable=True),
    default=DEFAULT_LOG_FILE,
    show_default=True,
    help="Append successful prompt/response metadata to this JSONL file.",
)
@click.option(
    "--temperature",
    type=click.FloatRange(min=0.0, max=2.0),
    default=DEFAULT_TEMPERATURE,
    show_default=True,
    help="Sampling temperature for the chat completion.",
)
@click.option(
    "--top-p",
    type=click.FloatRange(min=0.0, max=1.0),
    default=None,
    help="Optional nucleus sampling value for the chat completion.",
)
@click.option(
    "--max-output-tokens",
    type=click.IntRange(min=1),
    default=None,
    help="Optional max output tokens value passed through as an extra request field.",
)
def main(
    endpoint: str,
    api_key: str,
    deployment: str,
    api_version: str,
    system_prompt: str,
    log_file: Path,
    temperature: float,
    top_p: float | None,
    max_output_tokens: int | None,
) -> None:
    """Start an interactive Azure OpenAI chat session."""
    asyncio.run(
        run_chat(
            endpoint=endpoint,
            api_key=api_key,
            deployment=deployment,
            api_version=api_version,
            system_prompt=system_prompt,
            log_file=log_file,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
        )
    )


if __name__ == "__main__":
    main()
