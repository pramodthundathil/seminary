from django.shortcuts import redirect, HttpResponse
from django.contrib import messages 
from django.contrib.auth import logout

def role_redirection(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                role = request.user.user_roles.all()[0].role.name
            except:
                role = None
            print(role,"-------------------------------")
            # Check if user is Church Admin
            from home.models import ChurchAdmins
            is_church_admin = False
            try:
                if request.user.church_admin or ChurchAdmins.objects.filter(student__user=request.user, deleted_at__isnull=True).exists():
                    is_church_admin = True
            except Exception:
                pass

            if role == "Student":
                return redirect("student_home")
            elif is_church_admin or role == "Church Admin":
                return redirect("church_admin_dashboard")
            elif role == "Church User":
                return redirect("church_user_home")
            elif role is not None:
                return view_func(request, *args, **kwargs)
            else:
                logout(request)
                messages.error(request, "You are not authorized to access this page.Make Sure that you are logged in as the correct user.")
                return redirect('signin')
        else:
            return redirect('signin')
    return wrapper_func