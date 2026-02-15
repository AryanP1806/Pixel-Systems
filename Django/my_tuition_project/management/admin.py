from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Sum
from .models import User, Subject, Batch, Attendance, Test, Mark, FeeStructure, PaymentTransaction

# 1. Optimized User Admin (The Student/Teacher Directory)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Only show relevant columns for a quick overview
    list_display = ('username', 'get_full_name', 'current_grade', 'is_student', 'is_teacher', 'phone')
    list_filter = ('current_grade', 'is_student', 'is_teacher', 'gender')
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'parent_phone')
    
    # Organize the detailed view into sections
    fieldsets = UserAdmin.fieldsets + (
        ('Tuition Roles', {'fields': ('is_owner', 'is_teacher', 'is_student')}),
        ('Academic Details', {'fields': ('current_grade', 'year_of_study', 'last_year_marks', 'age', 'gender')}),
        ('Contact Info', {'fields': ('phone', 'parent_phone', 'address')}),
    )

# 2. Batch Management (Handling 30 students per class)
# @admin.register(Batch)
# class BatchAdmin(admin.ModelAdmin):
#     list_display = ('name', 'teacher', 'get_student_count', 'created_at')
#     list_filter = ('subjects', 'teacher')
#     search_fields = ('name',)
#     # Use horizontal filter for easy bulk selection of students/subjects
#     filter_horizontal = ('students', 'subjects')

#     def get_student_count(self, obj):
#         return obj.students.count()
#     get_student_count.short_description = "Students Enrolled"

# 3. Attendance Admin (Quick tracking)
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'batch', 'date', 'is_present')
    list_filter = ('date', 'batch', 'is_present')
    search_fields = ('student__username', 'student__first_name')
    date_hierarchy = 'date' # Adds a calendar navigation at the top

# 4. Fee & Money Management (The most critical part)
class PaymentInline(admin.TabularInline):
    """Allows adding payments directly inside the Fee window"""
    model = PaymentTransaction
    extra = 1

@admin.register(FeeStructure)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_amount', 'get_paid', 'get_balance', 'due_date')
    list_filter = ('due_date', 'student__current_grade')
    search_fields = ('student__username', 'student__first_name')
    inlines = [PaymentInline]

    def get_paid(self, obj):
        return obj.total_paid
    get_paid.short_description = "Paid"

    def get_balance(self, obj):
        return obj.balance_due
    get_balance.short_description = "Balance"

# 5. Academic Performance (Tests & Marks)
class MarkInline(admin.TabularInline):
    model = Mark
    extra = 5 # Show 5 empty rows to fill marks quickly

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'batch', 'subject', 'date_held', 'max_marks')
    list_filter = ('batch', 'subject', 'date_held')
    inlines = [MarkInline]

# Basic registrations
admin.site.register(Subject)
admin.site.register(PaymentTransaction)


# from django.contrib import admin
# from .models import User, Subject, Batch, Attendance, Test, Mark, FeeStructure, PaymentTransaction, BatchSubjectTeacher

# class BatchSubjectTeacherInline(admin.TabularInline):
#     model = BatchSubjectTeacher
#     extra = 1

# @admin.register(Batch)
# class BatchAdmin(admin.ModelAdmin):
#     list_display = ('name', 'teacher', 'get_student_count', 'grade', 'created_at')
#     list_filter = ('grade', 'teacher')
#     filter_horizontal = ('students',)
#     inlines = [BatchSubjectTeacherInline]

#     def get_student_count(self, obj):
#         return obj.students.count()
#     get_student_count.short_description = "Students"


from django.contrib import admin
from .models import User, Subject, Batch, Attendance, Test, Mark, FeeStructure, PaymentTransaction, BatchSubjectTeacher

class BatchSubjectTeacherInline(admin.TabularInline):
    model = BatchSubjectTeacher
    extra = 1

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'get_student_count', 'grade', 'created_at')
    list_filter = ('grade', 'teacher')
    filter_horizontal = ('students',)
    inlines = [BatchSubjectTeacherInline]

    def get_student_count(self, obj):
        return obj.students.count()
    get_student_count.short_description = "Students"

# Register the mapping model directly too
admin.site.register(BatchSubjectTeacher)

# --- GLOBAL SETTINGS ---
admin.site.site_header = "Deekshant Tuition Management"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "System Control"