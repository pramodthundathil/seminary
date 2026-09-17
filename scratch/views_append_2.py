
@login_required
@require_POST
def course_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
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
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_books_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentsBooks.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_subjects_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentsSubjects.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_instructors_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentsInstructor.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_uploads_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentsUploads.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_exams_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentsExams.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_assignment_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        StudentsAssignment.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def student_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Students.objects.filter(id__in=ids).delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def staff_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
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
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def assignment_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
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
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def reference_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        BookReferences.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def payments_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
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
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def church_codes_usage_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        ChurchAdmins.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def users_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        Users.objects.filter(id__in=ids).update(deleted_at=timezone.now(), is_active=False)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

@login_required
@require_POST
def church_code_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        ChurchLoginCodeSettings.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Successfully deleted {len(ids)} items'})
        messages.success(request, f'Successfully deleted {len(ids)} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))

