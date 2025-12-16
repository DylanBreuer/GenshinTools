from django import forms

from .models import OwnedCharacter, TalentProgress


class OwnedCharacterForm(forms.ModelForm):
    class Meta:
        model = OwnedCharacter
        fields = [
            'character',
            'level',
            'ascension_level',
            'constellations_unlocked',
            'chosen_weapon',
            'chosen_artifact_set',
            'artifact_plan_notes',
            'priority_notes',
        ]


class TalentProgressForm(forms.ModelForm):
    class Meta:
        model = TalentProgress
        fields = ['talent', 'current_level', 'target_level', 'skip']
