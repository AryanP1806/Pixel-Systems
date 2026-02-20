from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, Batch, FeeStructure, PaymentTransaction, Subject, Attendance, Test, Mark, Notice,StudyMaterial
from django.db.models import Sum, Q # Added Q here
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone 
import json 
import json
import base64
from django.db import models
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from .models import User

# Access Control
def is_owner(user):
    return user.is_authenticated and user.is_owner


def is_staff(user):
    return user.is_owner or user.is_teacher

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, Batch, FeeStructure, PaymentTransaction, Subject, Attendance, Test, Mark, BatchSubjectTeacher, BiometricCredential
from django.db.models import Sum, Q, Avg, Count, F # Added Avg, Count, F here
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone 

@login_required
def dashboard(request):
    user = request.user
    context = {}

    context['notices'] = Notice.objects.filter(is_active=True).order_by('-created_at')[:3]

    if user.is_student:
        context['recent_materials'] = StudyMaterial.objects.filter(
            Q(batch__students=user) | Q(batch__isnull=True)
        ).order_by('-uploaded_at')[:3]

    if user.is_owner or user.is_teacher:
        if user.is_owner:
            batches = Batch.objects.all()
        else:
            batches = Batch.objects.filter(
                Q(teacher=user) | Q(subject_assignments__teacher=user)
            ).distinct()
        
        context['teacher_count'] = User.objects.filter(is_teacher=True).count()
        context['active_batches_count'] = batches.count()
        context['student_count'] = User.objects.filter(
            is_student=True, 
            enrolled_batches__in=batches
        ).distinct().count()

        toppers_list = []
        at_risk_list = []

        for batch in batches:
            # FIX: Annotating toppers with Percentage instead of raw marks
            # Calculation: (marks_obtained / max_marks) * 100 averaged across all tests in the batch
            batch_students = User.objects.filter(enrolled_batches=batch).annotate(
                avg_pct=Avg(
                    F('mark__marks_obtained') * 100.0 / F('mark__test__max_marks'), 
                    filter=Q(mark__test__batch=batch)
                )
            ).filter(avg_pct__isnull=False).order_by('-avg_pct')[:3]
            
            for s in batch_students:
                toppers_list.append({
                    'student': s, 
                    'batch': batch, 
                    'avg': round(s.avg_pct, 1) 
                })

            # AT-RISK: Dropped below 40% in last 3 tests
            last_3_tests = Test.objects.filter(batch=batch).order_by('-date_held')[:3]
            if last_3_tests.exists():
                test_ids = last_3_tests.values_list('id', flat=True)
                
                # FIX: Calculating true percentage for at-risk flagging
                flagged = User.objects.filter(enrolled_batches=batch).annotate(
                    recent_avg_pct=Avg(
                        F('mark__marks_obtained') * 100.0 / F('mark__test__max_marks'), 
                        filter=Q(mark__test_id__in=test_ids)
                    )
                ).filter(recent_avg_pct__lt=40.0) # Threshold set to 40%

                for s in flagged:
                    at_risk_list.append({
                        'student': s, 
                        'batch': batch, 
                        'avg': round(s.recent_avg_pct, 1) if s.recent_avg_pct else 0
                    })

        context['toppers'] = toppers_list
        context['at_risk'] = at_risk_list

    elif user.is_student:
        attendance_records = Attendance.objects.filter(student=user)
        total = attendance_records.count()
        present = attendance_records.filter(is_present=True).count()
        context['attendance_pct'] = round((present / total * 100), 1) if total > 0 else 0
        latest_mark = Mark.objects.filter(student=user).select_related('test').order_by('-test__date_held').first()
        context['latest_test'] = latest_mark
        context['pending_fees'] = sum(f.balance_due for f in FeeStructure.objects.filter(student=user))

    return render(request, 'management/dashboard.html', context)


# --- SUBJECT MANAGEMENT ---
@login_required
@user_passes_test(is_owner)
def manage_subjects(request):
    if request.method == "POST":
        name = request.POST.get('name')
        Subject.objects.create(name=name)
        messages.success(request, f"Subject {name} added.")
        return redirect('manage_subjects')
    subjects = Subject.objects.all()
    return render(request, 'management/subjects.html', {'subjects': subjects})

# --- STUDENT MANAGEMENT ---
@login_required
@user_passes_test(is_owner)
def student_list(request):
    students = User.objects.filter(is_student=True).order_by('-date_joined')
    return render(request, 'management/student_list.html', {'students': students})

# Add this to your views.py

@login_required
def student_marks(request):
    # Security: Ensure only students see this view
    if not request.user.is_student:
        return redirect('dashboard')
    
    # Fetch all marks for the student, ordered by most recent test
    marks_records = Mark.objects.filter(student=request.user).select_related('test', 'test__subject').order_by('-test__date_held')
    
    # We can calculate some high-level stats if needed
    total_tests = marks_records.count()
    
    return render(request, 'management/student_marks.html', {
        'marks': marks_records,
        'total_tests': total_tests,
    })

