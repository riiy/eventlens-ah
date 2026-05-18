from app.core.config import settings
from app.llm.openai_compatible_provider import OpenAICompatibleProvider


class Gemma4Provider(OpenAICompatibleProvider):
    """Gemma4 provider via an OpenAI-compatible API endpoint."""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        resolved_model_name = model_name or settings.GEMMA4_MODEL_NAME
        super().__init__(
            model_name=resolved_model_name,
            api_key=api_key or settings.GEMMA4_API_KEY,
            base_url=base_url or settings.GEMMA4_BASE_URL,
            missing_api_key_message=(
                "GEMMA4_API_KEY is not configured. Set GEMMA4_API_KEY in backend/.env."
            ),
        )
