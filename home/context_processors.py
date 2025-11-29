from .models import Students

def student_processor(request):
    # if not request.user.is_authenticated:
    #     return {}

    try:
        # student = Students.objects.get(user_id=request.user.id)
        student = Students.objects.get(id=166)
    except Students.DoesNotExist:
        student = None

    return {
        "student": student
    }
