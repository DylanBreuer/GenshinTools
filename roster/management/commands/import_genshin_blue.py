from django.core.management.base import BaseCommand

from roster.models import (
    ArtifactSet,
    Character,
    CharacterArtifactRecommendation,
    CharacterTalent,
    CharacterWeaponRecommendation,
    Material,
    Weapon,
)
from roster.services.api_client import GenshinApiClient


class Command(BaseCommand):
    help = "Import characters, materials, weapons and build data from genshin.blue (genshin.jmp.blue)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            dest="base_url",
            default=None,
            help="Override the genshin.blue base URL (defaults to https://genshin.jmp.blue).",
        )

    def handle(self, *args, **options):
        client = GenshinApiClient(base_url=options.get("base_url"))

        self.stdout.write("Fetching characters from genshin.blue…")
        characters = client.fetch_characters()

        created_chars = 0
        for character in characters:
            _, created = Character.objects.update_or_create(
                name=character.name,
                defaults={
                    "element": character.element,
                    "weapon_type": character.weapon_type,
                    "rarity": character.rarity,
                    "description": character.description,
                },
            )
            created_chars += int(created)

        self.stdout.write(self.style.SUCCESS(f"Saved {len(characters)} characters ({created_chars} new)."))

        self.stdout.write("Fetching materials from genshin.blue…")
        materials = client.fetch_materials()

        created_materials = 0
        for material in materials:
            _, created = Material.objects.update_or_create(
                name=material.name,
                defaults={
                    "material_type": material.type,
                    "rarity": material.rarity,
                    "source": material.source,
                },
            )
            created_materials += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Saved {len(materials)} materials ({created_materials} new). Base URL: {client.base_url}"
            )
        )

        self.stdout.write("Fetching weapons from genshin.blue…")
        weapons = client.fetch_weapons()
        created_weapons = 0
        weapon_map: dict[str, Weapon] = {}
        for weapon in weapons:
            obj, created = Weapon.objects.update_or_create(
                name=weapon.name,
                defaults={
                    "weapon_type": weapon.weapon_type,
                    "rarity": weapon.rarity,
                    "source": weapon.source,
                    "description": weapon.description,
                },
            )
            weapon_map[obj.name.lower()] = obj
            created_weapons += int(created)

        self.stdout.write(
            self.style.SUCCESS(f"Saved {len(weapons)} weapons ({created_weapons} new). Base URL: {client.base_url}")
        )

        self.stdout.write("Fetching artifact sets from genshin.blue…")
        artifact_sets = client.fetch_artifacts()
        created_artifacts = 0
        artifact_map: dict[str, ArtifactSet] = {}
        for artifact in artifact_sets:
            obj, created = ArtifactSet.objects.update_or_create(
                name=artifact.name,
                defaults={
                    "two_piece_bonus": artifact.two_piece_bonus,
                    "four_piece_bonus": artifact.four_piece_bonus,
                },
            )
            artifact_map[obj.name.lower()] = obj
            created_artifacts += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Saved {len(artifact_sets)} artifact sets ({created_artifacts} new). Base URL: {client.base_url}"
            )
        )

        self.stdout.write("Saving build data (talents, weapons, artifacts) for characters…")
        for payload in characters:
            character = Character.objects.get(name=payload.name)

            for talent in payload.talents:
                CharacterTalent.objects.update_or_create(
                    character=character,
                    name=talent.name,
                    defaults={
                        "description": talent.description,
                        "recommended_priority": talent.priority,
                    },
                )

            for rec in payload.weapon_recommendations:
                weapon = weapon_map.get(rec.name.lower())
                if weapon is None:
                    weapon, _ = Weapon.objects.update_or_create(
                        name=rec.name,
                        defaults={
                            "weapon_type": payload.weapon_type,
                            "rarity": 4,
                            "source": "",
                        },
                    )
                    weapon_map[weapon.name.lower()] = weapon

                CharacterWeaponRecommendation.objects.update_or_create(
                    character=character,
                    weapon=weapon,
                    defaults={"ranking": rec.ranking},
                )

            for rec in payload.artifact_recommendations:
                artifact_set = artifact_map.get(rec.name.lower())
                if artifact_set is None:
                    artifact_set, _ = ArtifactSet.objects.update_or_create(
                        name=rec.name,
                        defaults={"two_piece_bonus": "", "four_piece_bonus": ""},
                    )
                    artifact_map[artifact_set.name.lower()] = artifact_set

                CharacterArtifactRecommendation.objects.update_or_create(
                    character=character,
                    artifact_set=artifact_set,
                    defaults={"ranking": rec.ranking},
                )
