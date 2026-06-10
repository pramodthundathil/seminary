from functools import wraps
from django.shortcuts import redirect

"""
for students only
"""
def student_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        role = request.user.user_roles.first().role.name if request.user.user_roles.exists() else None
        
        if role != "Student":
            return redirect("student_home")   
        
        # Check student payment status and active status
        from home.models import Students, Payments, StudentsSubjects
        student = Students.objects.filter(user=request.user).first()
        if student:
            # 1. If payment is not done, check balance and redirect to payment screen
            if not student.is_paid:
                payment = Payments.objects.filter(student=student, is_paid=False, subjects_id__isnull=True, deleted_at__isnull=True).first()
                if payment:
                    balance_due = float(payment.amount or 0)
                else:
                    course_fee = float(student.course_applied.fees) if (student.course_applied and student.course_applied.fees) else 0.00
                    subject_fees = sum(float(ss.subject.fees or 0) for ss in StudentsSubjects.objects.filter(student=student, deleted_at__isnull=True) if ss.subject)
                    total_fee_expected = course_fee + subject_fees
                    total_paid = sum(float(p.amount or 0) for p in Payments.objects.filter(student=student, is_paid=True, deleted_at__isnull=True))
                    balance_due = total_fee_expected - total_paid
                    
                    if balance_due > 0:
                        payment = Payments.objects.create(
                            name=f"{student.first_name} {student.last_name or ''}".strip(),
                            email=student.email,
                            phone=student.phone_number,
                            person_group="student",
                            amount=balance_due,
                            is_paid=False,
                            student=student
                        )
                
                if payment and balance_due > 0:
                    request.session['registration_payment_id'] = payment.id
                    return redirect('registration_payment')
                else:
                    student.is_paid = True
                    student.save()
            
            # 2. If payment is done but student is not active, redirect to student_inactive status screen
            if not student.active:
                return redirect('student_inactive')
        
        return view_func(request, *args, **kwargs)
    return wrapper


"""
for students and church users
"""
def student_or_church_user(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        role = request.user.user_roles.first().role.name if request.user.user_roles.exists() else None
        
        if role not in ["Student", "Church User"]:
            return redirect("signin")  # fallback
            
        if role == "Student":
            from home.models import Students, Payments, StudentsSubjects
            student = Students.objects.filter(user=request.user).first()
            if student:
                # 1. If payment is not done, check balance and redirect to payment screen
                if not student.is_paid:
                    payment = Payments.objects.filter(student=student, is_paid=False, subjects_id__isnull=True, deleted_at__isnull=True).first()
                    if payment:
                        balance_due = float(payment.amount or 0)
                    else:
                        course_fee = float(student.course_applied.fees) if (student.course_applied and student.course_applied.fees) else 0.00
                        subject_fees = sum(float(ss.subject.fees or 0) for ss in StudentsSubjects.objects.filter(student=student, deleted_at__isnull=True) if ss.subject)
                        total_fee_expected = course_fee + subject_fees
                        total_paid = sum(float(p.amount or 0) for p in Payments.objects.filter(student=student, is_paid=True, deleted_at__isnull=True))
                        balance_due = total_fee_expected - total_paid
                        
                        if balance_due > 0:
                            payment = Payments.objects.create(
                                name=f"{student.first_name} {student.last_name or ''}".strip(),
                                email=student.email,
                                phone=student.phone_number,
                                person_group="student",
                                amount=balance_due,
                                is_paid=False,
                                student=student
                            )
                    
                    if payment and balance_due > 0:
                        request.session['registration_payment_id'] = payment.id
                        return redirect('registration_payment')
                    else:
                        student.is_paid = True
                        student.save()
                
                # 2. If payment is done but student is not active, redirect to student_inactive status screen
                if not student.active:
                    return redirect('student_inactive')
        
        return view_func(request, *args, **kwargs)
    return wrapper
