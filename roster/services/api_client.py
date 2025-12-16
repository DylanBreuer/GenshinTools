"""Helper utilities for pulling data from a community API.

These helpers are intentionally small so the base URL or auth strategy can be
plugged in later without touching the models.
"""
from __future__ import annotations

from dataclasses import dataclass

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
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def fetch_characters(self) -> list[ApiCharacter]:
        response = requests.get(f"{self.base_url}/characters")
        response.raise_for_status()
        payload = response.json()
        return [
            ApiCharacter(
                name=item.get('name', ''),
                element=item.get('element', '').lower(),
                weapon_type=item.get('weapon_type', ''),
                rarity=int(item.get('rarity', 5)),
                description=item.get('description', ''),
            )
            for item in payload
        ]

    def fetch_materials(self) -> list[ApiMaterial]:
        response = requests.get(f"{self.base_url}/materials")
        response.raise_for_status()
        payload = response.json()
        return [
            ApiMaterial(
                name=item.get('name', ''),
                type=item.get('type', 'general'),
                rarity=int(item.get('rarity', 1)),
                source=item.get('source', ''),
            )
            for item in payload
        ]
