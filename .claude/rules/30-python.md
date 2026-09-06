# Python Guidelines

## Core Principles

- Follow PEP 8; use ruff for formatting and linting
- Type annotations: all public function parameters and return values must have type annotations
- Use `pathlib.Path` instead of `os.path`
- Use f-strings instead of `format()` and `%`

## Naming

- Classes: `PascalCase` (`UserService`, `DataProcessor`)
- Functions and variables: `snake_case` (`get_user_by_id`, `is_valid`)
- Constants: `UPPER_SNAKE_CASE` (`MAX_RETRY_COUNT`)
- **Prefer the narrowest visibility a member can have.** Inside a class:
  - **Private** (internal-only helpers and state not meant to be overridden or touched
    by subclasses): double-underscore prefix `__detect_type`, `__client`. Use this
    wherever a member is purely internal — which is most of them. A helper that never
    touches `self` is not one of them (see *Private helpers are functions, not methods*).
  - **Protected** (a subclass legitimately relies on it): single-underscore prefix
    `_method`. Use only when subclass access is actually intended.
  - **Public** (the type's API — e.g. a port's methods): no prefix.
- Module-level privates use a **single** underscore (`_helper`); name mangling only
  applies to class attributes, so `__` is meaningless at module scope.

## Type Annotations

```python
# 禁止
def process(data, config):
    ...

# 正确
def process(data: list[dict[str, Any]], config: ProcessConfig) -> ProcessResult:
    ...
```

- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Use `list[str]` instead of `List[str]` (Python 3.9+)
- Use `TypeAlias` or `TypedDict` for complex types
- Use `Protocol` to define structural subtypes instead of ABCs

## Error Handling

- Catch specific exceptions; no bare `except:` or `except Exception:`
- Custom business exceptions should inherit from a specific built-in exception class
- Use `raise ... from e` to preserve the exception chain

```python
# 禁止
try:
    result = call_api()
except:
    pass

# 正确
try:
    result = call_api()
except httpx.TimeoutException as e:
    raise ServiceUnavailableError(f"API timeout: {e.url}") from e
```

## Async

- Use `async/await` for asynchronous code; do not mix threads and coroutines
- Use `asyncio.TaskGroup` for concurrent execution (Python 3.11+)
- Use `contextlib.asynccontextmanager` to manage async resources

## Data Classes

- Use `dataclass` or `pydantic.BaseModel` for simple data containers
- Use `@dataclass(frozen=True)` for immutable data
- Use `pydantic.BaseSettings` for configuration objects

## Module Organization

- **One public class per module.** A file defines a single top-level class; name the
  module after it in `snake_case` (`SourceRepo` → `source_repo.py`,
  `RabbitConnector` → `connector.py` inside a `rabbit/` package). Splitting a
  multi-class file into a package is preferred over letting it grow.
- When an enclosing package already names the noun, the module drops the redundant
  prefix: `dto/source/create.py` (holds `SourceCreate`), not `source_create.py`.
- **Expose the package's public API from `__init__.py`** by re-exporting the classes
  (`from .connector import RabbitConnector`) with an explicit `__all__`, so callers
  import from the package (`from source_service.infra.rabbit import RabbitConnector`),
  not deep modules. Sibling modules inside the package import each other directly
  (`from ...pull_collector import PullCollector`), not via the package, to avoid
  import cycles.
- Allowed exceptions (do not over-split): a private helper class used by exactly one
  public class (e.g. `_Row`) may share its file; a module holding only related
  enums or constants is fine.

## Private helpers are functions, not methods

- **A helper that does not touch `self` is not a method.** Move it to module level, above
  the class (`10-core` → File layout: constants → free utilities → the class), and give it
  a single-underscore name (`_link_fields`).
- **`@staticmethod` on a private helper is the smell this rule removes.** It is already a
  free function; keeping it in the class body only hides it from direct import and testing,
  and makes the class look bigger than the behaviour it actually owns.
- A method stays a method when it **reads or writes instance state**, or when it is part of
  the type's public API. `SourceService.__detect_type` uses `self._page_fetcher`, so it
  stays; `_link_fields` and `_check_relevance` take everything they need as arguments, so
  they do not.
- Do not thread an injected collaborator through a free function just to empty the class —
  that trades one clear dependency for an extra parameter at every call site.
- Name mangling is a class-attribute feature: outside a class use one underscore, never two.

## Project Structure

- Use `pyproject.toml` for project configuration (not `setup.py`)
- Use pytest for testing; place configuration in `[tool.pytest]` within `pyproject.toml`
- Use `uv` or `poetry` for dependency management
