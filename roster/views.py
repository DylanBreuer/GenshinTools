from collections import Counter
from typing import Any

from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from .forms import OwnedCharacterForm, TalentProgressForm
from .models import (
    Character,
    CharacterTalent,
    Material,
    OwnedCharacter,
    OwnedMaterialStock,
    TalentProgress,
    aggregate_required_materials,
)


class OwnedCharacterListView(generic.ListView):
    model = OwnedCharacter
    template_name = 'roster/owned_character_list.html'
    context_object_name = 'owned_characters'

    def get_queryset(self):
        return (
            OwnedCharacter.objects.select_related('character', 'chosen_weapon', 'chosen_artifact_set')
            .prefetch_related('character__charactertalent_set')
            .order_by('character__name')
        )


class OwnedCharacterDetailView(generic.DetailView):
    model = OwnedCharacter
    template_name = 'roster/owned_character_detail.html'
    context_object_name = 'owned_character'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        owned_character: OwnedCharacter = context['owned_character']

        talent_prefetch = Prefetch(
            'charactertalent_set', queryset=CharacterTalent.objects.order_by('recommended_priority')
        )
        character = (
            Character.objects.prefetch_related(
                talent_prefetch,
                'characterartifactrecommendation_set__artifact_set',
                'characterweaponrecommendation_set__weapon',
                'charactermaterialrequirement_set__material',
            )
            .get(pk=owned_character.character.pk)
        )
        context['character'] = character

        inventory = Counter({stock.material: stock.quantity_owned for stock in OwnedMaterialStock.objects.all()})
        requirements = owned_character.required_materials()
        missing = Counter({material: max(0, qty - inventory.get(material, 0)) for material, qty in requirements.items()})
        context['material_requirements'] = requirements
        context['material_missing'] = missing
        context['inventory'] = inventory

        context['talent_form'] = TalentProgressForm()
        context['talent_progress'] = TalentProgress.objects.filter(owned_character=owned_character)
        return context


class OwnedCharacterCreateView(generic.CreateView):
    model = OwnedCharacter
    template_name = 'roster/owned_character_form.html'
    form_class = OwnedCharacterForm
    success_url = reverse_lazy('roster:owned-character-list')


class OwnedCharacterUpdateView(generic.UpdateView):
    model = OwnedCharacter
    template_name = 'roster/owned_character_form.html'
    form_class = OwnedCharacterForm
    success_url = reverse_lazy('roster:owned-character-list')


class TalentProgressCreateView(generic.View):
    def post(self, request, *args, **kwargs):
        owned_character = get_object_or_404(OwnedCharacter, pk=kwargs['pk'])
        form = TalentProgressForm(request.POST)
        if form.is_valid():
            talent_progress: TalentProgress = form.save(commit=False)
            talent_progress.owned_character = owned_character
            talent_progress.save()
            messages.success(request, 'Talent progress saved.')
        else:
            messages.error(request, 'Unable to save talent progress.')
        return redirect('roster:owned-character-detail', pk=owned_character.pk)


class MaterialSummaryView(generic.TemplateView):
    template_name = 'roster/material_summary.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        owned_characters = OwnedCharacter.objects.all()
        requirements = aggregate_required_materials(owned_characters)
        inventory = Counter({stock.material: stock.quantity_owned for stock in OwnedMaterialStock.objects.all()})
        missing = Counter({material: max(0, qty - inventory.get(material, 0)) for material, qty in requirements.items()})
        context.update(
            {
                'requirements': requirements,
                'inventory': inventory,
                'missing': missing,
                'materials': Material.objects.all(),
            }
        )
        return context


class MaterialIndexView(generic.ListView):
    model = Material
    template_name = 'roster/material_index.html'
    context_object_name = 'materials'
    paginate_by = 100
    ordering = ['-rarity', 'name']


class RecommendationIndexView(generic.ListView):
    template_name = 'roster/recommendation_index.html'
    context_object_name = 'characters'

    def get_queryset(self):
        return Character.objects.prefetch_related(
            'characterartifactrecommendation_set__artifact_set',
            'characterweaponrecommendation_set__weapon',
            'charactertalent_set',
        ).order_by('name')
