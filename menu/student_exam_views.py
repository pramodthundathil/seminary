
#Student Submitted Exams Views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Sum
from home.models import Students, StudentsExams, ObjectiveAnswers, DescriptiveAnswers

@login_required
def student_submitted_exams_list(request):
    """Render student submitted exams page"""
    context = {
        'page_title': 'My Submitted Exams',
    }
    return render(request, 'students/student_submitted_exams.html', context)

@login_required
def student_submitted_exams_datatable(request):
    """DataTables server-side processing for student's submitted exams"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'desc')
    
    # Get current student
    try:
        student = Students.objects.get(user=request.user, deleted_at__isnull=True)
    except Students.DoesNotExist:
        return JsonResponse({'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})
    
    # Query exams for this student
    query = StudentsExams.objects.filter(
        student=student,
        deleted_at__isnull=True
    ).select_related('exam', 'course', 'subject')

    if search_value:
        query = query.filter(
            Q(exam__exam_name__icontains=search_value) |
            Q(subject__subject_name__icontains=search_value) |
            Q(course__course_name__icontains=search_value)
        )
    
    # Ordering
    order_col = '-created_at'
    if order_column_index == 0:
        order_col = 'exam__exam_name'
    elif order_column_index == 1:
        order_col = 'subject__subject_name'
    elif order_column_index == 2:
        order_col = 'course__course_name'
    elif order_column_index == 3:
        order_col = 'start_time'

    if order_direction == 'desc' and not order_col.startswith('-'):
        order_col = '-' + order_col
    
    total_records = StudentsExams.objects.filter(student=student, deleted_at__isnull=True).count()
    filtered_records = query.count()
    data_list = query.order_by(order_col)[start:start+length]
    
    data = []
    for item in data_list:
        start_time = item.start_time.strftime('%Y-%m-%d %H:%M') if item.start_time else '-'
        
        # Determine status
        if item.is_exam_ended:
            status = '<span class="status-badge status-ended">Ended</span>'
        elif item.is_exam_started:
            status = '<span class="status-badge status-started">In Progress</span>'
        elif item.is_approved:
            status = '<span class="status-badge status-approved">Approved</span>'
        else:
            status = '<span class="status-badge status-pending">Pending</span>'
        
        # Calculate total marks if available
        from django.db.models import Sum
        obj_marks = ObjectiveAnswers.objects.filter(assignment=item).aggregate(total=Sum('mark'))['total'] or 0
        desc_marks = DescriptiveAnswers.objects.filter(assignment=item).aggregate(total=Sum('mark'))['total'] or 0
        total_marks = float(obj_marks) + float(desc_marks)
        
        marks_display = f'{total_marks:.1f}' if total_marks > 0 else '-'
        
        # Actions - always show view answer sheet button
        actions = f'''
            <div class="action-buttons">
                <button class="btn-action btn-view" onclick="viewAnswerSheet({item.id})" title="View Answer Sheet">
                    <i class="bi bi-eye"></i> View
                </button>
            </div>
        '''
        
        data.append({
            'exam_name': item.exam.exam_name if item.exam else 'Unknown Exam',
            'subject_name': item.subject.subject_name if item.subject else '-',
            'course_name': item.course.course_name if item.course else '-',
            'start_time': start_time,
            'duration': f'{item.exam_duration} min',
            'status': status,
            'marks': marks_display,
            'actions': actions
        })
        
    return JsonResponse({'draw': draw, 'recordsTotal': total_records, 'recordsFiltered': filtered_records, 'data': data})
