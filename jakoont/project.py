from __future__ import with_statement

import itertools
from nagare import presentation, var
from nagare.database import session
from sqlalchemy.sql import func

from jakoont.models import Project as DBProject,\
    User as DBUser, Entry as DBEntry

class Project(object):
    def __init__(self, project_id=None):
        self.project_id = project_id
        self.initialize()

    @property
    def _v_project(self):
        return session.query(DBProject).get(self.project_id)

    def initialize(self):
        self.entry_users = session.query(DBUser)\
            .join(DBEntry)\
            .filter(DBEntry.project_id == self.project_id)\
            .all()
        self.avg_amount = session.query(func.sum(DBEntry.amount))\
            .filter_by(project_id=self.project_id)\
            .first()[0]
        if self.avg_amount is not None:
            self.avg_amount /= len(self.entry_users)
        self.users_amounts = dict(
            (user.username, session.query(func.sum(DBEntry.amount))\
                 .filter_by(project_id=self.project_id)\
                 .filter_by(user_id=user.id)\
                 .first()[0])
            for user in self.entry_users
            )
        self.entry_user_id = var.Var()

    def get_projects(self):
        return session.query(DBProject).all()

    def login(self):
        pass

    def add_entry(self, amount):
        session.add(DBEntry(amount=amount,
                            user_id=self.entry_user_id(),
                            project_id=self.project_id))
        self.initialize()
    
    def remove_entry(self, eid):
        session.query(DBEntry).filter_by(id=eid).delete()
        self.initialize()

    def get_all_users(self):
        return session.query(DBUser).all()
    
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
                if u1a > self.avg_amount or u2a < self.avg_amount or u1a > u2a: continue
                to_give = u2a - self.avg_amount
                if to_give > u1a:
                    to_give = u1a
                to_give = round(to_give, precision)
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

@presentation.render_for(Project, "index")
def render(self, h, comp, *args):
    with h.ul:
        for proj in self.get_projects():
            h << h.li(h.a(proj.name).action(lambda pid=proj.id: comp.call(Project(pid), "edit")))
    return h.root

@presentation.render_for(Project, "edit")
def render(self, h, comp, *args):
    project = self._v_project
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
                            for user in self.get_all_users():
                                h << h.option(user.username, value=user.id)
                    h << h.td(h.input().action(self.add_entry))
                    h << h.td(h.input(type_="submit"))
    h << comp.render(h, "repartition")
    h << h.a("Home").action(comp.answer)    

    return h.root

@presentation.render_for(Project, "repartition")
def render(self, h, *args):
    precision = 2
    if self.avg_amount is not None:
        h << h.p(u"Average amount is %.2f, " % self.avg_amount)
        with h.ul:
            while precision >= 0:
                with h.li:
                    h << u"a %d decimales pres" %precision
                    with h.ul:
                        for u1, u2s in self.get_user_repartition(precision).items():
                            h << h.li(u"%s donne:" %u1)
                            h << h.ul(h.li("%.2f a %s" %(amount, u2)) for u2, amount in u2s.items())
                precision -= 1

    return h.root
