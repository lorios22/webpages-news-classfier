import os
from dataclasses import dataclass, field, fields
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from typing_extensions import Annotated

@dataclass
class Configuration:
    """The configurable fields for the research assistant."""
    max_web_research_loops: int = 3
    local_llm: str = "deepseek-r1:8b"

    def __init__(self, **kwargs):
        """Initialize with keyword arguments only."""
        if not kwargs and not self.__class__.__dataclass_fields__:
            raise TypeError("Configuration must be initialized with keyword arguments")
        for k, v in kwargs.items():
            if k not in self.__class__.__dataclass_fields__:
                raise TypeError(f"Unexpected keyword argument: {k}")
            setattr(self, k, v)

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})