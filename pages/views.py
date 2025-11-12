from django.shortcuts import render


def home(request):
    """Render the placeholder template so you can drop in your design files."""
    return render(request, "pages/home.html")
