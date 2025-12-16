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
        """Fetch all materials from genshin.blue (detailed)."""

        payload = self._get_json("/materials/all?lang=en")
        materials: list[ApiMaterial] = []

        def normalize_source(value: Any) -> str:
            if isinstance(value, list):
                return ", ".join(str(v) for v in value if v)
            if isinstance(value, str):
                return value
            return ""

        def normalize_type(item: dict[str, Any]) -> str:
            # Selon les données, tu peux avoir "type"/"category"/"material_type"
            raw = (item.get("type") or item.get("category") or item.get("material_type") or "").lower()
            # Garde ta logique si tu veux regrouper en 3 grands types
            if "weapon" in raw:
                return "weapon"
            if "talent" in raw:
                return "talent"
            if "character" in raw or "ascension" in raw or "boss" in raw or "local" in raw:
                return "character"
            return "general"

        for item in payload:
            if not isinstance(item, dict):
                continue

            name = item.get("name") or ""
            if not name:
                continue

            materials.append(
                ApiMaterial(
                    name=name,
                    type=normalize_type(item),
                    rarity=int(item.get("rarity", 1) or 1),
                    source=normalize_source(item.get("source")),
                )
            )

        return materials

