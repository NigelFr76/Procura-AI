"""Provider-agnostic LLM interface with structured outputs and fallback simulation."""

from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.agents.llm_provider")

T = TypeVar("T", bound=BaseModel)


class LLMProvider:
    """Manages chat model initialization and structured schema generation."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.model_name = model_name or settings.DEFAULT_MODEL_NAME
        self.temperature = temperature
        self._llm: Optional[BaseChatModel] = None

    def get_llm(self) -> Optional[BaseChatModel]:
        """Obtain configured LangChain chat model."""
        if self._llm is not None:
            return self._llm

        if self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    api_key=settings.OPENAI_API_KEY,
                )
                return self._llm
            except Exception as e:
                logger.warning("Failed to initialize ChatOpenAI: %s. Using fallback mode.", e)
                return None
        return None

    def generate_structured(
        self,
        messages: list[BaseMessage],
        response_model: Type[T],
        fallback_factory: Optional[callable] = None,
    ) -> T:
        """Generate validated Pydantic model response from LLM with automatic fallback."""
        llm = self.get_llm()
        if llm is not None:
            try:
                structured_llm = llm.with_structured_output(response_model)
                result = structured_llm.invoke(messages)
                if isinstance(result, response_model):
                    return result
                elif isinstance(result, dict):
                    return response_model.model_validate(result)
            except Exception as e:
                logger.error("LLM structured output failed: %s. Invoking fallback if available.", e)
                if fallback_factory is None:
                    raise

        if fallback_factory is not None:
            return fallback_factory()

        raise RuntimeError(
            f"No live LLM key configured for provider '{self.provider}' and no fallback factory provided."
        )


# Global singleton
llm_provider = LLMProvider()
