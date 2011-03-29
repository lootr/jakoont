from __future__ import with_statement

from nagare import presentation
from nagare.database import session

from jakoont.models import Project as DBProject
from jakoont.project import Project

class Jakoont(object):
    def __init__(self):
        self.projects = session.query(DBProject).all()

    def login(self):
        pass

    def edit(self, comp, pid):
        return comp.becomes(Project(pid), "edit")

@presentation.render_for(Jakoont)
def render(self, h, comp, *args):
    h.head.title("Accueil - Jakoont")
    h.head.css_url('/static/jakoont/jakoont.css')
    with h.div(id="main"):
        h << comp.render(h, "header")
        h << comp.render(h, "middle")
        h << comp.render(h, "footer")
        pass

    return h.root

@presentation.render_for(Jakoont, "header")
def render(self, h, *args):
    with h.div(id="header"):
        h << h.span("Jakoont")
        with h.div(class_="topmenu"):
            with h.ul(class_="nav"):
                h << h.li(h.a("Connexion").action(self.login), class_="login")

    return h.root

@presentation.render_for(Jakoont, "footer")
def render(self, h, *args):
    return h.root

@presentation.render_for(Jakoont, "middle")
def render(self, h, comp, *args):
    h << h.ul(h.li(h.a(proj.name).action(lambda pid=proj.id: self.edit(comp, pid))) for proj in self.projects)
    return h.root

# ---------------------------------------------------------------

app = Jakoont
