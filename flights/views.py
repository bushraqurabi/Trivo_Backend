from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def test_view(request):
    try:
        return JsonResponse({
            "message": "Hello, Django is working!",
            "status": "success"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "message": "An error occurred",
            "error": str(e)
        }, status=500)