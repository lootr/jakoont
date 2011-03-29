from __future__ import with_statement

import itertools
from nagare import component, presentation, editor, var
from nagare.database import session
from nagare.validator import StringValidator, IntValidator
from sqlalchemy.sql import expression, func

from jakoont.models import Project as DBProject,\
    User as DBUser, Entry as DBEntry

class Project(object):
    def __init__(self, project_id=None):
        self.project_id = project_id
        self.name = None
        self.editor = ProjectEditor(self)
        if project_id:
            self.initialize()

    def initialize(self):
        self.entry_users = self._v_project.users
        self.avg_amount = session.query(func.sum(DBEntry.amount))\
            .filter_by(project_id=self.project_id)\
            .first()[0]
        if self.avg_amount is not None:
            self.avg_amount /= len(self.entry_users)
        self.users_amounts = dict(
            (user.username, session.query(func.sum(DBEntry.amount))\
                 .filter_by(project_id=self.project_id)\
                 .filter_by(user_id=user.id)\
                 .first()[0] or 0.)
            for user in self.entry_users)

    @property
    def _v_project(self):
        return session.query(DBProject).get(self.project_id)

    def get_projects(self):
        return session.query(DBProject).all()

    def login(self):
        pass

    def create(self, comp):
        res = comp.call(self.editor, "new")
        if res:
            proj = DBProject(name=self.name)
            session.add(proj)

    def get_user_repartition(self, precision=2):
        users_amounts = self.users_amounts.copy()
        d = {}
        d2 = None
        while d2 != d:
            d2 = d.copy()
            for u1, u2 in itertools.product(self.entry_users, repeat=2):
                if u1 == u2: continue
                u1a = users_amounts[u1.username]
                u2a = users_amounts[u2.username]
                if u1a > self.avg_amount or u2a < self.avg_amount or u1a > u2a:
                    continue
                to_give = round(u2a - self.avg_amount, precision)
                if to_give:
                    users_amounts[u1.username] += to_give
                    users_amounts[u2.username] -= to_give
                    d[u1.username][u2.username] = d.setdefault(u1.username, {})\
                        .setdefault(u2.username, 0.) + to_give

        for u1 in d.keys():
            for u2, a1 in d.get(u1, {}).items():
                a2 = d.get(u2, {}).get(u1, 0.)
                if not (a1 and a2): continue
                if a1 > a2:
                    d[u1][u2] = a1 - a2
                    del d[u2][u1]
                elif a1 < a2:
                    d[u2][u1] = a2 - a1
                    del d[u1][u2]
                else:
                    del d[u1][u2]
                    del d[u2][u1]
            if u1 in d and not d[u1]:
                del d[u1]
            if u2 in d and not d[u2]:
                del d[u2]
        
        return d


class ProjectEditor(editor.Editor):
    def __init__(self, project):
        super(ProjectEditor, self).__init__(project, ("project_id", "name",))
        self.name.validate(StringValidator)
        self.entry_user_id = var.Var()
        self.new_amount = editor.Property().validate(IntValidator)

    def add_entry(self):
        if super(ProjectEditor, self).commit((), ('new_amount',)):
            session.add(DBEntry(amount=self.new_amount(),
                                user_id=self.entry_user_id(),
                                project_id=self.project_id()))
            self.target.initialize()
    
    def remove_entry(self, eid):
        session.query(DBEntry).filter_by(id=eid).delete()
        self.target.initialize()

    def commit(self, comp):
        if super(ProjectEditor, self).commit(('name',), ('new_amount',)):
            comp.answer(self)


@presentation.render_for(Project, "index")
def render(self, h, comp, *args):
    with h.ul:
        for proj in self.get_projects():
            h << h.li(h.a(proj.name).action(lambda pid=proj.id: comp.call(Project(pid).editor)))
    h << h.a("New").action(lambda: self.create(comp))

    return h.root

@presentation.render_for(ProjectEditor, "new")
def render(self, h, comp, *args):
    with h.form:
        with h.table:
            with h.tr:
                h << h.th(h.label("Name"))
                h << h.td(h.input().action(self.name))

            with h.tr:
                h << h.td(h.input(type="submit").action(lambda: self.commit(comp)), colspan=2)
    return h.root

@presentation.render_for(ProjectEditor)
@presentation.render_for(ProjectEditor, "edit")
def render(self, h, comp, *args):
    project = self.target._v_project
    h << h.h1(project.name)
    with h.form:
        with h.table:
            with h.thead:
                h << h.th("User")
                h << h.th("Amount")
            with h.tbody:
                for entry in project.entries:
                    with h.tr:
                        h << h.td(entry.user.username)
                        h << h.td(entry.amount)
                        h << h.td(h.a("Remove").action(lambda eid=entry.id: self.remove_entry(eid)))
                with h.tr:
                    with h.td:
                        with h.select(class_="userlist").action(self.entry_user_id):
                            for user in self.target._v_project.users:
                                h << h.option(user.username, value=user.id)
                    h << h.td(h.input().action(self.new_amount).error(self.new_amount.error))
                    h << h.td(h.input(type="submit").action(self.add_entry))
    h << component.Component(self.target, "repartition")
    h << h.a("Home").action(comp.answer)    

    return h.root

@presentation.render_for(Project, "repartition")
def render(self, h, *args):
    precision = 2
    if self.avg_amount is not None:
        h << h.p(u"Average amount is %.2f, " % self.avg_amount)
        with h.ul:
            while precision >= 2:
                with h.li:
                    h << u"a %d decimales pres" %precision
                    with h.ul:
                        for u1, u2s in self.get_user_repartition(precision).items():
                            h << h.li(u"%s donne:" %u1)
                            h << h.ul(h.li("%.2f a %s" %(amount, u2)) for u2, amount in u2s.items())
                precision -= 1

    return h.root
