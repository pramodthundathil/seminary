
# ============= CHURCH CODES USAGE VIEWS =============

@login_required
def church_codes_usage_list(request):
    """List of Church Admins using codes"""
    per_page = int(request.GET.get('per_page', 10))
    page_number = request.GET.get('page')
    
    # Filter for active records
    admins = ChurchAdmins.objects.filter(deleted_at__isnull=True).select_related(
        'church_code', 
        'church_code__branches',
        'student'
    ).order_by('-created_at')
    
    paginator = Paginator(admins, per_page)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'per_page': per_page,
        'page_title': 'Church Admins'
    }
    return render(request, "admin/church_codes/list.html", context)

@login_required
def church_codes_usage_delete(request, admin_id):
    """Soft delete church admin usage"""
    try:
        admin = get_object_or_404(ChurchAdmins, id=admin_id, deleted_at__isnull=True)
        admin.deleted_at = timezone.now()
        admin.save()
        messages.success(request, "Church Admin deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting Church Admin: {str(e)}")
        
    return redirect('church_codes_usage_list')
