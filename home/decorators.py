from django.shortcuts import redirect 
from django.contrib import messages 


def role_redirection(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                role = request.user.user_roles.all()[0].role_id.name
            except:
                role = None
            print(role,"-------------------------------")
            if role == "Admin":
                return view_func(request, *args, **kwargs)
            else:
                return redirect("student_index")
        else:
            messages.info(request,"Please login to continue")
            return redirect('signin')
    return wrapper_func