@login_required
@user_passes_test(is_owner)
def add_student(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        total_fees = request.POST.get('total_fees')
        
        # Get the numeric grade for logic
        raw_grade = request.POST.get('grade') 
        # Map numeric grade to a string label for year_of_study
        grade_labels = {
            '9': '9th Standard',
            '10': '10th Standard',
            '11': '11th Standard',
            '12': '12th Standard',
            '13': 'Repeaters'
        }
        
        user = User.objects.create_user(
            username=username, 
            password=password,
            email=request.POST.get('email'),
            is_student=True,
            phone=request.POST.get('phone'),
            parent_phone=request.POST.get('parent_phone'),
            age=request.POST.get('age') or None,
            gender=request.POST.get('gender'),
            # Logic: Use current_grade for filtering batches
            current_grade=int(raw_grade) if raw_grade else None,
            # Label: Use year_of_study for display
            year_of_study=grade_labels.get(raw_grade, f"{raw_grade}th Standard"),
            last_year_marks=request.POST.get('marks') or None
        )

        if total_fees:
            FeeStructure.objects.create(
                student=user,
                total_amount=total_fees,
                due_date=request.POST.get('due_date') or timezone.now().date(),
                description=f"Annual Fees - {user.year_of_study}"
            )

        messages.success(request, f"Student {username} registered in {user.year_of_study}.")
        
        if request.POST.get('add_another'):
            return redirect('add_student')
        return redirect('student_list')
    return render(request, 'management/add_student.html')


# --- BATCH MANAGEMENT ---
@login_required
def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'management/batch_list.html', {'batches': batches})

@login_required
@user_passes_test(is_owner)
def batch_create(request):
    if request.method == "POST":
        # Match the template field names exactly
        name = request.POST.get('name')
        grade = request.POST.get('grade')
        main_teacher_id = request.POST.get('main_teacher')
        
        # Validation to prevent the 404 you saw
        if not main_teacher_id:
            messages.error(request, "Please select a Class Teacher.")
            return redirect('batch_create')

        # 1. Create the Batch
        batch = Batch.objects.create(
            name=name,
            grade=grade,
            teacher_id=main_teacher_id
        )

        # 2. Process Subject-Teacher Assignments
        subject_ids = request.POST.getlist('subjects[]')
        assigned_teacher_ids = request.POST.getlist('subject_teachers[]')

        for sub_id, tech_id in zip(subject_ids, assigned_teacher_ids):
            if sub_id and tech_id:
                try:
                    subject = Subject.objects.get(id=sub_id)
                    teacher = User.objects.get(id=tech_id)
                    
                    # Save the specific mapping
                    from .models import BatchSubjectTeacher
                    BatchSubjectTeacher.objects.create(
                        batch=batch,
                        subject=subject,
                        teacher=teacher
                    )
                    
                    # CRITICAL: Also add to the batch's main subject list 
                    # so that Attendance and Tests can find them.
                    batch.subjects.add(subject)
                except (Subject.DoesNotExist, User.DoesNotExist):
                    continue 

        messages.success(request, f"Batch '{batch.name}' created with assigned faculty.")
        return redirect('batch_list')
    
    teachers = User.objects.filter(Q(is_teacher=True) | Q(is_owner=True))
    subjects = Subject.objects.all()
    return render(request, 'management/batch_form.html', {
        'teachers': teachers, 
        'subjects': subjects
    })


@login_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    # CRITICAL: Only show students whose current_grade matches the batch's grade
    # and who aren't already in this specific batch.
    all_students = User.objects.filter(
        is_student=True, 
        current_grade=batch.grade 
    ).exclude(id__in=batch.students.all())
    
    return render(request, 'management/batch_detail.html', {
        'batch': batch, 
        'all_students': all_students
    })

@login_required
@user_passes_test(is_owner)
def add_student_to_batch(request, batch_id):
    if request.method == "POST":
        batch = get_object_or_404(Batch, id=batch_id)
        # getlist captures all checked values from the form
        student_ids = request.POST.getlist('student_ids')
        
        if not student_ids:
            messages.warning(request, "No students were selected.")
            return redirect('batch_detail', batch_id=batch_id)

        students_to_add = User.objects.filter(
            id__in=student_ids, 
            current_grade=batch.grade, 
            is_student=True
        )
        
        count = students_to_add.count()
        if count > 0:
            batch.students.add(*students_to_add)
            messages.success(request, f"Successfully enrolled {count} students into {batch.name}.")
        else:
            messages.error(request, "Enrollment failed: Students must match the batch grade.")
            
    return redirect('batch_detail', batch_id=batch_id)

# --- ATTENDANCE SYSTEM ---

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, Batch, Attendance, Subject, Lecture, TeacherRate
import urllib.parse


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, Batch, Attendance, Subject, Lecture, BatchSubjectTeacher
import urllib.parse

