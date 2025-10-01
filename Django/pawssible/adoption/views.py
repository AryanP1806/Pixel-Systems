from django.shortcuts import render, redirect, get_object_or_404
from .models import AdoptablePet
from .forms import AdoptionRequestForm
from django.contrib.auth.decorators import login_required

def available_pets(request):
    pets = AdoptablePet.objects.filter(available=True)
    return render(request, 'adoption/list.html', {'pets': pets})

@login_required
def adopt_pet(request, pet_id):
    pet = get_object_or_404(AdoptablePet, id=pet_id)
    if request.method == 'POST':
        form = AdoptionRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.user = request.user
            request_obj.pet = pet
            request_obj.save()
            return redirect('adoption:list')
    else:
        form = AdoptionRequestForm()
    return render(request, 'adoption/adopt.html', {'form': form, 'pet': pet})
