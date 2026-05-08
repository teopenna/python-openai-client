# Python 3.13 Copilot Instructions

Write code for **Python 3.13** and prefer the standard library unless a dependency is clearly justified.

## Core principles

- Favor simple, explicit solutions over clever ones.
- Keep functions small, composable, and easy to test.
- Prefer pure functions for business logic; isolate I/O at boundaries.
- Match existing project patterns when they are already clean and modern.
- Do not add compatibility code for older Python versions unless explicitly required.

## Style and structure

- Follow PEP 8 and PEP 257.
- Use meaningful names; avoid abbreviations unless they are standard in the domain.
- Use modules and functions before introducing classes.
- Keep nesting shallow; use guard clauses and early returns when they improve clarity.
- Prefer `pathlib.Path` over `os.path`.
- Use f-strings instead of `%` formatting or `str.format()`.
- Use `enum.StrEnum` or `enum.Enum` for constrained string/value sets.
- Use `dataclasses.dataclass(slots=True)` for simple structured data; add `frozen=True` when immutability is appropriate.

## Typing

- Type all public functions, methods, constants, and module-level variables with non-obvious types.
- Use modern typing syntax:
  - `list[str]`, `dict[str, int]`, `set[Path]`
  - `str | None` instead of `Optional[str]`
  - `type[MyClass]` instead of `Type[MyClass]`
- Prefer `collections.abc` for abstract container and callable types.
- Use `typing.Self`, `typing.TypeAlias`, `typing.TypedDict`, `typing.Protocol`, and `typing.Literal` when they improve clarity.
- Prefer explicit domain types over `Any`.
- Avoid unnecessary casts; fix the type flow instead.

## Functions and APIs

- Design APIs to be obvious from the call site.
- Prefer keyword-only arguments for functions with multiple booleans or optional behaviors.
- Avoid boolean flag arguments when separate functions or enums would be clearer.
- Return rich values instead of overloaded sentinel values.
- Document non-obvious behavior in concise docstrings.
- Keep side effects visible in function names and signatures.

## Control flow and data handling

- Prefer comprehensions and generator expressions when they improve readability.
- Use `match` when it makes branching clearer than chained `if`/`elif`.
- Use `itertools`, `functools`, and `collections` instead of handwritten utility code when they simplify the solution.
- Validate external input at boundaries and convert it into well-typed internal data structures early.
- Avoid mutating shared state unless there is a clear reason.

## Error handling

- Raise specific exceptions with actionable messages.
- Do not swallow exceptions silently.
- Catch exceptions only when you can add context, recover, or translate them at a boundary.
- Preserve original tracebacks; use `raise ... from exc` when re-raising with context.
- Prefer structured validation over defensive blanket `try/except` blocks.

## I/O, files, and serialization

- Always use context managers for files, sockets, locks, and similar resources.
- Read and write text files with explicit `encoding="utf-8"` unless another encoding is required.
- Prefer `json` for interoperable serialization; avoid `pickle` for untrusted data.
- Use `tempfile` for temporary files and directories.
- Keep parsing and formatting logic separate from transport code.

## Async and concurrency

- Use `async`/`await` only for real concurrency or I/O-bound workflows.
- Do not mix sync and async APIs awkwardly; keep boundaries explicit.
- Prefer `asyncio.TaskGroup` for coordinating concurrent async tasks.
- Propagate cancellation correctly; do not hide `CancelledError`.
- For CPU-bound work, prefer process-based concurrency when appropriate.

## Logging and observability

- Use the `logging` module instead of `print()` for application diagnostics.
- Create module loggers with `logging.getLogger(__name__)`.
- Log enough context to debug failures, but never log secrets or sensitive data.
- Keep log messages structured and concise.

## Testing mindset

- Write code that is easy to test through clear inputs and outputs.
- Prefer deterministic behavior; inject time, randomness, and external services.
- Test behavior and contracts, not implementation details.
- Cover edge cases, failure paths, and data validation rules.

## Modern Python preferences

- Prefer `tomllib` for reading TOML when possible.
- Use `zoneinfo` for time zones.
- Use `datetime` objects that are timezone-aware for real-world timestamps.
- Prefer `contextlib` helpers over ad hoc resource-management code.
- Use `subprocess.run(..., check=True, text=True)` for simple command execution.
- Prefer `shutil`, `tempfile`, `pathlib`, and `subprocess` over shelling out for basic filesystem tasks.

## Security and reliability

- Never use `eval()` or `exec()` on untrusted input.
- Never build shell commands with unsanitized user data.
- Validate paths, URLs, and file formats from external sources.
- Make failure modes explicit; avoid silent fallbacks that hide bugs.

## When generating or editing code

- Preserve existing behavior unless the task explicitly asks for a change.
- Make surgical changes; do not refactor unrelated code opportunistically.
- Add comments only when the code needs explanation that names and structure cannot provide.
- Prefer deleting dead code over leaving unused branches or helpers behind.
