from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, Batch, FeeStructure, PaymentTransaction, Subject, Attendance, Test, Mark, Notice,StudyMaterial
from django.db.models import Sum, Q # Added Q here
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone 
import json 

# Access Control
def is_owner(user):
    return user.is_authenticated and user.is_owner


def is_staff(user):
    return user.is_owner or user.is_teacher

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, Batch, FeeStructure, PaymentTransaction, Subject, Attendance, Test, Mark, BatchSubjectTeacher
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

    # 2. Study Material Repository (Recent files for the student's batch)
    if user.is_student:
        context['recent_materials'] = StudyMaterial.objects.filter(
            Q(batch__students=user) | Q(batch__isnull=True)
        ).order_by('-uploaded_at')[:3]

    # Identify if user is staff (Owner or Teacher)
    if user.is_owner or user.is_teacher:
        # 1. GET BATCHES
        if user.is_owner:
            batches = Batch.objects.all()
            context['teacher_count'] = User.objects.filter(is_teacher=True).count()
        else:
            # For Teachers: Show batches where they are Lead OR Subject Teacher
            batches = Batch.objects.filter(
                Q(teacher=user) | Q(subject_assignments__teacher=user)
            ).distinct()
        
        # 2. STATS
        context['student_count'] = User.objects.filter(is_student=True).count()
        context['teacher_count'] = User.objects.filter(is_teacher=True).count()
        context['active_batches_count'] = Batch.objects.count()
        context['active_batches_count'] = batches.count()
        context['student_count'] = User.objects.filter(
            is_student=True, 
            enrolled_batches__in=batches
        ).distinct().count()

        # 3. ACADEMIC HEALTH CHECK (Toppers & At-Risk)
        toppers_list = []
        at_risk_list = []

        for batch in batches:
            # TOPPERS: Average marks across all tests in THIS batch
            # We calculate this by filtering marks belonging to tests of this batch
            batch_students = User.objects.filter(enrolled_batches=batch).annotate(
                avg_score=Avg('mark__marks_obtained', filter=Q(mark__test__batch=batch))
            ).filter(avg_score__isnull=False).order_by('-avg_score')[:3]
            
            for s in batch_students:
                toppers_list.append({
                    'student': s, 
                    'batch': batch, 
                    'avg': round(s.avg_score, 1)
                })

            # AT-RISK: Dropped below 40% in last 3 tests
            # We first find the last 3 tests for this batch
            last_3_tests = Test.objects.filter(batch=batch).order_by('-date_held')[:3]
            if last_3_tests.exists():
                test_ids = last_3_tests.values_list('id', flat=True)
                # Calculate the average max marks of these tests to set a threshold
                avg_max = last_3_tests.aggregate(Avg('max_marks'))['max_marks__avg'] or 100
                threshold = avg_max * 0.4
                
                flagged = User.objects.filter(enrolled_batches=batch).annotate(
                    recent_avg=Avg('mark__marks_obtained', filter=Q(mark__test_id__in=test_ids))
                ).filter(recent_avg__lt=threshold)

                for s in flagged:
                    at_risk_list.append({
                        'student': s, 
                        'batch': batch, 
                        'avg': round(s.recent_avg, 1) if s.recent_avg else 0
                    })

        context['toppers'] = toppers_list
        context['at_risk'] = at_risk_list

    # STUDENT SPECIFIC VIEW
    elif user.is_student:
        attendance_records = Attendance.objects.filter(student=user)
        total = attendance_records.count()
        present = attendance_records.filter(is_present=True).count()
        
        context['attendance_pct'] = round((present / total * 100), 1) if total > 0 else 0
        
        # Latest performance
        latest_mark = Mark.objects.filter(student=user).select_related('test').order_by('-test__date_held').first()
        context['latest_test'] = latest_mark
        
        # Financials
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

@login_required
def take_attendance(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    
    # 1. Determine the date (Priority: POST > GET > Today)
    date_str = request.POST.get('date') or request.GET.get('date')
    if date_str:
        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date = timezone.now().date()
    else:
        date = timezone.now().date()

    if request.method == "POST":
        present_student_ids = request.POST.getlist('attendance')
        for student in batch.students.all():
            Attendance.objects.update_or_create(
                student=student, 
                batch=batch, 
                date=date,
                defaults={'is_present': str(student.id) in present_student_ids}
            )
        messages.success(request, f"Attendance updated for {date}")
        return redirect('batch_detail', batch_id=batch_id)
    
    # 2. Fetch existing attendance to pre-fill the form
    # We create a set of IDs for students who are ALREADY marked present for this date
    present_ids = Attendance.objects.filter(
        batch=batch, 
        date=date, 
        is_present=True
    ).values_list('student_id', flat=True)

    # 3. Check if any attendance exists at all for this date
    # If NO records exist, we default everyone to 'checked' for convenience
    has_records = Attendance.objects.filter(batch=batch, date=date).exists()

    return render(request, 'management/attendance_form.html', {
        'batch': batch, 
        'date': date.strftime('%Y-%m-%d'),
        'present_ids': present_ids,
        'has_records': has_records
    })

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


@login_required
@user_passes_test(is_owner)
def student_profile(request, student_id):
    student = get_object_or_404(User, id=student_id, is_student=True)
    
    # 1. Batches & Subjects
    batches = student.enrolled_batches.all().prefetch_related('subjects', 'subject_assignments__teacher')
    
    # 2. Academic Performance
    marks = Mark.objects.filter(student=student).select_related('test', 'test__subject').order_by('-test__date_held')
    
    # 3. Attendance Summary
    attendance_records = Attendance.objects.filter(student=student).order_by('-date')
    total_days = attendance_records.count()
    present_days = attendance_records.filter(is_present=True).count()
    attendance_pct = (present_days / total_days * 100) if total_days > 0 else 0
    

    chart_data = {}
    student_marks = Mark.objects.filter(student_id=student_id).select_related('test__subject').order_by('test__date_held')
    
    for m in student_marks:
        sub_name = m.test.subject.name
        if sub_name not in chart_data:
            chart_data[sub_name] = {'labels': [], 'scores': []}
        
        chart_data[sub_name]['labels'].append(m.test.date_held.strftime('%d %b'))
        # Calculate percentage for uniform graphing
        pct = (m.marks_obtained / m.test.max_marks) * 100
        chart_data[sub_name]['scores'].append(round(pct, 1))


    # 4. Financial Ledger
    fees = FeeStructure.objects.filter(student=student).prefetch_related('payments')
    total_balance = sum(f.balance_due for f in fees)

    return render(request, 'management/student_profile.html', {
        'student': student,
        'batches': batches,
        'marks': marks,
        'attendance_history': attendance_records[:10], # Last 10 days
        'attendance_pct': round(attendance_pct, 1),
        'fees': fees,
        'total_balance': total_balance,
        'chart_data_json': json.dumps(chart_data),
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