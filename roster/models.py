from __future__ import annotations

from collections import Counter
from typing import Iterable

from django.db import models


class Character(models.Model):
    ELEMENT_CHOICES = [
        ('anemo', 'Anemo'),
        ('geo', 'Geo'),
        ('electro', 'Electro'),
        ('dendro', 'Dendro'),
        ('pyro', 'Pyro'),
        ('hydro', 'Hydro'),
        ('cryo', 'Cryo'),
    ]

    name = models.CharField(max_length=100, unique=True)
    element = models.CharField(max_length=20, choices=ELEMENT_CHOICES)
    rarity = models.PositiveSmallIntegerField(default=5)
    role = models.CharField(max_length=80, blank=True)
    weapon_type = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Weapon(models.Model):
    WEAPON_TYPES = [
        ('sword', 'Sword'),
        ('claymore', 'Claymore'),
        ('polearm', 'Polearm'),
        ('bow', 'Bow'),
        ('catalyst', 'Catalyst'),
    ]

    name = models.CharField(max_length=120, unique=True)
    weapon_type = models.CharField(max_length=30, choices=WEAPON_TYPES)
    rarity = models.PositiveSmallIntegerField(default=4)
    source = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class ArtifactSet(models.Model):
    name = models.CharField(max_length=120, unique=True)
    two_piece_bonus = models.TextField(blank=True)
    four_piece_bonus = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Material(models.Model):
    MATERIAL_TYPES = [
        ('character', 'Character Ascension'),
        ('talent', 'Talent'),
        ('weapon', 'Weapon'),
        ('artifact', 'Artifact'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=120, unique=True)
    material_type = models.CharField(max_length=30, choices=MATERIAL_TYPES)
    rarity = models.PositiveSmallIntegerField(default=1)
    source = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-rarity', 'name']

    def __str__(self) -> str:
        return self.name


class CharacterMaterialRequirement(models.Model):
    class RequirementCategory(models.TextChoices):
        ASCENSION = 'ascension', 'Ascension'
        TALENT = 'talent', 'Talent'
        PASSIVE = 'passive', 'Passive'

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    category = models.CharField(
        max_length=30, choices=RequirementCategory.choices, default=RequirementCategory.ASCENSION
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['character', 'material', 'category']

    def __str__(self) -> str:
        return f"{self.character} - {self.material} ({self.category})"


class CharacterTalent(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    recommended_priority = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['recommended_priority']
        unique_together = ['character', 'name']

    def __str__(self) -> str:
        return f"{self.character} - {self.name}"


class CharacterWeaponRecommendation(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    weapon = models.ForeignKey(Weapon, on_delete=models.CASCADE)
    ranking = models.PositiveSmallIntegerField(default=1)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['ranking']
        unique_together = ['character', 'weapon']

    def __str__(self) -> str:
        return f"{self.character} -> {self.weapon}"


class CharacterArtifactRecommendation(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    artifact_set = models.ForeignKey(ArtifactSet, on_delete=models.CASCADE)
    ranking = models.PositiveSmallIntegerField(default=1)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['ranking']
        unique_together = ['character', 'artifact_set']

    def __str__(self) -> str:
        return f"{self.character} -> {self.artifact_set}"


class OwnedMaterialStock(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity_owned = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Material stock'
        verbose_name_plural = 'Material stock'

    def __str__(self) -> str:
        return f"{self.material}: {self.quantity_owned}"


class OwnedCharacter(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=1)
    ascension_level = models.PositiveSmallIntegerField(default=0)
    constellations_unlocked = models.PositiveSmallIntegerField(default=0)
    chosen_weapon = models.ForeignKey(Weapon, on_delete=models.SET_NULL, null=True, blank=True)
    chosen_artifact_set = models.ForeignKey(
        ArtifactSet, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_choices'
    )
    artifact_plan_notes = models.TextField(blank=True)
    priority_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['character']
        ordering = ['character__name']

    def __str__(self) -> str:
        return f"{self.character} (Lv.{self.level})"

    def required_materials(self) -> Counter:
        requirements = CharacterMaterialRequirement.objects.filter(character=self.character)
        tally: Counter = Counter()
        for req in requirements:
            tally[req.material] += req.quantity
        return tally


class TalentProgress(models.Model):
    owned_character = models.ForeignKey(OwnedCharacter, on_delete=models.CASCADE)
    talent = models.ForeignKey(CharacterTalent, on_delete=models.CASCADE)
    current_level = models.PositiveSmallIntegerField(default=1)
    target_level = models.PositiveSmallIntegerField(default=10)
    skip = models.BooleanField(default=False)

    class Meta:
        unique_together = ['owned_character', 'talent']

    def __str__(self) -> str:
        return f"{self.owned_character} - {self.talent.name}"


def aggregate_required_materials(owned_characters: Iterable[OwnedCharacter]) -> Counter:
    tally: Counter = Counter()
    for owned in owned_characters:
        tally.update(owned.required_materials())
    return tally
