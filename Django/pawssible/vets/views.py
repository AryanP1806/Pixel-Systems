from django.shortcuts import render
from .models import Vet

def vet_list(request):
    vets = Vet.objects.all()
    return render(request, 'vet/vet_list.html', {'vets': vets})
