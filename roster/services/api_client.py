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
    """Lightweight wrapper around https://genshin.jmp.blue/ ("genshin blue")."""

    DEFAULT_BASE_URL = "https://genshin.jmp.blue"

    def __init__(self, base_url: str | None = None, session: requests.Session | None = None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.session = session or requests.Session()

    def _get_json(self, path: str) -> Any:
        response = self.session.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

    def fetch_characters(self) -> list[ApiCharacterPayload]:
        """Fetch all characters and their related build data from genshin.blue."""

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
            detail = self._get_json(f"/characters/{slug}")
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
        categories = self._get_json("/materials")
        if isinstance(categories, dict):
            categories = list(categories.keys())
        if not isinstance(categories, list):
            categories = []

        materials: list[ApiMaterial] = []

        def extract_sources(item: dict[str, Any]) -> str:
            """
            Normalize all possible 'source' fields across categories into one string,
            including inherited sources, local-specialties regions, and talent-boss bosses.
            """

            path = item.get("_path", "")

            # --------------------------------------------------
            # 🎯 talent-boss → source = boss hebdomadaire (mapping)
            # --------------------------------------------------
            TALENT_BOSS_SOURCE_BY_KEYWORD = {
                "boreas": "Andrius, Dominator of Wolves",
                "dvalin": "Stormterror",
                "monoceros": "Childe (Tartaglia)",
                "foul-legacy": "Childe (Tartaglia)",
                "azhdaha": "Azhdaha",
                "raiden": "Magatsu Mitake Narukami no Mikoto",
                "puppet": "Everlasting Lord of Arcane Wisdom",
                "mushin": "Everlasting Lord of Arcane Wisdom",
                "calamitous-god": "Shouki no Kami",
                "aeons": "Shouki no Kami",
                "lightless": "All-Devouring Narwhal",
                "fading-candle": "The Knave",
                "denial-and-judgment": "The Knave",
            }

            if path:
                for key, boss in TALENT_BOSS_SOURCE_BY_KEYWORD.items():
                    if key in path:
                        return boss

            # --------------------------------------------------
            # 🌍 local-specialties → source = région
            # --------------------------------------------------
            if path:
                region = path.split("/")[0]
                if region in {
                    "mondstadt",
                    "liyue",
                    "inazuma",
                    "sumeru",
                    "fontaine",
                    "natlan",
                }:
                    return region.capitalize()

            # --------------------------------------------------
            # 🔁 sources directes / héritées
            # --------------------------------------------------
            candidates = [
                item.get("source"),
                item.get("sources"),
                item.get("_inherited_sources"),
                item.get("obtain"),
                item.get("obtainedFrom"),
                item.get("domain"),
                item.get("dropDomain"),
                item.get("location"),
                item.get("region"),
            ]

            def norm(v: Any) -> list[str]:
                if isinstance(v, str) and v.strip():
                    return [v.strip()]
                if isinstance(v, list):
                    return [x.strip() for x in v if isinstance(x, str) and x.strip()]
                return []

            parts: list[str] = []
            for c in candidates:
                parts.extend(norm(c))

            # dédoublonnage en conservant l'ordre
            seen = set()
            unique: list[str] = []
            for p in parts:
                if p not in seen:
                    seen.add(p)
                    unique.append(p)

            return ", ".join(unique)


        def extract_items_from_category_payload(payload: Any) -> list[dict[str, Any]]:
            items: list[dict[str, Any]] = []

            def looks_like_item(d: dict[str, Any]) -> bool:
                if not isinstance(d.get("name"), str) or not d["name"].strip():
                    return False
                return any(k in d for k in ("id", "rarity", "experience", "characters"))

            def get_sources_from_node(node: Any) -> list[str]:
                if not isinstance(node, dict):
                    return []
                raw = node.get("sources") or node.get("source")
                if isinstance(raw, str) and raw.strip():
                    return [raw.strip()]
                if isinstance(raw, list):
                    return [s.strip() for s in raw if isinstance(s, str) and s.strip()]
                return []

            def walk(node: Any, path: tuple[str, ...] = (), inherited_sources: list[str] | None = None) -> None:
                inherited_sources = inherited_sources or []

                if isinstance(node, dict):
                    # hériter des sources si ce niveau en définit
                    local_sources = inherited_sources + get_sources_from_node(node)

                    # clé parasite
                    if "id" in node and isinstance(node["id"], str) and len(node) <= 2 and "items" in node:
                        # cas typique: {"items":[...], "id":"weapon-experience"}
                        pass

                    if looks_like_item(node):
                        # on copie pour ne pas modifier l'objet original (évite des effets de bord)
                        clean = dict(node)
                        clean["_path"] = "/".join(path)
                        if local_sources:
                            clean["_inherited_sources"] = local_sources
                        items.append(clean)

                    for k, v in node.items():
                        # ignore uniquement la clé parasite "id" des wrappers simples
                        if k == "id" and isinstance(v, str) and len(node) <= 2:
                            continue
                        walk(v, path + (str(k),), local_sources)

                elif isinstance(node, list):
                    for idx, v in enumerate(node):
                        walk(v, path + (str(idx),), inherited_sources)

            walk(payload)
            return items


        for category in categories:
            payload = self._get_json(f"/materials/{category}")

            if isinstance(payload, list):
                items: list[dict[str, Any]] = []
                for slug in [s for s in payload if isinstance(s, str)]:
                    detail = self._get_json(f"/materials/{category}/{slug}")
                    if isinstance(detail, dict) and detail.get("name"):
                        items.append(detail)
            else:
                items = extract_items_from_category_payload(payload)

            print(f"{category} : {len(items)}")

            for item in items:
                name = item.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue

                try:
                    rarity = int(item.get("rarity", 1) or 1)
                except (TypeError, ValueError):
                    rarity = 1

                materials.append(
                    ApiMaterial(
                        name=name.strip(),
                        type=category,
                        rarity=rarity,
                        # ✅ ici la modif
                        source=extract_sources(item),
                    )
                )

        return materials

    def fetch_weapons(self) -> list[ApiWeapon]:
        """Fetch weapon catalogue (either detailed list or slug list)."""

        payload = self._get_json("/weapons?lang=en")
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
                    detail = self._get_json(f"/weapons/{entry}?lang=en")
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

        payload = self._get_json("/artifacts?lang=en")
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
                    detail = self._get_json(f"/artifacts/{entry}?lang=en")
                    artifacts.append(build_set(entry, detail if isinstance(detail, dict) else {}))
                elif isinstance(entry, dict):
                    slug = str(entry.get("name") or entry.get("id") or entry.get("slug") or "")
                    artifacts.append(build_set(slug, entry))
        elif isinstance(payload, dict):
            for slug, info in payload.items():
                if isinstance(info, dict):
                    artifacts.append(build_set(str(slug), info))

        return artifacts

