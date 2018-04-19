import os, random
from datetime import datetime
from flask import current_app, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from . import main
from .forms import EditProfileAdminForm
from .. import db
from ..models import User, Permission, Role, Post, Teacher, Course, \
	Classes, Grade, Sysconfig, TestPaper
from flask_sqlalchemy import get_debug_queries
from werkzeug.utils import secure_filename

@main.route('/', methods=['GET', 'POST'])
def index():
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
	posts = pagination.items
	return render_template('index.html', posts=posts, pagination=pagination)

@main.route('/news/<int:id>')
def news(id):
	posts = Post.query.get_or_404(id)
	author = Teacher.query.filter_by(tea_id=posts.author_id).first()
	inside_post = True
	return render_template('news.html', posts=[posts], inside_post=inside_post, author=author)

@main.route('/courses')
def courses():
	if current_user.is_anonymous:
		show_all = True
		show_grade = None
		active_course = None
	else:
		if current_user.role_id == 1 or current_user.role_id == 3:
			show_all = True
			show_grade = None
			active_course = Teacher.query.get(current_user.id).course_on
		if current_user.role_id == 2 or current_user.role_id == 4:
			show_all = False
			show_grade = current_user.grade
			teacher = Classes.query.filter_by(classname=current_user.classname).first().teacher
			active_course = Teacher.query.filter_by(tea_id=teacher).first().course_on
	courses = Course.query.order_by(Course.grade.asc(), Course.chapter.asc(), Course.section.asc()).all()
	grades = Grade.query.order_by(Grade.id).all()
	return render_template('courses.html', courses=courses, grades=grades, 
		show_all=show_all, show_grade=show_grade, active_course=active_course)

@main.route('/course/<int:id>')
def course(id):
	course = Course.query.get_or_404(id)
	includes = 'courses/' + course.title + '.html'
	return render_template('course.html', course=course, includes=includes)

@main.route('/russianroulette')
@login_required
@permission_required(Permission.EDIT)
def russianroulette():
	aclass = Classes.query.get_or_404(current_user.class_on)
	stunum = User.query.filter_by(classname=aclass.classname).count()
	if stunum < 1:
		flash('该班还没有学生')
		return redirect(url_for('.index'))
	students = User.query.filter_by(classname=aclass.classname).all()
	chosen = students[random.randint(0, stunum-1)]
	return render_template('russianroulette.html', chosen=chosen)

@main.route('/beforetestinst')
@login_required
def beforetestinst():
	student = User.query.get_or_404(current_user.id)
	return render_template('beforetestinst.html', student=student)

@main.route('/testing')
@login_required
def testing():
	aclass = Classes.query.filter_by(classname=current_user.classname).first()
	if aclass.test_on == 0:
		flash('考试尚未开始，请稍等！')
		return redirect(url_for('.beforetestinst'))
	else:
		totalquests = aclass.test_on
		quests = TestPaper.query.filter_by(grade=aclass.grade).all()
		random.shuffle(quests)
	return render_template('testing.html', quests=quests, totalquests=totalquests)

@main.route('/microlesson')
def microlesson():
	if current_user.can(Permission.CLASS) == False:
		flash('请登录后再进入微课超市')
		return redirect(url_for('main.index'))
	abort(404)
	return render_template('microlesson.html')

@main.after_app_request
def after_request(response):
	for query in get_debug_queries():
		if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIMEOUT']:
			current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
				(query.statement, query.parameters, query.duration, query.context))
	return response
