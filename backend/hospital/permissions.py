from rest_framework.permissions import BasePermission, SAFE_METHODS

def role_of(user):
    if user.is_superuser: return "Admin"
    try: return user.profile.role
    except Exception: return ""

class HospitalPermission(BasePermission):
    """Role rules for the receptionist workflow; object data remains behind JWT auth."""
    def has_permission(self, request, view):
        role = role_of(request.user)
        if not role: return False
        action = getattr(view, "action", "")
        if role == "Admin": return True
        if role == "Receptionist":
            if request.method in SAFE_METHODS: return True
            allowed = {"patient": {"create", "update", "partial_update", "destroy"}, "diagnosis": {"create"}, "test": {"create", "update", "partial_update"}, "caretaker": {"create"}, "person": {"create"}}
            return action in allowed.get(getattr(view, "basename", ""), set())
        if role == "Doctor":
            return request.method in SAFE_METHODS or (view.basename in ("diagnosis", "test") and action in ("create", "update", "partial_update"))
        return False
