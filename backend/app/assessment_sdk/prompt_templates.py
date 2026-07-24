"""Reusable prompt template infrastructure (no attack prompts)."""

from __future__ import annotations

from dataclasses import dataclass, field
from string import Formatter
from typing import Any

from app.assessment_sdk.exceptions import ConfigurationError, ValidationError
from app.assessment_sdk.validators import validate_prompt_length


@dataclass(slots=True)
class PromptTemplate:
    """Named prompt template with ``{placeholder}`` substitution.

    This is infrastructure only — it does not embed security-test payloads.
    """

    name: str
    template: str
    description: str = ""
    required_variables: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("PromptTemplate.name is required")
        if not self.template.strip():
            raise ValueError("PromptTemplate.template is required")
        discovered = self.discover_variables(self.template)
        if not self.required_variables:
            self.required_variables = tuple(discovered)

    @staticmethod
    def discover_variables(template: str) -> list[str]:
        names: list[str] = []
        for _, field_name, _, _ in Formatter().parse(template):
            if field_name and field_name not in names:
                names.append(field_name)
        return names

    def render(self, **variables: Any) -> str:
        missing = [name for name in self.required_variables if name not in variables]
        if missing:
            raise ValidationError(
                f"Missing prompt variables: {', '.join(missing)}",
                details={"missing": missing, "template": self.name},
            )
        try:
            rendered = self.template.format(**variables)
        except KeyError as exc:
            raise ValidationError(
                f"Unresolved prompt variable: {exc}",
                details={"template": self.name},
            ) from exc
        return validate_prompt_length(rendered)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "required_variables": list(self.required_variables),
            "metadata": dict(self.metadata),
        }


class PromptTemplateRegistry:
    """In-memory registry of reusable prompt templates."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate, *, replace: bool = False) -> None:
        if template.name in self._templates and not replace:
            raise ConfigurationError(
                f"Prompt template already registered: {template.name!r}",
                details={"name": template.name},
            )
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        try:
            return self._templates[name]
        except KeyError as exc:
            raise ConfigurationError(
                f"Prompt template not found: {name!r}",
                details={"name": name},
            ) from exc

    def render(self, template_name: str, **variables: Any) -> str:
        return self.get(template_name).render(**variables)

    def names(self) -> list[str]:
        return sorted(self._templates)

    def clear(self) -> None:
        self._templates.clear()

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._templates

    def __len__(self) -> int:
        return len(self._templates)
