import os, time, math
from flask import current_app, render_template, redirect, url_for, flash, request, abort
from . import main
from .forms import WorkUploadForm
from .. import db
from ..models import Version, Song, Rawdata
from flask_sqlalchemy import get_debug_queries

@main.route('/', methods=['GET', 'POST'])
def index():
	form = WorkUploadForm()
	vername = ["1st style", "substream", "2nd style", "3rd style", "4th style", "5th style",
			"6th style", "7th style", "8th style", "9th style", "10th style", "IIDX RED",
			"HAPPY SKY", "DistorteD", "GOLD", "DJ TROOPERS", "EMPRESS", "SIRIUS", "Resort Anthem",
			"Lincle", "tricoro", "SPADA", "PENDUAL", "copula", "SINOBUZ", "CANNON BALLERS"]
	blksize = 64
	pointer = 0
	headersize = 16
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
		infoline = workfile.read(headersize)
		pointer = pointer + headersize
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
		workfile.seek(pointer)
		slotdata = workfile.read(totalslots * 2)
		pointer = pointer + totalslots * 2
		musicid = [1000]
		if len(slotdata) < totalslots * 2:
			flash('文件slot数据损坏！')
			return redirect(url_for('.index'))
		for i in range(0, totalslots * 2, 2):
			j = int(slotdata[i]) + int(slotdata[i+1])
			if j == 255 * 2 or j == 0:
				continue
			musicid.append(math.floor(i / 2))
		if len(musicid) > totalsongs:
			flash('slot数目大于歌曲总数')
			return redirect(url_for('.index'))
		if len(musicid) < totalsongs:
			flash('slot数目小于歌曲总数')
			return redirect(url_for('.index'))
		alldata = Rawdata.query.all()
		if alldata != []:
			for data in alldata:
				db.session.delete(data)
			db.session.commit()
		for i in range(0, totalsongs):
			block = []
			for j in range(0, 13):
				workfile.seek(pointer)
				block.append(workfile.read(blksize))
				pointer = pointer + blksize
				if len(block[j]) < blksize:
					flash('文件block数据损坏！')
					return redirect(url_for('.index'))
			rawdata = Rawdata(songid=musicid[i], block0=block[0], block1=block[1], block2=block[2],
				block3=block[3], block4=block[4], block5=block[5], block6=block[6], block7=block[7],
				block8=block[8], block9=block[9], block10=block[10], block11=block[11], block12=block[12])
			db.session.add(rawdata)
		allsongs = Song.query.all()
		if allsongs != []:
			for song in allsongs:
				db.session.delete(song)
			db.session.commit()
		flash('文件上传成功')
		return redirect(url_for('.index'))
	return render_template('index.html', form=form, version=version, gtext=gamever_text)

@main.route('/management')
def management():
	abort(404)
	return render_template('management.html')

@main.route('/add')
def add():
	abort(404)
	return render_template('add.html')

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