@login_required
def take_attendance(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    
    # 1. Date Logic
    date_str = request.POST.get('date') or request.GET.get('date')
    date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()

    if request.method == "POST":
        subject_id = request.POST.get('subject')
        duration = request.POST.get('duration')
        topic = request.POST.get('topic')
        present_student_ids = request.POST.getlist('attendance')
        
        # --- THE TEACHER ATTRIBUTION LOGIC ---
        # Look for the teacher assigned to this specific subject in this batch
        assignment = BatchSubjectTeacher.objects.filter(batch=batch, subject_id=subject_id).first()
        
        if assignment:
            target_teacher = assignment.teacher
        else:
            # Fallback to the main Class Teacher if no specific subject assignment exists
            target_teacher = batch.teacher

        # 2. Save Student Attendance
        absent_names = []
        for student in batch.students.all():
            is_present = str(student.id) in present_student_ids
            Attendance.objects.update_or_create(
                student=student, batch=batch, date=date,
                defaults={'is_present': is_present}
            )
            if not is_present:
                absent_names.append(student.username)

        # 3. Save Lecture Log (Attributes money to target_teacher)
        if subject_id and duration:
            Lecture.objects.update_or_create(
                batch=batch,
                subject_id=subject_id,
                teacher=target_teacher, # <--- THIS IS THE FIX
                date=date,
                defaults={
                    'duration_minutes': duration,
                    'topic_covered': topic or "Class Session"
                }
            )

        # 4. Prepare WhatsApp Message
        subject_name = Subject.objects.get(id=subject_id).name
        wa_msg = (
            f"*Deekshant Academy Update*\n"
            f"Date: {date.strftime('%d %b %Y')}\n"
            f"Batch: {batch.name}\n"
            f"Subject: {subject_name}\n"
            f"Topic: {topic}\n"
            # f"Attendance: {len(present_student_ids)}/{batch.students.count()}\n"
        )
        if absent_names:
            wa_msg += f"Absentees: \n{'\n'.join(absent_names)}"
            
        encoded_msg = urllib.parse.quote(wa_msg)
        
        messages.success(request, f"Attendance saved. Credit given to {target_teacher.username}.")
        
        return render(request, 'management/attendance_success.html', {
            'batch': batch,
            'wa_url': f"https://wa.me/?text={encoded_msg}"
        })

    # GET Request
    present_ids = Attendance.objects.filter(batch=batch, date=date, is_present=True).values_list('student_id', flat=True)
    has_records = Attendance.objects.filter(batch=batch, date=date).exists()
    
    return render(request, 'management/attendance_form.html', {
        'batch': batch,
        'date': date.strftime('%Y-%m-%d'),
        'present_ids': present_ids,
        'has_records': has_records,
        'subjects': batch.subjects.all()
    })


# @login_required
# def take_attendance(request, batch_id):
#     batch = get_object_or_404(Batch, id=batch_id)
    
#     # Check permissions (Owner or assigned teacher)
#     if not request.user.is_owner:
#         is_assigned = batch.teacher == request.user or batch.subject_assignments.filter(teacher=request.user).exists()
#         if not is_assigned:
#             messages.error(request, "Access Denied.")
#             return redirect('batch_list')

#     date_str = request.POST.get('date') or request.GET.get('date')
#     date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()

#     if request.method == "POST":
#         subject_id = request.POST.get('subject')
#         duration = request.POST.get('duration')
#         topic = request.POST.get('topic')
#         present_student_ids = request.POST.getlist('attendance')
        
#         # 1. Save Student Attendance
#         absent_names = []
#         for student in batch.students.all():
#             is_present = str(student.id) in present_student_ids
#             Attendance.objects.update_or_create(
#                 student=student, 
#                 batch=batch, 
#                 date=date,
#                 defaults={'is_present': is_present}
#             )
#             if not is_present:
#                 absent_names.append(student.username)

#         # 2. Save Lecture/Teaching Hours (for Teacher Pay)
#         if subject_id and duration:
#             Lecture.objects.update_or_create(
#                 batch=batch,
#                 subject_id=subject_id,
#                 teacher=request.user,
#                 date=date,
#                 defaults={
#                     'duration_minutes': duration,
#                     'topic_covered': topic or "Regular Class"
#                 }
#             )

#         # 3. Generate WhatsApp Summary Message
#         subject_name = Subject.objects.get(id=subject_id).name if subject_id else "Class"
#         total = batch.students.count()
#         present_count = len(present_student_ids)
        
        # wa_msg = (
        #     f"*Deekshant Academy - Attendance*\n"
        #     f"📅 Date: {date.strftime('%d %b %Y')}\n"
        #     f"📚 Batch: {batch.name}\n"
        #     f"📖 Subject: {subject_name}\n"
        #     f"📝 Topic: {topic}\n"
        #     f"⏱ Duration: {duration} mins\n"
        #     f"--------------------------\n"
        #     f"✅ Present: {present_count}/{total}\n"
        #     f"❌ Absent: {len(absent_names)}\n"
        # )
#         if absent_names:
#             wa_msg += f"⚠️ Absentees: \n{'\n'.join(absent_names)}"
        
#         # We pass the message to a success page or back to the template
#         encoded_msg = urllib.parse.quote(wa_msg)
#         context = {
#             'batch': batch,
#             'date': date,
#             'wa_url': f"https://wa.me/?text={encoded_msg}",
#             'success': True
#         }
#         messages.success(request, f"Attendance and {duration} mins lecture saved for {date}.")
#         return render(request, 'management/attendance_success.html', context)

#     # Initial GET request logic
#     present_ids = Attendance.objects.filter(batch=batch, date=date, is_present=True).values_list('student_id', flat=True)
#     has_records = Attendance.objects.filter(batch=batch, date=date).exists()
    
#     return render(request, 'management/attendance_form.html', {
#         'batch': batch,
#         'date': date.strftime('%Y-%m-%d'),
#         'present_ids': present_ids,
#         'has_records': has_records,
#         'subjects': batch.subjects.all()
#     })


# --- FEE MANAGEMENT ---
@login_required
def manage_fees(request, student_id):
    # Security Check: Only the Owner or the specific Student can view these fees
    if not request.user.is_owner and request.user.id != student_id:
        messages.error(request, "Access Denied: You can only view your own fee records.")
        return redirect('dashboard')

    student = get_object_or_404(User, id=student_id)
    fees = FeeStructure.objects.filter(student=student)
    
    # Optional: Calculate total balance for a cleaner summary
    total_balance = sum(f.balance_due for f in fees)
    
    return render(request, 'management/fee_detail.html', {
        'student': student, 
        'fees': fees,
        'total_balance': total_balance
    })

@login_required
@user_passes_test(is_owner)
def add_payment(request, fee_id):
    fee = get_object_or_404(FeeStructure, id=fee_id)
    if request.method == "POST":
        PaymentTransaction.objects.create(
            fee_structure=fee,
            amount_paid=request.POST.get('amount_paid'),
            note=request.POST.get('note')
        )
        return redirect('manage_fees', student_id=fee.student.id)
    return render(request, 'management/add_payment.html', {'fee': fee})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self):
        if self.request.user.is_student:
            return reverse_lazy('manage_fees', kwargs={'student_id': self.request.user.id})
        return reverse_lazy('dashboard')
    
