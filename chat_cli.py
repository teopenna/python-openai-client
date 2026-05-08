from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse

import click
from openai import APIConnectionError, APIStatusError, AsyncAzureOpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.completion_usage import CompletionUsage
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_VERSION = "2024-10-21"
EXIT_COMMANDS = {"exit", "quit", ":q"}
DEFAULT_TEMPERATURE = 0.1
DEFAULT_LOG_FILE = Path("logs", "chat_log.jsonl")

class EndpointMode(StrEnum):
    AZURE_RESOURCE = "azure-resource"
    V1_BASE_URL = "v1-base-url"


type TokenUsage = dict[str, object] | None


@dataclass(slots=True)
class ReplyResult:
    text: str
    token_usage: TokenUsage
    latency_seconds: float


def normalize_endpoint(endpoint: str) -> tuple[EndpointMode, str]:
    """Accept either a resource endpoint or a full /openai/v1 base URL."""
    normalized = endpoint.strip().rstrip("/")
    parsed = urlparse(normalized)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise click.BadParameter("Use a full HTTPS endpoint, for example https://my-resource.openai.azure.com")

    path = parsed.path.rstrip("/")
    if path == "":
        return EndpointMode.AZURE_RESOURCE, normalized
    if path == "/openai/v1":
        return EndpointMode.V1_BASE_URL, f"{normalized}/"

    raise click.BadParameter(
        "Use either the Azure resource endpoint (https://...openai.azure.com) "
        "or the full v1 base URL (.../openai/v1/)."
    )


def build_client(*, endpoint: str, api_key: str, api_version: str) -> AsyncAzureOpenAI | AsyncOpenAI:
    mode, normalized_endpoint = normalize_endpoint(endpoint)
    if mode is EndpointMode.V1_BASE_URL:
        return AsyncOpenAI(api_key=api_key, base_url=normalized_endpoint)
    return AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=normalized_endpoint,
        api_version=api_version,
    )


def serialize_usage(usage: CompletionUsage | None) -> TokenUsage:
    if usage is None:
        return None
    return usage.model_dump(mode="json", exclude_none=True)


def append_chat_log(
    *,
    log_file: Path,
    prompt: str,
    response: str,
    token_usage: TokenUsage,
    latency_seconds: float,
    temperature: float,
    top_k: int | None,
    top_p: float | None,
) -> None:
    entry = {
        "prompt": prompt,
        "response": response,
        "token_usage": token_usage,
        "latency_seconds": round(latency_seconds, 3),
        "model_parameters": {
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
        },
    }
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


async def stream_reply(
    *,
    client: AsyncAzureOpenAI | AsyncOpenAI,
    deployment: str,
    messages: list[ChatCompletionMessageParam],
    temperature: float,
    top_k: int | None,
    top_p: float | None,
) -> ReplyResult:
    """Stream the assistant reply to the terminal and return the full text."""
    request_started_at = perf_counter()
    extra_body = {"top_k": top_k} if top_k is not None else None
    stream = await client.chat.completions.create(
        model=deployment,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
        temperature=temperature,
        top_p=top_p,
        extra_body=extra_body,
    )

    parts: list[str] = []
    usage: CompletionUsage | None = None
    click.secho("Assistant: ", fg="green", nl=False)
    async for chunk in stream:
        if chunk.usage is not None:
            usage = chunk.usage

        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta.content
        if not delta:
            continue

        parts.append(delta)
        for character in delta:
            click.echo(character, nl=False)

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
    top_k: int | None,
    top_p: float | None,
) -> None:
    client = build_client(endpoint=endpoint, api_key=api_key, api_version=api_version)
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
                    top_k=top_k,
                    top_p=top_p,
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
                top_k=top_k,
                top_p=top_p,
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
    "--top-k",
    type=click.IntRange(min=1),
    default=None,
    help="Optional top-k sampling value passed through as an extra request field.",
)
@click.option(
    "--top-p",
    type=click.FloatRange(min=0.0, max=1.0),
    default=None,
    help="Optional nucleus sampling value for the chat completion.",
)
def main(
    endpoint: str,
    api_key: str,
    deployment: str,
    api_version: str,
    system_prompt: str,
    log_file: Path,
    temperature: float,
    top_k: int | None,
    top_p: float | None,
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
            top_k=top_k,
            top_p=top_p,
        )
    )


if __name__ == "__main__":
    main()
