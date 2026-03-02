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
            if role == "Admin":
                return view_func(request, *args, **kwargs)
            elif role == "Student":
                return redirect("student_home")
            else:
                logout(request)
                messages.error(request, "You are not authorized to access this page.Make Sure that you are logged in as the correct user.")
                return redirect('signin')
        else:
            return redirect('signin')
    return wrapper_func