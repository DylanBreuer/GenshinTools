from django.contrib import admin

from .models import (
    ArtifactSet,
    Character,
    CharacterArtifactRecommendation,
    CharacterMaterialRequirement,
    CharacterTalent,
    CharacterWeaponRecommendation,
    Material,
    OwnedCharacter,
    OwnedMaterialStock,
    TalentProgress,
    Weapon,
)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'element', 'weapon_type', 'rarity')
    search_fields = ('name', 'element', 'weapon_type')


admin.site.register(Weapon)
admin.site.register(ArtifactSet)
admin.site.register(Material)
admin.site.register(CharacterMaterialRequirement)
admin.site.register(CharacterTalent)
admin.site.register(CharacterWeaponRecommendation)
admin.site.register(CharacterArtifactRecommendation)
admin.site.register(OwnedCharacter)
admin.site.register(OwnedMaterialStock)
admin.site.register(TalentProgress)
