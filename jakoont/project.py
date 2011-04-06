from __future__ import with_statement

import itertools
from nagare import component, presentation, editor, var
from nagare import database
from nagare.validator import StringValidator, IntValidator
from sqlalchemy.sql import expression, func

from jakoont.models import Project as DBProject,\
    User as DBUser, Entry as DBEntry, ProjectUser as DBProjectUser

class Project(object):
    def __init__(self, project_id=None):
        self.project_id = project_id
        self.name = None
        self.users_ids = []
        self.editor = ProjectEditor(self)
        if project_id:
            self.initialize()

    def initialize(self):
        self.entry_users = self._v_project.users
        self.avg_amount = database.session.query(func.sum(DBEntry.amount))\
            .filter_by(project_id=self.project_id)\
            .first()[0]
        if self.avg_amount is not None:
            self.avg_amount /= len(self.entry_users)
        self.users_amounts = dict(
            (user.username, database.session.query(func.sum(DBEntry.amount))\
                 .filter_by(project_id=self.project_id)\
                 .filter_by(user_id=user.id)\
                 .first()[0] or 0.)
            for user in self.entry_users)

    @property
    def _v_project(self):
        if self.project_id is not None:
            return database.session.query(DBProject).get(self.project_id)

    def get_projects(self):
        return database.session.query(DBProject).all()

    def get_users(self):
        return database.session.query(DBUser).all()

    def login(self):
        pass

    def create(self, comp):
        res = comp.call(self.editor, "new")
        if res:
            proj = DBProject(name=self.name)
            for user_id in self.users_ids:
                pu = DBProjectUser(project_id=self.project_id,
                                   user_id=user_id)
                proj.project_users.append(pu)
            database.session.add(proj)

    def get_user_repartition(self, precision=2):
        users_amounts = self.users_amounts.copy()
        d = {}
        d2 = None

        # Each user that gave less than the average amount
        # gives to the others to balance repartition
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

        # Then avoid multiple shares between two users like:
        #        A gives X to B
        #        B gives Y to A
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # A gives X-Y to B (with X > Y)
        for u1 in d.keys():
            for u2, a1 in d.get(u1, {}).items():
                a2 = d.get(u2, {}).get(u1, 0.)
                # Two users must exist to balance shares
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
            # Remove null shares
            for u in [u1, u2]:
                if u in d and not d[u]:
                    del d[u]
        
        return d


class ProjectEditor(editor.Editor):
    def __init__(self, project):
        super(ProjectEditor, self).__init__(project, ("project_id", "name", "users_ids"))
        self.name.validate(StringValidator)
        self.users_ids#.validate(ListValidatorMeta(IntValidator))
        self.entry_user_id = var.Var()
        self.new_amount = editor.Property().validate(IntValidator)

    def add_entry(self):
        if super(ProjectEditor, self).commit((), ('new_amount',)):
            database.session.add(DBEntry(amount=self.new_amount.value,
                                         user_id=self.entry_user_id(),
                                         project_id=self.project_id()
                                         ))
            self.target.initialize()
    
    def remove_entry(self, eid):
        database.session.query(DBEntry).filter_by(id=eid).delete()
        self.target.initialize()

    def add_projectuser(self):
        if super(ProjectEditor, self).commit((), ('users_ids',)):
            database.session.add(DBProjectUser(project_id=self.project_id(),
                                               user_id=self.users_ids.value
                                               ))
            self.target.initialize()

    def commit(self, comp):
        if super(ProjectEditor, self).commit(('name', 'users_ids'), ('new_amount',)):
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
                h << h.th(h.label("Users"))
                opts = [h.option(u.username, value=u.id) for u in self.target.get_users()]
                h << h.td(h.select(opts, multiple=True).action(self.users_ids))

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
                            for user in project.users:
                                h << h.option(user.username, value=user.id)
                    h << h.td(h.input().action(self.new_amount).error(self.new_amount.error))
                    h << h.td(h.input(type="submit").action(self.add_entry))
                with h.tr:
                    opts = [h.option(u.username, value=u.id) for u in self.target.get_users()]
                    #h << h.td(h.select(opts).action(self.users_ids), colspan=2)
                    #h << h.td(h.input(type="submit").action(self.add_projectuser))

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
