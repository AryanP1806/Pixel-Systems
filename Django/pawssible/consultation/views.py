from django.shortcuts import render, redirect
from .forms import ConsultationForm
from django.contrib.auth.decorators import login_required

@login_required
def request_consultation(request):
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.user = request.user
            consultation.save()
            return redirect('consultation:success')
    else:
        form = ConsultationForm()
    return render(request, 'consultation/request.html', {'form': form})

def consultation_success(request):
    return render(request, 'consultation/success.html')
