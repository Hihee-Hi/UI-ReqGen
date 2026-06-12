import os
from functools import lru_cache
from typing import List, Optional

from openai import OpenAI


DEFAULT_GENERATION_MODEL = "gpt-4o"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required. Set OPENAI_BASE_URL as well if you use "
            "a compatible gateway instead of the default OpenAI endpoint."
        )

    client_kwargs = {"api_key": api_key}
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
) -> str:
    response = get_openai_client().chat.completions.create(
        model=model or os.getenv("UI_REQGEN_GENERATION_MODEL", DEFAULT_GENERATION_MODEL),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def create_embedding(
    text: str,
    model: Optional[str] = None,
) -> List[float]:
    response = get_openai_client().embeddings.create(
        model=model or os.getenv("UI_REQGEN_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        input=text,
        encoding_format="float",
    )
    return response.data[0].embedding
