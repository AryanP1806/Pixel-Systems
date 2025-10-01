from django.shortcuts import render

# Create your views here.


from django.shortcuts import render

def home(request):
    """
    Renders the main overview page of the website.
    """
    return render(request, 'core/index.html')

def about(request):
    """
    Optional: About Us page
    """
    return render(request, 'core/about.html')
