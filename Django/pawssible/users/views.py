from django.shortcuts import render, redirect
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required
from community.models import Post


@login_required
def view_profile(request):
    profile = request.user.profile
    my_posts = Post.objects.filter(user=request.user)
    return render(request, 'users/profile.html', {
        'profile': profile,
        'my_posts': my_posts,
    })

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'users/edit_profile.html', {'form': form})


from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegisterForm
from django.contrib import messages
from .forms import PetScheduleForm
from django.http import JsonResponse
from .models import PetSchedule
from django.utils import timezone

def user_schedule(request):
    now = timezone.now()
    upcoming = PetSchedule.objects.filter(user=request.user, scheduled_time__gte=now)
    data = [
        {
            "title": s.title,
            "description": s.description,
            "time": s.scheduled_time.isoformat()
        }
        for s in upcoming
    ]
    return JsonResponse(data, safe=False)

@login_required
def create_schedule(request):
    if request.method == 'POST':
        form = PetScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            schedule.save()
            return redirect('users:schedule_list')
    else:
        form = PetScheduleForm()
    return render(request, 'users/create_schedule.html', {'form': form})


@login_required
def schedule_list(request):
    schedules = PetSchedule.objects.filter(user=request.user).order_by('scheduled_time')
    return render(request, 'users/schedule_list.html', {'schedules': schedules})


@login_required
def upcoming_schedules_api(request):
    now = timezone.now()
    upcoming = PetSchedule.objects.filter(user=request.user, scheduled_time__gte=now)
    data = [
        {
            "title": s.title,
            "description": s.description,
            "time": s.scheduled_time
        }
        for s in upcoming
    ]
    return JsonResponse(data, safe=False)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_staff = False
            user.is_superuser = False
            user.save()
            messages.success(request, 'Account created! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})



