import hashlib, bleach, math
from flask_sqlalchemy import SQLAlchemy
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager, db
from flask import current_app, request, url_for
from datetime import datetime
from markdown import markdown

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	default = db.Column(db.Boolean, default=False, index=True)
	permissions = db.Column(db.Integer)
	students = db.relationship('User', backref='role', lazy='dynamic')
	teachers = db.relationship('Teacher', backref='role', lazy='dynamic')
	
	@staticmethod
	def insert_roles():
		roles = {
			'Student': (Permission.CLASS, True), 
			'Groupleader': (Permission.CLASS | Permission.SCORE, False), 
			'Teacher': (Permission.CLASS | Permission.SCORE | Permission.EDIT, False), 
			'Administrator': (0xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name
		
class Permission:
	CLASS = 0x01
	SCORE = 0x02
	EDIT = 0x04
	ADMINISER = 0x80

class User(UserMixin, db.Model):
	__tablename__ = 'users'
	
	id = db.Column(db.Integer, primary_key=True)
	studentid = db.Column(db.Integer, unique=True, index=True)
	username = db.Column(db.String(16), unique=True, index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	grade = db.Column(db.String(16))
	classname = db.Column(db.String(16), db.ForeignKey('classes.classname'))
	group = db.Column(db.Integer, index=True, default=0)
	totalscore = db.Column(db.Integer, index=True, default=60)
	perfscore = db.Column(db.Integer, index=True, default=60)
	workscore = db.Column(db.Integer, index=True, default=0)
	testscore = db.Column(db.Integer, index=True, default=0)
	login_ip = db.Column(db.String(32))
	password_hash = db.Column(db.String(128))
	
	@property
	def password(self):
		raise AttributeError('不可以读取原密码')
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
	def can(self, permissions):
		return self.role is not None and (self.role.permissions & permissions) == permissions
	def is_student(self):
		return self.can(Permission.CLASS)
	def is_groupleader(self):
		return self.can(Permission.SCORE)
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		if self.role is None:
			self.role = Role.query.filter_by(default=True).first()
		if self.grade is None or self.classname is None:
			grade_num = math.floor(self.studentid / 10000)
			grade = Grade.query.filter_by(grade_num=grade_num).first()
			self.grade = grade.grade_name
			self.classname = grade.grade_name + '(' + str(math.floor(self.studentid / 100) % 100) + ')'
		if self.password_hash is None:
			self.password_hash = generate_password_hash('666666')
			
	def __repr__(self):
		return '<User %r>' % self.username

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64), index=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	timestamp_update = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('teachers.tea_id'))
	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 
			'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'p', 'br']
		target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'), 
			tags=allowed_tags, strip=True))

db.event.listen(Post.body, 'set', Post.on_changed_body)

class Classes(db.Model):
	__tablename__ = 'classes'
	id = db.Column(db.Integer, primary_key=True)
	grade = db.Column(db.String(16))
	classname = db.Column(db.String(16), unique=True)
	teacher = db.Column(db.Integer, db.ForeignKey('teachers.tea_id'))
	test_on = db.Column(db.Integer, default=0)

class Teacher(UserMixin, db.Model):
	__tablename__ = 'teachers'
	id = db.Column(db.Integer, primary_key=True)
	tea_id = db.Column(db.Integer, unique=True, index=True)
	tea_name = db.Column(db.String(16), index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	password_hash = db.Column(db.String(128))
	class_on = db.Column(db.String(16))
	course_on = db.Column(db.Integer)
	
	@property
	def password(self):
		raise AttributeError('不可以读取原密码')
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
	def can(self, permissions):
		return self.role is not None and (self.role.permissions & permissions) == permissions
	def is_administrator(self):
		return self.can(Permission.ADMINISER)
	def is_teacher(self):
		return self.can(Permission.EDIT)
		
	def __init__(self, **kwargs):
		super(Teacher, self).__init__(**kwargs)
		if self.role is None:
			if self.tea_name == current_app.config['FLASKY_ADMIN']:
				self.role = Role.query.filter_by(permissions=0xff).first()
			if self.role is None:
				self.role = Role.query.filter_by(id=3).first()
	
	def __repr__(self):
		return '<Teacher %r>' % self.tea_name

class Course(db.Model):
	__tablename__ = 'course'
	id = db.Column(db.Integer, primary_key=True)
	grade = db.Column(db.String(160), index=True)
	chapter = db.Column(db.Integer)
	chap_name = db.Column(db.String(128), index=True)
	section = db.Column(db.Integer)
	title = db.Column(db.String(128), index=True)
	
class Grade(db.Model):
	__tablename__ = 'grade'
	id = db.Column(db.Integer, primary_key=True)
	grade_num = db.Column(db.Integer)
	grade_name = db.Column(db.String(16))

class Sysconfig(db.Model):
	__tablename__ = 'sysconfig'
	id = db.Column(db.Integer, primary_key=True)
	weeknum = db.Column(db.Integer)
	suffix = db.Column(db.String(16))

class Performance(db.Model):
	__tablename__ = 'performance'
	id = db.Column(db.Integer, primary_key=True)
	classname = db.Column(db.String(16), index=True)
	groupnum = db.Column(db.Integer)
	weeknum = db.Column(db.Integer)
	commentid = db.Column(db.Integer)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	deletion = db.Column(db.Integer, default=0)

class PerfComments(db.Model):
	__tablename__ = 'perfcomments'
	id = db.Column(db.Integer, primary_key=True)
	comment = db.Column(db.String(128), index=True)
	score = db.Column(db.Integer)

class PerfLog(db.Model):
	__tablename__ = 'perflog'
	id = db.Column(db.Integer, primary_key=True)
	studentid = db.Column(db.Integer)
	perfid = db.Column(db.Integer)
	
class StudentWork(db.Model):
	__tablename__ = 'studentwork'
	id = db.Column(db.Integer, primary_key=True)
	studentid = db.Column(db.Integer)
	weeknum = db.Column(db.Integer)
	workscore = db.Column(db.Integer, default=0)
	filename = db.Column(db.String(128), index=True)
	
class TestPaper(db.Model):
	__tablename__ = 'testpaper'
	id = db.Column(db.Integer, primary_key=True)
	grade = db.Column(db.String(16), index=True)
	questno = db.Column(db.Integer, index=True)
	question = db.Column(db.String(256))
	opta = db.Column(db.String(256))
	optb = db.Column(db.String(256))
	optc = db.Column(db.String(256))
	optd = db.Column(db.String(256))
	ans = db.Column(db.Integer)
	
class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False
	def is_administrator(self):
		return False

@login_manager.user_loader
def load_user(user):
	loaded = Teacher.query.get(int(user))
	if loaded is None:
		loaded = User.query.get(int(user))
	return loaded

login_manager.anonymous_user = AnonymousUser
