import os, time
from flask import current_app, render_template, redirect, url_for, flash, request, abort
from . import main
from .forms import WorkUploadForm
from .. import db
from ..models import Version, Song
from flask_sqlalchemy import get_debug_queries

@main.route('/', methods=['GET', 'POST'])
def index():
	form = WorkUploadForm()
	vername = ["1st style", "substream", "2nd style", "3rd style", "4th style", "5th style",
			"6th style", "7th style", "8th style", "9th style", "10th style", "IIDX RED",
			"HAPPY SKY", "DistorteD", "GOLD", "DJ TROOPERS", "EMPRESS", "SIRIUS", "Resort Anthem",
			"Lincle", "tricoro", "SPADA", "PENDUAL", "copula", "SINOBUZ", "CANNON BALLERS"]
	blksize = 64
	version = Version.query.get(1)
	if version is not None:
		gamever_text = vername[version.gamever]
	else:
		gamever_text = ''
	if form.validate_on_submit():
		upload_folder = 'app/static/workfiles'
		if not os.path.exists(upload_folder):
			os.makedirs(upload_folder)
		workfile = form.workfile.data
		filename = 'music_data.bin'
		save_path = os.path.join(upload_folder, filename)
		infoline = workfile.read(16)
		if len(infoline) != 16 or infoline[0:4] != b'IIDX':
			flash('文件头有问题！')
			return redirect(url_for('.index'))
		if int(infoline[4]) > 25:
			flash('不支持该版本！')
			return redirect(url_for('.index'))
		gamever = int(infoline[4])
		totalsongs = int(infoline[9]) * 16 * 16 + int(infoline[8])
		totalslots = int(infoline[11]) * 16 * 16 + int(infoline[10])
		workfile.save(save_path)
		modtime = time.ctime(os.path.getmtime(save_path))
		if version is None:
			version = Version(gamever=gamever, modtime=modtime, totalsongs=totalsongs, totalslots=totalslots)
		else:
			version.gamever = gamever
			version.modtime = modtime
			version.totalsongs = totalsongs
			version.totalslots = totalslots
		db.session.add(version)
		allsongs = Song.query.all()
		if allsongs != []:
			db.session.delete(songs)
		
		flash('文件上传成功')
		return redirect(url_for('.index'))
	return render_template('index.html', form=form, version=version, gtext=gamever_text)

@main.route('/management')
def management():
	abort(404)
	return render_template('management.html')

@main.route('/exporter')
def exporter():
	abort(404)
	return render_template('exporter.html')

@main.after_app_request
def after_request(response):
	for query in get_debug_queries():
		if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIMEOUT']:
			current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
				(query.statement, query.parameters, query.duration, query.context))
	return response
