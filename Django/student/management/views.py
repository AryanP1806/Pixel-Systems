from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Student
from .forms import StudentForm
from .hashing import student_hash

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'students/login.html', {'error': 'Invalid credentials'})
    return render(request, 'students/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    return render(request, 'students/home.html')

@login_required
def add_student(request):
    if not request.user.is_staff:
        return redirect('view_students')

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            student_hash.insert(student)
            return redirect('view_students')
    else:
        form = StudentForm()
    return render(request, 'students/add_student.html', {'form': form})

@login_required
def view_students(request):
    if request.user.is_staff:
        students = Student.objects.all()
    else:
        # Normal student view - only their record if email matches
        students = Student.objects.filter(email=request.user.email)
    student_hash.table = {hash(s.student_id) % 100: s for s in students}
    sorted_students = student_hash.get_all_sorted()
    return render(request, 'students/view_students.html', {'students': sorted_students})

@login_required
def delete_student(request, student_id):
    if not request.user.is_staff:
        return redirect('view_students')

    student = get_object_or_404(Student, student_id=student_id)
    if request.method == 'POST':
        student_hash.delete(student.student_id)
        student.delete()
        return redirect('view_students')
    return render(request, 'students/delete_student.html', {'student': student})

def search_student(request):
    query = request.GET.get('student_id')
    result = None
    if query:
        result = student_hash.search(query)
        if not result:
            try:
                result = Student.objects.get(student_id=query)
                student_hash.insert(result)
            except Student.DoesNotExist:
                result = None
    return render(request, ' view_students.html', {'students': [result] if result else []})
