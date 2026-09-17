
@login_required
@require_POST
def pages_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Pages.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('pages_list')

@login_required
@require_POST
def course_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Courses.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('course_list')

@login_required
@require_POST
def student_books_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentBooks.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_books_list')

@login_required
@require_POST
def student_subjects_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentSubjects.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_subjects_list')

@login_required
@require_POST
def student_instructors_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentInstructors.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_instructors_list')

@login_required
@require_POST
def student_uploads_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentUploads.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_uploads_list')

@login_required
@require_POST
def student_submitted_exams_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentSubmittedExams.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_submitted_exams_list')

@login_required
@require_POST
def student_submitted_assignment_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentSubmittedAssignment.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_submitted_assignment_list')

@login_required
@require_POST
def student_exams_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentExams.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_exams_list')

@login_required
@require_POST
def student_assignment_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentAssignment.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_assignment_list')

@login_required
@require_POST
def student_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Students.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('student_list')

@login_required
@require_POST
def application_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Applications.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('application_list')

@login_required
@require_POST
def staff_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Staffs.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('staff_list')

@login_required
@require_POST
def assignment_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Assignments.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('assignment_list')

@login_required
@require_POST
def reference_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        References.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('reference_list')

@login_required
@require_POST
def support_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Support.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('support_list')

@login_required
@require_POST
def uploads_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Uploads.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('uploads_list')

@login_required
@require_POST
def payments_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Payments.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('payments_list')

@login_required
@require_POST
def church_codes_usage_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        ChurchCodesUsage.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('church_codes_usage_list')

@login_required
@require_POST
def users_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Users.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('users_list')

@login_required
@require_POST
def church_code_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        ChurchCodes.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('church_code_list')

@login_required
@require_POST
def church_admin_applications_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        ChurchAdminApplications.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('church_admin_applications_list')

