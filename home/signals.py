from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import ObjectiveAnswers, DescriptiveAnswers, StudentsExams

@receiver([post_save, post_delete], sender=ObjectiveAnswers)
@receiver([post_save, post_delete], sender=DescriptiveAnswers)
def update_exam_score(sender, instance, **kwargs):
    """
    Signal to update the total exam score (show_on_score) 
    whenever an objective or descriptive answer is saved or deleted.
    """
    # Skip during fixture loading (loaddata) to prevent DoNotExist and DB errors
    if kwargs.get('raw'):
        return

    student_exam = instance.assignment
    
    # Calculate sum of marks
    total_obj_marks = ObjectiveAnswers.objects.filter(assignment=student_exam).aggregate(Sum('mark'))['mark__sum'] or 0
    total_desc_marks = DescriptiveAnswers.objects.filter(assignment=student_exam).aggregate(Sum('mark'))['mark__sum'] or 0
    
    # Update score
    student_exam.show_on_score = total_obj_marks + total_desc_marks
    student_exam.save()
