from flask_sqlalchemy import SQLAlchemy
from . import db

class Version(db.Model):
	__tablename__ = 'version'
	id = db.Column(db.Integer, primary_key=True)
	gamever = db.Column(db.Integer)
	modtime = db.Column(db.String(64))
	totalsongs = db.Column(db.Integer)
	totalslots = db.Column(db.Integer)

class Song(db.Model):
	__tablename__ = 'song'
	id = db.Column(db.Integer, primary_key=True)
	songid = db.Column(db.Integer, unique=True, index=True)
	title = db.Column(db.String(128), index=True)
	alias = db.Column(db.String(128), index=True)
	genre = db.Column(db.String(128), index=True)
	artist = db.Column(db.String(128), index=True)
	version = db.Column(db.String(32), index=True)
	spn = db.Column(db.Integer)
	sph = db.Column(db.Integer)
	spa = db.Column(db.Integer)
	dpn = db.Column(db.Integer)
	dph = db.Column(db.Integer)
	dpa = db.Column(db.Integer)
	spb = db.Column(db.Integer)
	volume = db.Column(db.Integer)
	bgadelay = db.Column(db.Integer)
	bganame = db.Column(db.String(32), index=True)
	font = db.Column(db.Integer)
	otherfolder = db.Column(db.Boolean, default=False)

	def __repr__(self):
		return '<Song %r>' % self.title

class Rawdata(db.Model):
	__tablename__ = 'rawdata'
	id = db.Column(db.Integer, primary_key=True)
	songid = db.Column(db.Integer, unique=True, index=True)
	block0 = db.Column(db.String(128), index=True)
	block1 = db.Column(db.String(128), index=True)
	block2 = db.Column(db.String(128), index=True)
	block3 = db.Column(db.String(128), index=True)
	block4 = db.Column(db.String(128), index=True)
	block5 = db.Column(db.String(128), index=True)
	block6 = db.Column(db.String(128), index=True)
	block7 = db.Column(db.String(128), index=True)
	block8 = db.Column(db.String(128), index=True)
	block9 = db.Column(db.String(128), index=True)
	block10 = db.Column(db.String(128), index=True)
	block11 = db.Column(db.String(128), index=True)
	block12 = db.Column(db.String(128), index=True)
