from django.shortcuts import render # We import render instead of HttpResponse

def index(request):
    # This looks for 'home/index.html' inside the templates folder
    return render(request, 'home/index.html')