from django.core.management.base import BaseCommand

from roster.models import (
    ArtifactSet,
    Character,
    CharacterArtifactRecommendation,
    CharacterMaterialRequirement,
    CharacterTalent,
    CharacterWeaponRecommendation,
    Material,
    Weapon,
)


class Command(BaseCommand):
    help = 'Seed the database with example characters, materials, and recommendations.'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample characters...')
        amber, _ = Character.objects.get_or_create(
            name='Amber', element='pyro', weapon_type='bow', rarity=4, role='Bow DPS'
        )
        xiangling, _ = Character.objects.get_or_create(
            name='Xiangling', element='pyro', weapon_type='polearm', rarity=4, role='Off-field DPS'
        )

        skyward, _ = Weapon.objects.get_or_create(name='Skyward Harp', weapon_type='bow', rarity=5)
        favonius, _ = Weapon.objects.get_or_create(name='Favonius Lance', weapon_type='polearm', rarity=4)

        crimson, _ = ArtifactSet.objects.get_or_create(
            name='Crimson Witch of Flames',
            two_piece_bonus='+15% Pyro DMG Bonus',
            four_piece_bonus='Pyro DMG bonus increases after using Elemental Skill',
        )
        emblems, _ = ArtifactSet.objects.get_or_create(
            name='Emblem of Severed Fate',
            two_piece_bonus='+20% Energy Recharge',
            four_piece_bonus='Burst DMG increases with Energy Recharge',
        )

        self.stdout.write('Creating materials...')
        pyro_regisvine, _ = Material.objects.get_or_create(
            name='Agnidus Agate Chunk', material_type='character', rarity=4, source='Pyro Regisvine'
        )
        hilichurl_arrow, _ = Material.objects.get_or_create(
            name='Firm Arrowhead', material_type='talent', rarity=2, source='Hilichurls'
        )
        everflame, _ = Material.objects.get_or_create(
            name='Everflame Seed', material_type='character', rarity=4, source='Pyro Regisvine'
        )

        CharacterMaterialRequirement.objects.get_or_create(
            character=amber,
            material=pyro_regisvine,
            quantity=9,
            category=CharacterMaterialRequirement.RequirementCategory.ASCENSION,
        )
        CharacterMaterialRequirement.objects.get_or_create(
            character=amber,
            material=hilichurl_arrow,
            quantity=36,
            category=CharacterMaterialRequirement.RequirementCategory.TALENT,
        )
        CharacterMaterialRequirement.objects.get_or_create(
            character=xiangling,
            material=everflame,
            quantity=6,
            category=CharacterMaterialRequirement.RequirementCategory.ASCENSION,
        )

        CharacterTalent.objects.get_or_create(character=amber, name='Normal Attack: Sharpshooter', recommended_priority=3)
        CharacterTalent.objects.get_or_create(character=amber, name='Explosive Puppet', recommended_priority=2)
        CharacterTalent.objects.get_or_create(character=amber, name='Fiery Rain', recommended_priority=1)
        CharacterTalent.objects.get_or_create(character=xiangling, name='Dough-Fu', recommended_priority=2)
        CharacterTalent.objects.get_or_create(character=xiangling, name='Guoba Attack', recommended_priority=3)
        CharacterTalent.objects.get_or_create(character=xiangling, name='Pyronado', recommended_priority=1)

        CharacterWeaponRecommendation.objects.get_or_create(character=amber, weapon=skyward, ranking=1)
        CharacterWeaponRecommendation.objects.get_or_create(character=xiangling, weapon=favonius, ranking=2)

        CharacterArtifactRecommendation.objects.get_or_create(character=amber, artifact_set=crimson, ranking=1)
        CharacterArtifactRecommendation.objects.get_or_create(character=xiangling, artifact_set=emblems, ranking=1)

        self.stdout.write(self.style.SUCCESS('Sample data loaded.'))
