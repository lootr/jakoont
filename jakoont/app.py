from __future__ import with_statement

import os
import itertools
from nagare import presentation, var
from nagare.database import session
from sqlalchemy.sql import func

from jakoont.models import Project, User, Entry

class Jakoont(object):
    def __init__(self):
        self.project = session.query(Project).first()
        self.all_users = session.query(User).all()
        self.entry_users = session.query(User)\
            .join(Entry)\
            .filter(Entry.project_id == self.project.id)\
            .all()
        self.entry_user_id = var.Var()

    def add_entry(self, amount):
        session.add(Entry(amount=amount,
                          user_id=self.entry_user_id(),
                          project=self.project))
    
    def get_avg_amount(self):
        avg_amount = session.query(func.sum(Entry.amount))\
            .filter_by(project_id=self.project.id)\
            .first()[0]
        if avg_amount is not None:
            return avg_amount / len(self.entry_users)
    
    def get_users_amounts(self):
        d = {}
        for user in self.entry_users:
            d[user] = session.query(func.sum(Entry.amount))\
                .filter_by(project_id=self.project.id)\
                .filter_by(user_id=user.id)\
                .first()[0]
        return d

    def get_user_repartition(self):
        avg_amount = self.get_avg_amount()
        users_amounts = self.get_users_amounts()
        d = {}
        d2 = None
        while d2 != d:
            d2 = d.copy()
            for u1, u2 in itertools.product(self.entry_users, repeat=2):
                if u1 == u2: continue
                u1a = users_amounts[u1]
                u2a = users_amounts[u2]
                if u1a > avg_amount or u2a < avg_amount or u1a > u2a: continue
                to_give = u2a - avg_amount
                if to_give > u1a:
                    to_give = u1a
                to_give = round(to_give, 2)
                if to_give:
                    users_amounts[u1] += to_give
                    users_amounts[u2] -= to_give
                    d[u1][u2] = d.setdefault(u1, {}).setdefault(u2, 0.) + to_give
        return d
    
    def login(self):
        pass

    def remove_entry(self, eid):
        session.query(Entry).filter_by(id=eid).delete()

@presentation.render_for(Jakoont)
def render(self, h, comp, *args):
    h.head.title("Accueil - Jakoont")
    h.head.css_url('/static/jakoont/jakoont.css')
    with h.div(id="main"):
        h << comp.render(h, "header")
        h << comp.render(h, "middle")
        h << comp.render(h, "footer")

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
    h << h.h1(self.project.name)
    with h.form:
        with h.table:
            with h.thead:
                h << h.th("User")
                h << h.th("Amount")
            with h.tbody:
                for entry in self.project.entries:
                    with h.tr:
                        h << h.td(entry.user.username)
                        h << h.td(entry.amount)
                        h << h.td(h.a("Remove").action(lambda eid=entry.id: self.remove_entry(eid)))
                with h.tr:
                    with h.td:
                        with h.select(class_="userlist").action(self.entry_user_id):
                            for user in self.all_users:
                                h << h.option(user.username, value=user.id)
                    h << h.td(h.input().action(self.add_entry))
                    h << h.td(h.input(type_="submit"))
    
    avg_amount = self.get_avg_amount()
    ur = self.get_user_repartition()
    if avg_amount is not None:
        with h.p:
            h << u"Average amount is %.2f, " % avg_amount
        with h.ul:
            for u1 in ur:
                h << h.li(u"%s donne:" %u1.username)
                with h.ul:
                    for u2, amount in ur[u1].items():
                        h << h.li("%.2f a %s" %(amount, u2.username))
    return h.root

# ---------------------------------------------------------------

app = Jakoont