import csv
import io
from django.contrib import messages

@user_passes_test(is_owner)
def bulk_student_upload(request):
    if request.method == "POST":
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        next(io_string) # Skip header
        
        for row in csv.reader(io_string, delimiter=','):
            # row format: username, password, email, grade, phone, total_fees
            user = User.objects.create_user(
                username=row[0],
                password=row[1],
                email=row[2],
                current_grade=row[3],
                phone=row[4],
                is_student=True
            )
            # Auto-assign to batch based on grade
            batch = Batch.objects.filter(grade=row[3]).first()
            if batch:
                batch.students.add(user)
        
        messages.success(request, "Students imported and batched successfully!")
        return redirect('student_list')
    return render(request, 'management/bulk_upload.html')

@user_passes_test(is_owner)
def promote_students(request):
    if request.method == "POST":
        # 1. Move students to next grade
        students = User.objects.filter(is_student=True)
        for student in students:
            if student.current_grade < 12:
                student.current_grade += 1
                student.save()
            else:
                # Mark as Alumnus or deactivate if they passed 12th
                student.is_active = False
                student.save()
        
        # 2. Re-assign to new batches based on the new grade
        for student in User.objects.filter(is_student=True, is_active=True):
            new_batch = Batch.objects.filter(grade=student.current_grade).first()
            if new_batch:
                new_batch.students.add(student)
                
        messages.success(request, "New academic year started! Students promoted.")
        return redirect('dashboard')
    

