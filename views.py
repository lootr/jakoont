from django.http import HttpResponse
from django.shortcuts import render_to_response
from jakoont.models import Project

def index(req):
    projects = Project.objects.all()
    return render_to_response('index.html', {'projects': projects})
