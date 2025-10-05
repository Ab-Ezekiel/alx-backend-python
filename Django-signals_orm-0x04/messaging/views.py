# messaging/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages

@login_required
@require_http_methods(["GET", "POST"])
def delete_user(request):
    """
    Confirm and delete the authenticated user's account.
    GET: show confirmation page.
    POST: delete the user and log them out.
    """
    if request.method == "POST":
        user = request.user
        # Optionally store username for message before deletion
        username = user.username
        # Delete user — this triggers post_delete signals
        user.delete()
        # Log out the session (user is already deleted)
        logout(request)
        messages.success(request, f"Account {username} deleted.")
        # Redirect to home (adjust as needed)
        return redirect("/")
    # GET - show confirmation template (simple)
    return render(request, "messaging/confirm_delete.html", {"user": request.user})
