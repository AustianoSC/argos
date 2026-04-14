import logging

from langchain_openai import ChatOpenAI

from argos.config import settings

logger = logging.getLogger(__name__)


def get_match_llm() -> ChatOpenAI:
    """LLM for product matching — higher accuracy needed."""
    return ChatOpenAI(
        model=settings.match_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_api_key,
        temperature=0,
        max_tokens=500,
    )


def get_extract_llm() -> ChatOpenAI:
    """LLM for price extraction — high volume, lower cost."""
    return ChatOpenAI(
        model=settings.extract_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_api_key,
        temperature=0,
        max_tokens=300,
    )
