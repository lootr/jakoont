import datetime
from sqlalchemy import Column, Unicode, Integer, ForeignKey, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation

Base = declarative_base()
__metadata__ = Base.metadata

class Project(Base):
    __tablename__ = 'projects'

    id            = Column(Integer, primary_key=True)
    name          = Column(Unicode(32), nullable=False)
    creation_date = Column(DateTime, nullable=False, default=datetime.datetime.now)


class User(Base):
    __tablename__ = 'users'

    id            = Column(Integer, primary_key=True)
    username      = Column(Unicode(32), nullable=False)
    firstname     = Column(Unicode(32))
    lastname      = Column(Unicode(32))


class Entry(Base):
    __tablename__ = 'entries'

    id            = Column(Integer, primary_key=True)
    project_id    = Column(ForeignKey(Project.id), nullable=False)
    user_id       = Column(ForeignKey(User.id), nullable=False)
    amount        = Column(Float, nullable=False)


Entry.project = relation(Project, backref="entries")
Entry.user = relation(User, backref="entries")
