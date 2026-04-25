from __future__ import annotations


class ConfigValidationError(ValueError):
    """Raised when application configuration is invalid."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Invalid application configuration.")

    def as_dict(self) -> dict[str, object]:
        return {
            "error": "invalid_configuration",
            "message": "Application configuration is invalid.",
            "details": self.errors,
        }

