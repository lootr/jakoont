from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from jakoont.models import Project, Entry

def do(req, action, pid):
    if action == "edit":
        return edit(req, pid)
    elif action == "post":
        return post(req, pid)

def index(req):
    projects = Project.objects.all()
    return render_to_response('index.html', {'projects': projects})

def edit(req, pid):
    p = get_object_or_404(Project, pk=pid)
    users = User.objects.filter(pk__in=p.entry_set.values('user'))
    total = p.entry_set.aggregate(Sum('amount')).values()[0]
    return render_to_response('edit.html', {'project': p,
                                            'users': users,
                                            'amount_sum': total},
                              context_instance=RequestContext(req))

def post(req, pid):
    pid = int(pid)
    Entry(project_id=pid,
          creator_id=req.POST['user'],
          user_id=req.POST['user'],
          amount=req.POST['amount']
          ).save()
    return redirect('/edit/%d' %pid)
