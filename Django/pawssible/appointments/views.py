from django.shortcuts import render, redirect
from .forms import AppointmentForm
from .models import Appointment
from django.contrib.auth.decorators import login_required

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.save()
            return redirect('appointments:success')
    else:
        form = AppointmentForm()
    return render(request, 'appointments/book.html', {'form': form})

def appointment_success(request):
    return render(request, 'appointments/success.html')
