from django.shortcuts import redirect 
from django.contrib import messages 


def role_redirection(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                role = request.user.user_roles.first().role.name if request.user.user_roles.exists() else "No Role"
            except:
                role = None
            print(role,"-------------------------------")
            
            # Handle role-based redirection
            if role == "Student":
                return redirect('student_home')
            elif role == "Church User":  
                return redirect('church_user_home')
            elif role == "Admin":
                return view_func(request, *args, **kwargs)
            else:
                return redirect("home/")
        else:
            messages.info(request,"Please login to continue")
            return redirect('signin')
    return wrapper_func