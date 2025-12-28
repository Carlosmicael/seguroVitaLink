from multiprocessing import context
from django.shortcuts import render


def dashboard(request):
    context = {
        
    }

    return render(request, 'components/dashboard/dashboard.html', context)
