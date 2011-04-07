import datetime
from nagare import database
from sqlalchemy import Column, Unicode, Integer, ForeignKey, DateTime, Float, UnicodeText, ForeignKeyConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import exc, relation
from sqlalchemy.orm.properties import ColumnProperty

Base = declarative_base()
__metadata__ = Base.metadata

def _repr(self):
    cls = self.__class__
    return "<%s %s />" %(cls.__name__, ' '.join('%s=%r' %(p.key, getattr(self, p.key)) for p in self.__mapper__.iterate_properties if isinstance(p, ColumnProperty)))

Base.__repr__ = _repr

def _create_pu_by_user(user, balancing=None):
    if isinstance(user, tuple):
        return _create_pu_by_user(*user)
    return ProjectUser(user=user, balancing=balancing)

class Project(Base):
    __tablename__   = 'projects'

    id              = Column(Integer, primary_key=True)
    name            = Column(Unicode(32), nullable=False)
    creation_date   = Column(DateTime, nullable=False, default=datetime.datetime.now)

    users           = association_proxy("project_users", "user", creator=_create_pu_by_user)

    def add_entry(self, user, *args, **kwargs):
        attrs = dict(project=self, user=user)
        try:
            pu = database.session.query(ProjectUser).filter_by(**attrs).one()
        except exc.NoResultFound:
            pu = ProjectUser(**attrs)
            database.session.add(pu)
            database.session.flush()
        return pu.add_entry(*args, **kwargs)


class User(Base):
    __tablename__   = 'users'

    id              = Column(Integer, primary_key=True)
    username        = Column(Unicode(32), nullable=False)
    firstname       = Column(Unicode(32))
    lastname        = Column(Unicode(32))


class ProjectUser(Base):
    __tablename__   = 'projects_users'

    project_id      = Column(ForeignKey(Project.id), primary_key=True)
    user_id         = Column(ForeignKey(User.id), primary_key=True)
    balancing       = Column(Integer, default=1)

    project         = relation(Project, backref="project_users")
    user            = relation(User, backref="project_users")

    def add_entry(self, amount, comment=None):
        self.entries.append(Entry(project_id=self.project_id,
                                  user_id=self.user_id,
                                  amount=amount,
                                  comment=comment))


class Entry(Base):
    __tablename__   = 'entries'
    __table_args__  = (
        ForeignKeyConstraint(['project_id', 'user_id'],
                             ['projects_users.project_id', 'projects_users.user_id']),
        {})

    id              = Column(Integer, primary_key=True)
    project_id      = Column(ForeignKey(Project.id), nullable=False)
    user_id         = Column(ForeignKey(User.id), nullable=False)
    amount          = Column(Float, nullable=False)
    comment         = Column(UnicodeText, nullable=False, default=u"")

    project         = relation(Project, backref="entries")
    user            = relation(User, backref="entries")
    project_user    = relation(ProjectUser, backref="entries")
