"""Helper utilities for pulling data from a community API.

These helpers are intentionally small so the base URL or auth strategy can be
plugged in later without touching the models.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ApiCharacter:
    name: str
    element: str
    weapon_type: str
    rarity: int
    description: str


@dataclass
class ApiMaterial:
    name: str
    type: str
    rarity: int
    source: str


class GenshinApiClient:
    """Lightweight wrapper around https://genshin.jmp.blue/ ("genshin blue")."""

    DEFAULT_BASE_URL = "https://genshin.jmp.blue"

    def __init__(self, base_url: str | None = None, session: requests.Session | None = None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.session = session or requests.Session()

    def _get_json(self, path: str) -> Any:
        response = self.session.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

    def fetch_characters(self) -> list[ApiCharacter]:
        """Fetch all characters from genshin.blue.

        The API returns a list of character slugs. Each slug is resolved to a full
        payload that contains the vision/weapon/rarity fields we need.
        """

        slugs = self._get_json("/characters")
        characters: list[ApiCharacter] = []

        for slug in slugs:
            detail = self._get_json(f"/characters/{slug}")
            characters.append(
                ApiCharacter(
                    name=detail.get("name") or slug.replace("-", " ").title(),
                    element=(detail.get("vision") or detail.get("element") or "").lower(),
                    weapon_type=(detail.get("weapon") or detail.get("weapon_type") or "").lower(),
                    rarity=int(detail.get("rarity", 5)),
                    description=detail.get("description", ""),
                )
            )

        return characters

    def fetch_materials(self) -> list[ApiMaterial]:
        """Fetch materials across all categories exposed by genshin.blue."""

        categories = self._get_json("/materials")
        materials: list[ApiMaterial] = []

        def category_key_to_type(category: str) -> str:
            mapping = {
                "character-ascension": "character",
                "talent": "talent",
                "weapon": "weapon",
                "common-ascension": "general",
                "local-specialties": "character",
                "weekly-boss": "talent",
                "boss": "character",
            }
            return mapping.get(category, "general")

        for category in categories:
            items = self._get_json(f"/materials/{category}")
            if isinstance(items, dict):
                # Newer versions return {slug: {detail}}
                iterable = items.items()
            else:
                iterable = [(slug, self._get_json(f"/materials/{category}/{slug}")) for slug in items]

            for slug, detail in iterable:
                materials.append(
                    ApiMaterial(
                        name=detail.get("name") or slug.replace("-", " ").title(),
                        type=category_key_to_type(category),
                        rarity=int(detail.get("rarity", 1)),
                        source=", ".join(detail.get("source", []) if isinstance(detail.get("source"), list) else detail.get("source", "")),
                    )
                )

        return materials
