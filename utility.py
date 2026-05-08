"""Contains utility functions and classes for the chat CLI."""

from dataclasses import dataclass
from enum import StrEnum
import json
from urllib.parse import urlparse
from zipfile import Path

from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types import CompletionUsage


class EndpointMode(StrEnum):
    AZURE_RESOURCE = "azure-resource"
    V1_BASE_URL = "v1-base-url"


type TokenUsage = dict[str, object] | None


@dataclass(slots=True)
class ReplyResult:
    text: str
    token_usage: TokenUsage
    latency_seconds: float


def normalize_endpoint(endpoint: str) -> tuple[bool, EndpointMode, str]:
    """Accept either a resource endpoint or a full /openai/v1 base URL."""
    normalized = endpoint.strip().rstrip("/")
    parsed = urlparse(normalized)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, None, "Use a full HTTPS endpoint, for example https://my-resource.openai.azure.com"
        # raise click.BadParameter("Use a full HTTPS endpoint, for example https://my-resource.openai.azure.com")

    path = parsed.path.rstrip("/")
    if path == "":
        return True, EndpointMode.AZURE_RESOURCE, normalized
    if path == "/openai/v1":
        return True, EndpointMode.V1_BASE_URL, f"{normalized}/"

    return False, None, "Use either the Azure resource endpoint (https://...openai.azure.com) or the full v1 base URL (.../openai/v1/)."
    # raise click.BadParameter(
    #     "Use either the Azure resource endpoint (https://...openai.azure.com) "
    #     "or the full v1 base URL (.../openai/v1/)."
    # )


def build_client(*, endpoint: str, api_key: str, api_version: str) -> tuple[bool, AsyncAzureOpenAI | AsyncOpenAI, str]:
    valid, mode, normalized_endpoint = normalize_endpoint(endpoint)
    if not valid:
        return False, None, normalized_endpoint
    
    if mode is EndpointMode.V1_BASE_URL:
        return True, AsyncOpenAI(api_key=api_key, base_url=normalized_endpoint), ""
    return True, AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=normalized_endpoint,
        api_version=api_version,
    ), ""


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
