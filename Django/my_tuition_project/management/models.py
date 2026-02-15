from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone


class User(AbstractUser):
    # Roles
    is_owner = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    
    # Personal Details
    phone = models.CharField(max_length=15, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    year_of_study = models.CharField(max_length=50, blank=True, help_text="e.g. 10th Standard, FY BTech")
    last_year_marks = models.FloatField(null=True, blank=True)
    current_grade = models.PositiveIntegerField(null=True, blank=True)
    def __str__(self):
        return self.username

class Subject(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Batch(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batches_taught')
    subjects = models.ManyToManyField(Subject)
    grade = models.PositiveIntegerField() # Link batch to a specific grade
    students = models.ManyToManyField(User, related_name='enrolled_batches')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.teacher.get_full_name()})"
    
class BatchSubjectTeacher(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_teacher': True})

    class Meta:
        unique_together = ('batch', 'subject')
        
class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'batch', 'date')

class Test(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=100)
    date_held = models.DateField()
    max_marks = models.PositiveIntegerField()

class Mark(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()


class FeeStructure(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fees')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Fees")
    due_date = models.DateField()
    description = models.CharField(max_length=200)

    @property
    def total_paid(self):
        return sum(payment.amount_paid for payment in self.payments.all())

    @property
    def balance_due(self):
        return self.total_amount - self.total_paid

class PaymentTransaction(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=100, blank=True)


class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('User', on_delete=models.CASCADE) # FIXED: on_delete

    def __str__(self):
        return self.title


class StudyMaterial(models.Model):
    MATERIAL_TYPES = [
        ('FILE', 'Document/PDF'),
        ('IMAGE', 'Photo/Image'),
        ('TEXT', 'Written Notes'),
    ]
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES, default='FILE')
    file = models.FileField(upload_to='study_materials/', null=True, blank=True)
    text_content = models.TextField(null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self): return self.title