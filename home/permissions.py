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
        
        return view_func(request, *args, **kwargs)
    return wrapper
