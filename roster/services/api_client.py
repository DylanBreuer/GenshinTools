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
class ApiTalent:
    name: str
    description: str = ""
    priority: int = 1


@dataclass
class ApiRecommendation:
    name: str
    ranking: int = 1


@dataclass
class ApiMaterial:
    name: str
    type: str
    rarity: int
    source: str


@dataclass
class ApiWeapon:
    name: str
    weapon_type: str
    rarity: int
    source: str
    description: str = ""


@dataclass
class ApiArtifactSet:
    name: str
    two_piece_bonus: str
    four_piece_bonus: str


@dataclass
class ApiCharacterPayload(ApiCharacter):
    talents: list[ApiTalent]
    weapon_recommendations: list[ApiRecommendation]
    artifact_recommendations: list[ApiRecommendation]


class GenshinApiClient:
    """Lightweight wrapper around https://genshin.dev."""

    DEFAULT_BASE_URL = "https://genshin.dev"
    DEFAULT_LANGUAGE = "fr"

    def __init__(
        self,
        base_url: str | None = None,
        *,
        language: str | None = None,
        session: requests.Session | None = None,
    ):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.language = (language or self.DEFAULT_LANGUAGE).lower()
        self.session = session or requests.Session()

    def _get_json(self, path: str) -> Any:
        response = self.session.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

    def fetch_characters(self) -> list[ApiCharacterPayload]:
        """Fetch all characters and their related build data from genshin.dev."""

        slugs = self._get_json("/characters")
        if isinstance(slugs, dict):
            slugs = list(slugs.keys())
        if not isinstance(slugs, list):
            slugs = []
        characters: list[ApiCharacterPayload] = []

        def normalize_recommendations(raw: Any) -> list[ApiRecommendation]:
            entries: list[ApiRecommendation] = []
            if isinstance(raw, dict):
                for idx, key in enumerate(raw):
                    name = raw.get(key) if isinstance(raw.get(key), str) else key
                    if name:
                        entries.append(ApiRecommendation(str(name), ranking=idx + 1))
            elif isinstance(raw, list):
                for idx, item in enumerate(raw):
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("title") or item.get("weapon")
                    else:
                        name = item
                    if name:
                        entries.append(ApiRecommendation(str(name), ranking=idx + 1))
            elif isinstance(raw, str):
                entries.append(ApiRecommendation(raw, ranking=1))
            return entries

        def normalize_talents(detail: dict[str, Any]) -> list[ApiTalent]:
            talents: list[ApiTalent] = []
            raw_talents = detail.get("talents") or detail.get("skills") or []
            priority_lookup: dict[str, int] = {}
            raw_priority = detail.get("talent_priority") or detail.get("priority") or []
            if isinstance(raw_priority, list):
                for idx, name in enumerate(raw_priority):
                    if isinstance(name, str):
                        priority_lookup[name.lower()] = idx + 1

            if isinstance(raw_talents, dict):
                raw_talents = raw_talents.values()

            if isinstance(raw_talents, list) or isinstance(raw_talents, tuple):
                iterable = raw_talents
            else:
                iterable = []

            for idx, talent in enumerate(iterable):
                if isinstance(talent, dict):
                    name = talent.get("name") or talent.get("title")
                    description = talent.get("description") or talent.get("info") or ""
                else:
                    name, description = str(talent), ""
                if not name:
                    continue
                priority = priority_lookup.get(name.lower(), idx + 1)
                talents.append(ApiTalent(name=str(name), description=str(description), priority=priority))

            return talents

        for slug in slugs:
            detail = self._get_json(f"/characters/{slug}?lang={self.language}")
            base_name = detail.get("name") or slug.replace("-", " ").title()
            characters.append(
                ApiCharacterPayload(
                    name=base_name,
                    element=(detail.get("vision") or detail.get("element") or "").lower(),
                    weapon_type=(detail.get("weapon") or detail.get("weapon_type") or "").lower(),
                    rarity=int(detail.get("rarity", 5)),
                    description=detail.get("description", ""),
                    talents=normalize_talents(detail),
                    weapon_recommendations=normalize_recommendations(
                        detail.get("recommended_weapons")
                        or detail.get("best_weapons")
                        or detail.get("weapons")
                        or detail.get("weapon_recommendations")
                        or []
                    ),
                    artifact_recommendations=normalize_recommendations(
                        detail.get("recommended_artifacts")
                        or detail.get("artifacts")
                        or detail.get("artifact_recommendations")
                        or detail.get("recommended_sets")
                        or []
                    ),
                )
            )

        return characters

    def fetch_materials(self) -> list[ApiMaterial]:
        """Fetch all materials from genshin.dev (detailed)."""

        payload = self._get_json(f"/materials/all?lang={self.language}")
        materials: list[ApiMaterial] = []

        if isinstance(payload, dict):
            items = payload.values()
        elif isinstance(payload, list):
            items = payload
        else:
            items = []

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

        for item in items:
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

    def fetch_weapons(self) -> list[ApiWeapon]:
        """Fetch weapon catalogue (either detailed list or slug list)."""

        payload = self._get_json(f"/weapons?lang={self.language}")
        weapons: list[ApiWeapon] = []

        def build_weapon(slug: str, item: dict[str, Any]) -> ApiWeapon:
            return ApiWeapon(
                name=item.get("name") or slug.replace("-", " ").title(),
                weapon_type=(item.get("type") or item.get("weapon_type") or item.get("weapon") or "").lower(),
                rarity=int(item.get("rarity", 4) or 4),
                source=str(item.get("source") or item.get("obtain") or ""),
                description=str(item.get("description", "")),
            )

        if isinstance(payload, list):
            # either list of slugs or list of dicts
            for entry in payload:
                if isinstance(entry, str):
                    detail = self._get_json(f"/weapons/{entry}?lang={self.language}")
                    weapons.append(build_weapon(entry, detail if isinstance(detail, dict) else {}))
                elif isinstance(entry, dict):
                    slug = str(entry.get("name") or entry.get("id") or entry.get("slug") or "")
                    weapons.append(build_weapon(slug, entry))
        elif isinstance(payload, dict):
            for slug, info in payload.items():
                if isinstance(info, dict):
                    weapons.append(build_weapon(str(slug), info))

        return weapons

    def fetch_artifacts(self) -> list[ApiArtifactSet]:
        """Fetch artifact sets (2-piece and 4-piece bonuses)."""

        payload = self._get_json(f"/artifacts?lang={self.language}")
        artifacts: list[ApiArtifactSet] = []

        def build_set(slug: str, item: dict[str, Any]) -> ApiArtifactSet:
            return ApiArtifactSet(
                name=item.get("name") or slug.replace("-", " ").title(),
                two_piece_bonus=str(
                    item.get("2pc")
                    or item.get("two_pc")
                    or item.get("two_piece_bonus")
                    or item.get("2_piece_bonus")
                    or ""
                ),
                four_piece_bonus=str(
                    item.get("4pc")
                    or item.get("four_pc")
                    or item.get("four_piece_bonus")
                    or item.get("4_piece_bonus")
                    or ""
                ),
            )

        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, str):
                    detail = self._get_json(f"/artifacts/{entry}?lang={self.language}")
                    artifacts.append(build_set(entry, detail if isinstance(detail, dict) else {}))
                elif isinstance(entry, dict):
                    slug = str(entry.get("name") or entry.get("id") or entry.get("slug") or "")
                    artifacts.append(build_set(slug, entry))
        elif isinstance(payload, dict):
            for slug, info in payload.items():
                if isinstance(info, dict):
                    artifacts.append(build_set(str(slug), info))

        return artifacts

