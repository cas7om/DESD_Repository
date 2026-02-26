from .models import User

SESSION_USER_ID_KEY = "auth_user_id"

def current_user(request):
    user_id = request.session.get(SESSION_USER_ID_KEY)
    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()
    return {
        "current_user": user,
        "is_logged_in": user is not None,
    }