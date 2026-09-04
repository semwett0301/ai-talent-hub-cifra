from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from .config import EnvSettings
from .models import HubCandidate, RuntimeSettings, SiteConfig
from .url_utils import host_matches, normalize_url

logger = logging.getLogger(__name__)


class _Hub(BaseModel):
    url: str
    label: str | None = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class _Output(BaseModel):
    hubs: list[_Hub] = Field(default_factory=list)


async def browser_use_find_hubs(site: SiteConfig, settings: RuntimeSettings, env: EnvSettings) -> list[HubCandidate]:
    """Optional last-resort UI navigation. browser-use is intentionally lazy imported."""
    try:
        from browser_use import Agent, Browser, ChatOpenAI
    except ImportError:
        logger.warning("browser-use fallback requested but package is not installed. Install: uv pip install -e '.[browser-fallback]'")
        return []

    token = env.llm_token()
    if not token:
        logger.warning("browser-use fallback requested but no OpenAI-compatible API token is configured")
        return []

    seed = normalize_url(str(site.url))
    kwargs = {"model": env.browser_use_model, "api_key": token}
    if env.llm_base_url():
        kwargs["base_url"] = env.llm_base_url()
    llm = ChatOpenAI(**kwargs)
    browser = Browser(headless=settings.browser_headless, user_agent=settings.user_agent)
    task = f"""
Open {seed}. Find the primary in-domain LISTING pages that contain news, press releases,
media updates, articles, publications, company updates or similar dated editorial content.
Use menus/tabs/buttons if necessary. Return listing/section URLs, not individual articles.
Stay on the same organization/domain. Return at most {settings.browser_max_hubs} hubs.
""".strip()
    try:
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            output_model_schema=_Output,
            use_judge=False,
            max_actions_per_step=4,
        )
        history = await agent.run(max_steps=settings.browser_max_steps)
        value = getattr(history, "structured_output", None)
        if isinstance(value, BaseModel):
            output = _Output.model_validate(value.model_dump())
        elif isinstance(value, dict):
            output = _Output.model_validate(value)
        else:
            raw = history.final_result()
            output = _Output.model_validate_json(raw) if raw else _Output()
        out: dict[str, HubCandidate] = {}
        for item in output.hubs:
            url = normalize_url(item.url, base=seed)
            if not url or not host_matches(url, site.allowed_domains, seed):
                continue
            out[url] = HubCandidate(
                url=url,
                score=item.confidence,
                title=item.label,
                source="browser_use",
            )
        return sorted(out.values(), key=lambda x: x.score, reverse=True)
    except Exception:
        logger.exception("Browser Use discovery fallback failed for %s", seed)
        return []
    finally:
        try:
            await browser.kill()
        except Exception:
            pass
