"""Internationalization and message retrieval module."""

import json
from pathlib import Path
from typing import Any


class MessageLoader:
    """Load and retrieve text messages from messages.json."""

    def __init__(self, messages_path: Path | None = None):
        """Initialize message loader."""
        if messages_path is None:
            messages_path = Path(__file__).parent / "messages.json"
        self.messages_path = messages_path
        self.messages: dict[str, Any] = {}
        self.load_messages()

    def load_messages(self) -> None:
        """Load messages from JSON file."""
        with open(self.messages_path, "r", encoding="utf-8") as f:
            self.messages = json.load(f)

    def get(self, key: str, **kwargs: Any) -> str:
        """
        Get message by key with optional formatting.

        Args:
            key: Dot-separated path to message (e.g., "user.welcome", "admin.main_menu")
            **kwargs: Format parameters for the message

        Returns:
            Formatted message string

        Raises:
            KeyError: If message key is not found
        """
        parts = key.split(".")
        value: Any = self.messages

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    raise KeyError(f"Message key not found: {key}")
            else:
                raise KeyError(f"Invalid message path: {key}")

        if not isinstance(value, str):
            raise ValueError(f"Message value must be a string: {key}")

        # Format message with provided parameters
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing format parameter for message '{key}': {e}")

        return value

    def reload(self) -> None:
        """Reload messages from file."""
        self.load_messages()


# Global message loader instance
_message_loader: MessageLoader | None = None


def get_message_loader() -> MessageLoader:
    """Get or create global message loader instance."""
    global _message_loader
    if _message_loader is None:
        _message_loader = MessageLoader()
    return _message_loader


def t(key: str, **kwargs: Any) -> str:
    """
    Convenient shorthand for getting translated/formatted messages.

    Args:
        key: Dot-separated path to message
        **kwargs: Format parameters

    Returns:
        Formatted message string

    Example:
        >>> t("user.welcome")
        "👋 Welcome! To participate..."
        >>> t("user.participation_confirmed", description="Win $100", end_at="2024-05-15")
        "🎉 Success! You are now participating..."
    """
    loader = get_message_loader()
    return loader.get(key, **kwargs)


def init_messages(messages_path: Path | None = None) -> MessageLoader:
    """
    Initialize message loader with custom path.

    Args:
        messages_path: Path to messages.json file

    Returns:
        MessageLoader instance
    """
    global _message_loader
    _message_loader = MessageLoader(messages_path)
    return _message_loader
