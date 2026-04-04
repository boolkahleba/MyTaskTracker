from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import HistoricalTaskData


@login_required
def historical_data_list_view(request):
    items = HistoricalTaskData.objects.all().order_by('-completed_at')
    return render(request, 'predictions/historical_data_list.html', {
        'items': items,
    })