@login_required
def create_test(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if request.method == "POST":
        test = Test.objects.create(
            batch=batch,
            subject=get_object_or_404(Subject, id=request.POST.get('subject')),
            test_name=request.POST.get('test_name'),
            date_held=request.POST.get('date'),
            max_marks=request.POST.get('max_marks')
        )
        messages.success(request, f"Test '{test.test_name}' created. You can now enter marks.")
        return redirect('enter_marks', test_id=test.id)
    
    return render(request, 'management/test_form.html', {'batch': batch})

@login_required
def enter_marks(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    batch = test.batch
    
    if request.method == "POST":
        for student in batch.students.all():
            mark_val = request.POST.get(f'marks_{student.id}')
            if mark_val:
                Mark.objects.update_or_create(
                    student=student, test=test,
                    defaults={'marks_obtained': mark_val}
                )
        messages.success(request, f"Marks saved for {test.test_name}")
        return redirect('batch_detail', batch_id=batch.id)
    
    # Get existing marks to pre-fill
    existing_marks = {m.student_id: m.marks_obtained for m in Mark.objects.filter(test=test)}
    return render(request, 'management/enter_marks.html', {
        'test': test, 
        'existing_marks': existing_marks
    })


# Add this to your existing views.py

@login_required
def student_attendance(request):
    # Ensure only students (or logged-in users viewing their own) can see this
    # If an owner wants to see a specific student's attendance, they usually use the admin or batch detail
    # but this view is specifically for the logged-in student's dashboard.
    
    attendance_records = Attendance.objects.filter(student=request.user).order_by('-date')
    
    # Calculate statistics
    total_sessions = attendance_records.count()
    present_count = attendance_records.filter(is_present=True).count()
    absent_count = total_sessions - present_count
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0

    context = {
        'records': attendance_records,
        'total': total_sessions,
        'present': present_count,
        'absent': absent_count,
        'percentage': round(attendance_percentage, 1)
    }
    return render(request, 'management/student_attendance.html', context)


# Add these to your existing views.py

@login_required
@user_passes_test(is_owner)
def teacher_list(request):
    teachers = User.objects.filter(is_teacher=True).order_by('-date_joined')
    return render(request, 'management/teacher_list.html', {'teachers': teachers})

@login_required
@user_passes_test(is_owner)
def add_teacher(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=request.POST.get('email'),
            is_teacher=True,
            phone=request.POST.get('phone'),
            address=request.POST.get('address')
        )
        messages.success(request, f"Teacher {username} added to faculty.")
        return redirect('teacher_list')
    return render(request, 'management/add_teacher.html')

# --- PERMISSION UPDATES FOR TEACHERS ---

@login_required
def batch_list(request):
    if request.user.is_owner:
        batches = Batch.objects.all()
    elif request.user.is_teacher:
        # Show batches where they are the Lead Teacher OR a Subject Teacher
        batches = Batch.objects.filter(
            Q(teacher=request.user) | Q(subject_assignments__teacher=request.user)
        ).distinct()
    else:
        return redirect('dashboard')
        
    return render(request, 'management/batch_list.html', {'batches': batches})

@login_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    
    # Security: Teachers can only view batches they are part of
    if not request.user.is_owner:
        is_assigned = batch.subject_assignments.filter(teacher=request.user).exists() or batch.teacher == request.user
        if not is_assigned:
            messages.error(request, "Access Denied: You are not assigned to this batch.")
            return redirect('batch_list')

    # Students available for enrollment (Grade match + Not already in batch)
    all_students = User.objects.filter(
        is_student=True, 
        current_grade=batch.grade 
    ).exclude(id__in=batch.students.all())
    
    # --- NEW: Attendance History Logic ---
    # Get distinct dates where attendance was recorded for this batch
    attendance_dates = Attendance.objects.filter(batch=batch).values('date').distinct().order_by('-date')
    
    attendance_history = []
    for entry in attendance_dates:
        date = entry['date']
        records = Attendance.objects.filter(batch=batch, date=date)
        present_count = records.filter(is_present=True).count()
        total_students = records.count()
        
        attendance_history.append({
            'date': date,
            'present': present_count,
            'total': total_students,
            'percentage': (present_count / total_students * 100) if total_students > 0 else 0
        })

    return render(request, 'management/batch_detail.html', {
        'batch': batch, 
        'all_students': all_students,
        'attendance_history': attendance_history
    })

# Add these imports at the top
from django.http import Http404

# Add this helper function at the bottom (or inside the view)
def number_to_words(number):
    # Simple version for Indian Rupees (handling up to lakhs for tuition fees)
    d = { 0 : 'Zero', 1 : 'One', 2 : 'Two', 3 : 'Three', 4 : 'Four', 5 : 'Five',
          6 : 'Six', 7 : 'Seven', 8 : 'Eight', 9 : 'Nine', 10 : 'Ten',
          11 : 'Eleven', 12 : 'Twelve', 13 : 'Thirteen', 14 : 'Fourteen',
          15 : 'Fifteen', 16 : 'Sixteen', 17 : 'Seventeen', 18 : 'Eighteen',
          19 : 'Nineteen', 20 : 'Twenty',
          30 : 'Thirty', 40 : 'Forty', 50 : 'Fifty', 60 : 'Sixty',
          70 : 'Seventy', 80 : 'Eighty', 90 : 'Ninety' }
    n = int(number)
    if n in d: return d[n]
    if n < 100: return d[n // 10 * 10] + ' ' + d[n % 10]
    if n < 1000: return d[n // 100] + ' Hundred ' + (number_to_words(n % 100) if n % 100 > 0 else '')
    if n < 100000: return number_to_words(n // 1000) + ' Thousand ' + (number_to_words(n % 1000) if n % 1000 > 0 else '')
    return str(n) # Fallback for very large numbers


@login_required
def view_receipt(request, transaction_id):
    transaction = get_object_or_404(PaymentTransaction, id=transaction_id)
    student = transaction.fee_structure.student
    
    # Permission Check
    if not request.user.is_owner and student != request.user:
        raise Http404("Unauthorized Access")

    # 1. FIXED LOGIC: Get unique subjects from ALL batches the student is in
    # This ensures if they are in a 'PCM' batch AND a 'Bio' batch, we see all 4 subjects.
    all_subjects = Subject.objects.filter(batch__students=student).distinct()
    
    # 2. Map names to initials
    initials_map = {
        'Physics': 'P', 
        'Chemistry': 'C', 
        'Math': 'M', 
        'Mathematics': 'M', 
        'Biology': 'B',
        'Bio': 'B'
    }
    
    subject_initials = set() # Use a set to avoid duplicates (e.g., if two batches both have Physics)
    for sub in all_subjects:
        # Check map, otherwise take first letter of the subject name
        initial = initials_map.get(sub.name, sub.name[0].upper())
        subject_initials.add(initial)
    
    # 3. Sort initials into standard "PCMB" order
    order = "PCMB"
    sorted_initials = sorted(list(subject_initials), key=lambda x: order.find(x) if x in order else 99)
    subject_display = "".join(sorted_initials) if sorted_initials else "General Fees"

    # 4. Generate amount in words
    amount_in_words = number_to_words(transaction.amount_paid)
    
    context = {
        't': transaction,
        'student': student,
        'fee': transaction.fee_structure,
        'amount_words': amount_in_words,
        'subject_display': subject_display,
        'receipt_no': f"{transaction.id:04d}",
    }
    return render(request, 'management/receipt.html', context)


from django.db.models import Sum, F
from decimal import Decimal

@login_required
@user_passes_test(is_owner)
def finance_dashboard(request):
    # 1. High Level Totals
    total_expected = FeeStructure.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_collected = PaymentTransaction.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    total_pending = total_expected - total_collected

    # 2. Defaulters List (Students with balance > 0 and past due date)
    # Note: We filter in memory for simplicity as per Rule 2
    all_fees = FeeStructure.objects.select_related('student').prefetch_related('payments')
    defaulters = []
    
    for fee in all_fees:
        if fee.balance_due > 0 and fee.due_date < timezone.now().date():
            defaulters.append({
                'student': fee.student,
                'fee': fee,
                'balance': fee.balance_due,
                'parent_phone': fee.student.parent_phone
            })

    # 3. Monthly Collection (Current Month)
    current_month = timezone.now().month
    monthly_collection = PaymentTransaction.objects.filter(
        payment_date__month=current_month
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    context = {
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'monthly_collection': monthly_collection,
        'defaulters': defaulters,
    }
    return render(request, 'management/finance_dashboard.html', context)

from django.db import transaction

@login_required
@user_passes_test(is_owner)
def promote_students(request):
    if request.method == "POST":
        # We use a transaction to ensure either everything moves or nothing moves (no partial data)
        with transaction.atomic():
            active_students = User.objects.filter(is_student=True, is_active=True)
            
            for student in active_students:
                if student.current_grade == 9:
                    # Promote 9 -> 10
                    student.current_grade = 10
                    student.year_of_study = "10th Standard"
                    student.save()
                    
                    # Automatically create New Year Fee Structure
                    FeeStructure.objects.create(
                        student=student,
                        total_amount=15000, # Default or you can make this a setting
                        due_date=timezone.now().date() + timezone.timedelta(days=30),
                        description=f"Annual Fees - 10th Standard (Promoted)"
                    )
                
                elif student.current_grade == 10:
                    # You don't teach 11th. Mark as finished.
                    student.is_active = False
                    student.save()
                
                elif student.current_grade == 12:
                    # Finished 12th. Mark as Alumni.
                    student.is_active = False
                    student.save()

            # Archive Batches: Rename current batches and clear their students
            # This keeps the history of the batch name but readies the system for new year
            current_batches = Batch.objects.all()
            for batch in current_batches:
                # Rename to archive
                current_year = timezone.now().year
                batch.name = f"[Archived {current_year}] {batch.name}"
                batch.save()
                # Remove students so the new year batches are fresh
                batch.students.clear()

        messages.success(request, "Academic Year Transition Complete! 9th graders promoted to 10th. 10th & 12th graders marked as finished. Old batches archived.")
        return redirect('dashboard')
    
    return render(request, 'management/promote_confirm.html')

from django.db.models import Avg
from django.utils import timezone
import calendar


@login_required
@user_passes_test(is_owner)
def student_profile(request, student_id):
    student = get_object_or_404(User, id=student_id, is_student=True)
    
    # --- FILTERS ---
    now = timezone.now()
    view_mode = request.GET.get('view_mode', 'monthly') # 'monthly' or 'all_time'
    month = int(request.GET.get('month', now.month))
    year = int(request.GET.get('year', now.year))
    
    # --- DATA FETCHING ---
    if view_mode == 'all_time':
        attendance_base = Attendance.objects.filter(student=student)
        marks_base = Mark.objects.filter(student=student)
        report_label = "All-Time Academic Standing"
    else:
        attendance_base = Attendance.objects.filter(student=student, date__month=month, date__year=year)
        marks_base = Mark.objects.filter(student=student, test__date_held__month=month, test__date_held__year=year)
        report_label = f"Monthly Report: {calendar.month_name[month]} {year}"

    # 1. Attendance Calculations
    attendance_records = attendance_base.order_by('-date')
    total_days = attendance_records.count()
    present_days = attendance_records.filter(is_present=True).count()
    attendance_pct = (present_days / total_days * 100) if total_days > 0 else 0
    
    # 2. Performance & Grade Logic
    marks = marks_base.select_related('test', 'test__subject').order_by('-test__date_held')
    avg_pct = 0
    if marks.exists():
        total_score_pct = sum((m.marks_obtained / m.test.max_marks) * 100 for m in marks)
        avg_pct = total_score_pct / marks.count()
    
    # Unified Grade Logic
    if avg_pct >= 90: system_grade, status_color = "A+", "text-primary"
    elif avg_pct >= 75: system_grade, status_color = "A", "text-success"
    elif avg_pct >= 60: system_grade, status_color = "B", "text-info"
    elif avg_pct >= 40: system_grade, status_color = "C", "text-warning"
    else: system_grade, status_color = "D", "text-danger"

    # 3. Chart Data (Always Yearly Trend for visual context)
    chart_data = {}
    year_marks = Mark.objects.filter(student=student, test__date_held__year=year).select_related('test__subject').order_by('test__date_held')
    for m in year_marks:
        sub_name = m.test.subject.name
        if sub_name not in chart_data:
            chart_data[sub_name] = {'labels': [], 'scores': []}
        chart_data[sub_name]['labels'].append(m.test.date_held.strftime('%d %b'))
        chart_data[sub_name]['scores'].append(round((m.marks_obtained / m.test.max_marks) * 100, 1))

    # 4. Context for Template
    months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    return render(request, 'management/student_profile.html', {
        'student': student,
        'view_mode': view_mode,
        'report_label': report_label,
        'marks': marks,
        'attendance_history': attendance_records[:10],
        'attendance_pct': round(attendance_pct, 1),
        'total_days': total_days,
        'present_days': present_days,
        'system_grade': system_grade,
        'status_color': status_color,
        'avg_pct': round(avg_pct, 1),
        'chart_data_json': json.dumps(chart_data),
        'selected_month': month,
        'selected_year': year,
        'months_list': months_list,
        'total_balance': sum(f.balance_due for f in FeeStructure.objects.filter(student=student))
    })

@login_required
@user_passes_test(is_owner)
def report_card(request, student_id):
    student = get_object_or_404(User, id=student_id, is_student=True)
    
    # Fetch data specifically for the report card
    marks = Mark.objects.filter(student=student).select_related('test', 'test__subject').order_by('test__subject__name')
    
    attendance_records = Attendance.objects.filter(student=student)
    total_days = attendance_records.count()
    present_days = attendance_records.filter(is_present=True).count()
    attendance_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0

    return render(request, 'management/report_card.html', {
        'student': student,
        'marks': marks,
        'total_days': total_days,
        'present_days': present_days,
        'attendance_pct': attendance_pct,
    })


@login_required
@user_passes_test(is_owner)
def create_notice(request):
    if request.method == "POST":
        Notice.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            created_by=request.user
        )
        messages.success(request, "Notice broadcasted successfully!")
        return redirect('dashboard')
    return render(request, 'management/add_notice.html')

@login_required
@user_passes_test(is_staff)
def upload_material(request):
    if request.method == "POST":
        m_type = request.POST.get('material_type')
        StudyMaterial.objects.create(
            title=request.POST.get('title'),
            material_type=m_type,
            file=request.FILES.get('file') if m_type != 'TEXT' else None,
            text_content=request.POST.get('text_content') if m_type == 'TEXT' else '',
            subject_id=request.POST.get('subject'),
            batch_id=request.POST.get('batch') or None,
            uploaded_by=request.user
        )
        messages.success(request, "Material published to the repository!")
        return redirect('study_material_list')
    
    # Context logic for dropdowns
    subjects = Subject.objects.all() if request.user.is_owner else Subject.objects.filter(batch__teacher=request.user).distinct()
    batches = Batch.objects.all() if request.user.is_owner else Batch.objects.filter(teacher=request.user)
    
    return render(request, 'management/upload_material.html', {
        'subjects': subjects,
        'batches': batches
    })

@login_required
def study_material_list(request):
    # View all materials accessible to the user
    if request.user.is_student:
        materials = StudyMaterial.objects.filter(batch__students=request.user) | StudyMaterial.objects.filter(batch__isnull=True)
    else:
        materials = StudyMaterial.objects.all()
    return render(request, 'management/material_list.html', {'materials': materials})


from django.contrib import messages
from .models import StudyMaterial, Subject, User, Batch, Test, Mark

# --- TEACHER & STUDENT EDIT/DELETE ---
@login_required
@user_passes_test(is_owner)
def edit_user(request, user_id):
    """
    Comprehensive profile editor for both Students and Teachers.
    Handles all academic, personal, and security fields.
    """
    u = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        # 1. Core Identity
        u.username = request.POST.get('username')
        u.first_name = request.POST.get('first_name', '')
        u.last_name = request.POST.get('last_name', '')
        u.email = request.POST.get('email', '')
        
        # 2. Personal Details
        u.phone = request.POST.get('phone', '')
        u.address = request.POST.get('address', '')
        u.age = request.POST.get('age') or None
        u.gender = request.POST.get('gender', '')

        # 3. Role-Specific Logic
        if u.is_student:
            u.parent_phone = request.POST.get('parent_phone', '')
            u.last_year_marks = request.POST.get('last_year_marks') or None
            
            # Synchronize Grade and Display Label
            raw_grade = request.POST.get('current_grade')
            if raw_grade:
                u.current_grade = int(raw_grade)
                grade_labels = {
                    '9': '9th Standard', '10': '10th Standard', 
                    '11': '11th Standard', '12': '12th Standard', '13': 'Repeaters'
                }
                u.year_of_study = grade_labels.get(str(raw_grade), f"{raw_grade}th Standard")
        
        # 4. Security Reset
        password = request.POST.get('password')
        if password and len(password.strip()) > 0:
            u.set_password(password)
        
        u.save()
        messages.success(request, f"Profile for {u.get_full_name() or u.username} fully synchronized.")
        return redirect('student_list' if u.is_student else 'teacher_list')

    return render(request, 'management/edit_user.html', {'u': u})

@login_required
@user_passes_test(is_owner)
def delete_user(request, user_id):
    u = get_object_or_404(User, id=user_id)
    role = "Student" if u.is_student else "Teacher"
    u.delete()
    messages.warning(request, f"{role} deleted successfully.")
    return redirect('student_list' if role == "Student" else 'teacher_list')

# --- SUBJECT EDIT/DELETE ---
@login_required
@user_passes_test(is_owner)
def delete_subject(request, subject_id):
    sub = get_object_or_404(Subject, id=subject_id)
    sub.delete()
    messages.warning(request, "Subject removed.")
    return redirect('manage_subjects')

# --- BATCH EDIT/DELETE ---
@login_required
@user_passes_test(is_owner)
def delete_batch(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    batch.delete()
    messages.warning(request, "Batch deleted.")
    return redirect('batch_list')

# --- STUDY MATERIAL EDIT/DELETE ---
@login_required
def delete_material(request, material_id):
    mat = get_object_or_404(StudyMaterial, id=material_id)
    # SECURITY: Only owner or the uploader can delete
    if request.user.is_owner or mat.uploaded_by == request.user:
        mat.delete()
        messages.warning(request, "Material removed from repository.")
    else:
        messages.error(request, "Permission Denied: You didn't upload this.")
    return redirect('study_material_list')


from .models import TeacherRate, Lecture, TeacherPayment

@login_required
@user_passes_test(is_owner)
def manage_teacher_rates(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, is_teacher=True)
    if request.method == "POST":
        grade = request.POST.get('grade')
        rate = request.POST.get('rate')
        TeacherRate.objects.update_or_create(
            teacher=teacher, grade=grade,
            defaults={'hourly_rate': rate}
        )
        messages.success(request, f"Rate updated for Grade {grade}")
        return redirect('manage_teacher_rates', teacher_id=teacher.id)
    
    rates = TeacherRate.objects.filter(teacher=teacher)
    return render(request, 'management/teacher_rates.html', {'teacher': teacher, 'rates': rates})

@login_required
def log_lecture(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    # Only owner or assigned teacher can log
    if not request.user.is_owner and batch.teacher != request.user:
        # Check if they are a subject teacher for this batch
        is_assigned = batch.subject_assignments.filter(teacher=request.user).exists()
        if not is_assigned:
            messages.error(request, "Unauthorized")
            return redirect('dashboard')

    if request.method == "POST":
        Lecture.objects.create(
            batch=batch,
            subject_id=request.POST.get('subject'),
            teacher=request.user if not request.user.is_owner else User.objects.get(id=request.POST.get('teacher')),
            date=request.POST.get('date'),
            duration_minutes=request.POST.get('duration'),
            topic_covered=request.POST.get('topic')
        )
        messages.success(request, "Lecture logged successfully.")
        return redirect('batch_detail', batch_id=batch.id)
    
    subjects = batch.subjects.all()
    teachers = User.objects.filter(is_teacher=True)
    return render(request, 'management/lecture_form.html', {'batch': batch, 'subjects': subjects, 'teachers': teachers})

@login_required
@user_passes_test(is_owner)
def teacher_salary_report(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, is_teacher=True)
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    lectures = Lecture.objects.filter(
        teacher=teacher, 
        date__month=month, 
        date__year=year
    ).select_related('batch')
    
    total_earnings = sum(l.calculated_earning for l in lectures)
    
    return render(request, 'management/teacher_salary_report.html', {
        'teacher': teacher,
        'lectures': lectures,
        'total_earnings': total_earnings,
        'selected_month': month,
        'selected_year': year
    })



from django.http import JsonResponse
from django.db.models import Count, Q
from django.urls import reverse_lazy, reverse

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = []

    if len(query) < 2:
        return JsonResponse({'results': []})

    # 1. Search Students
    students = User.objects.filter(
        Q(is_student=True) & 
        (Q(username__icontains=query) | Q(first_name__icontains=query) | Q(phone__icontains=query))
    )[:5]
    for s in students:
        results.append({
            'category': 'Students',
            'title': s.get_full_name() or s.username,
            'subtitle': f"Std: {s.current_grade}th | {s.enrolled_batches.count()} Batches",
            'url': reverse('student_profile', args=[s.id]),
            'icon': 'bi-person-badge'
        })

    # 2. Search Teachers
    teachers = User.objects.filter(
        Q(is_teacher=True) & 
        (Q(username__icontains=query) | Q(email__icontains=query))
    )[:5]
    for t in teachers:
        results.append({
            'category': 'Faculty',
            'title': t.get_full_name() or t.username,
            'subtitle': f"Teaching {t.batches_taught.count() + t.batchsubjectteacher_set.count()} Subjects",
            'url': reverse('teacher_profile', args=[t.id]),
            'icon': 'bi-mortarboard'
        })

    # 3. Search Batches (With Stats)
    batches = Batch.objects.filter(name__icontains=query).annotate(
        student_count=Count('students', distinct=True),
        test_count=Count('test', distinct=True)
    )[:5]
    for b in batches:
        results.append({
            'category': 'Batches',
            'title': b.name,
            'subtitle': f"Gr {b.grade} | {b.student_count} Students | {b.test_count} Tests",
            'url': reverse('batch_detail', args=[b.id]),
            'icon': 'bi-stack'
        })

    return JsonResponse({'results': results})


@login_required
@user_passes_test(is_owner)
def teacher_profile(request, teacher_id):
    """
    Dedicated detail view for a Teacher.
    Shows Assignments, Rates, and Recent Activity.
    """
    teacher = get_object_or_404(User, id=teacher_id, is_teacher=True)
    
    # Assignments
    assignments = BatchSubjectTeacher.objects.filter(teacher=teacher).select_related('batch', 'subject')
    
    # Financials (Last 30 days)
    recent_lectures = Lecture.objects.filter(teacher=teacher).order_by('-date')[:10]
    monthly_total = sum(l.calculated_earning for l in Lecture.objects.filter(teacher=teacher, date__month=timezone.now().month))
    
    # Rates
    rates = TeacherRate.objects.filter(teacher=teacher)
    
    return render(request, 'management/teacher_profile.html', {
        'teacher': teacher,
        'assignments': assignments,
        'recent_lectures': recent_lectures,
        'monthly_total': monthly_total,
        'rates': rates,
    })




@csrf_exempt
def register_biometric(request):
    """
    Step 1: Save the public key from the browser.
    Note: Real production needs 'fido2-tools' to verify, 
    this is a simplified logic for your MVP.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        BiometricCredential.objects.create(
            user=request.user,
            credential_id=data['id'],
            public_key=data['publicKey']
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

@csrf_exempt
def login_biometric(request):
    """
    Step 2: Authenticate user based on credential ID.
    In a raw implementation, we trust the device signature.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        cred = BiometricCredential.objects.filter(credential_id=data['id']).first()
        if cred:
            login(request, cred.user)
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=401)