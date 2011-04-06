from __future__ import with_statement

from nagare import component, presentation

from jakoont.project import Project, ProjectEditor

class Jakoont(object):
    def __init__(self):
        self.project_index = component.Component(Project(), "index")

    def login(self):
        pass

    def edit(self, comp, pid):
        return comp.call(Project(pid), "edit")

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
    h << self.project_index
    return h.root

# ---------------------------------------------------------------

app = Jakoont
