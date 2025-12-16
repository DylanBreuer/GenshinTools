from django.core.management.base import BaseCommand

from roster.models import Character, Material
from roster.services.api_client import GenshinApiClient


class Command(BaseCommand):
    help = "Import characters and materials from the public genshin.blue API (genshin.jmp.blue)."

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
