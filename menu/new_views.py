@login_required
def view_answer_sheet(request, exam_id):
    """Display answer sheet for a specific student exam"""
    student_exam = get_object_or_404(StudentsExams, id=exam_id, deleted_at__isnull=True)
    exam = student_exam.exam
    
    # Get all questions for this exam
    objective_questions = []
    descriptive_questions = []
    
    if exam.exam_type == 'objective' or exam.exam_type == 'both':
        # Get objective questions
        obj_questions = ObjectiveQuestions.objects.filter(exam=exam).order_by('id')
        for question in obj_questions:
            # Get student's answer for this question
            answer = ObjectiveAnswers.objects.filter(
                assignment=student_exam,
                question=question
            ).first()
            
            objective_questions.append({
                'question': question,
                'answer': answer
            })
    
    if exam.exam_type == 'descriptive' or exam.exam_type == 'both':
        # Get descriptive questions
        desc_questions = DescriptiveQuestions.objects.filter(exam=exam).order_by('id')
        for question in desc_questions:
            # Get student's answer for this question
            answer = DescriptiveAnswers.objects.filter(
                assignment=student_exam,
                question=question
            ).first()
            
            descriptive_questions.append({
                'question': question,
                'answer': answer
            })
    
    context = {
        'student_exam': student_exam,
        'objective_questions': objective_questions,
        'descriptive_questions': descriptive_questions,
    }
    
    return render(request, 'admin/students/answer_sheet.html', context)

@login_required
@require_POST
def update_answer_marks(request):
    """Update marks for a student's answer"""
    try:
        answer_id = request.POST.get('answer_id')
        answer_type = request.POST.get('answer_type')  # 'objective' or 'descriptive'
        marks = request.POST.get('marks')
        
        if not answer_id or not answer_type or marks is None:
            return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
        
        marks = float(marks)
        
        if answer_type == 'objective':
            answer = get_object_or_404(ObjectiveAnswers, id=answer_id)
            # Validate marks don't exceed question marks
            if marks > float(answer.question.marks):
                return JsonResponse({
                    'success': False, 
                    'message': f'Marks cannot exceed {answer.question.marks}'
                }, status=400)
            answer.mark = marks
            answer.save()
        elif answer_type == 'descriptive':
            answer = get_object_or_404(DescriptiveAnswers, id=answer_id)
            # Validate marks don't exceed question marks
            if marks > float(answer.question.mark):
                return JsonResponse({
                    'success': False, 
                    'message': f'Marks cannot exceed {answer.question.mark}'
                }, status=400)
            answer.mark = marks
            answer.save()
        else:
            return JsonResponse({'success': False, 'message': 'Invalid answer type'}, status=400)
        
        return JsonResponse({'success': True, 'message': 'Marks updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
