import os, time, math
from flask import current_app, render_template, redirect, url_for, flash, request, abort
from . import main
from .forms import WorkUploadForm, EditMusicForm, SearchForm, EditHeaderForm
from .. import db
from ..models import Version, Song, Rawdata
from flask_sqlalchemy import get_debug_queries

vername = ["1st style", "substream", "2nd style", "3rd style", "4th style", "5th style",
			"6th style", "7th style", "8th style", "9th style", "10th style", "IIDX RED",
			"HAPPY SKY", "DistorteD", "GOLD", "DJ TROOPERS", "EMPRESS", "SIRIUS", "Resort Anthem",
			"Lincle", "tricoro", "SPADA", "PENDUAL", "copula", "SINOBUZ", "CANNON BALLERS"]
blksize = 64
headersize = 16

@main.route('/', methods=['GET', 'POST'])
def index():
	form = WorkUploadForm()
	pointer = 0
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
		filename = 'music_data_' + str(request.remote_addr).replace('.', '_') + '.bin'
		save_path = os.path.join(upload_folder, filename)
		workfile.save(save_path)

		modtime = time.ctime(os.path.getmtime(save_path))
		workfile.seek(pointer)
		infoline = workfile.read(headersize)
		pointer = pointer + headersize
		if len(infoline) != 16 or infoline[0:4] != b'IIDX':
			print(len(infoline))
			print(infoline)
			flash('文件头有问题！')
			return redirect(url_for('.index'))
		gamever = infoline[4]
		if gamever > 25:
			flash('不支持该版本！')
			return redirect(url_for('.index'))
		totalsongs = int(infoline[9]) * 16 * 16 + int(infoline[8])
		totalslots = int(infoline[11]) * 16 * 16 + int(infoline[10])
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
		alldata = Rawdata.query.all()
		for data in alldata:
			title = data.block0.rstrip(b'\x00')
			alias = data.block1.rstrip(b'\x00')
			genre = data.block2.rstrip(b'\x00')
			artist = data.block3
			if artist[-1] == 0:
				fontcolor = 0
				artist = artist.rstrip(b'\x00')
			else:
				fontcolor = artist[-4] * 1000000 + artist[-3] * 1000 + artist[-2]
				artist = artist[:-4].rstrip(b'\x00')
			font = data.block4[20]
			version = data.block4[24]
			if data.block4[26] == 1:
				otherfolder = True
			else:
				otherfolder = False
			spn = data.block4[32]
			sph = data.block4[33]
			spa = data.block4[34]
			dpn = data.block4[35]
			dph = data.block4[36]
			dpa = data.block4[37]
			spb = data.block4[38]
			songid = int(data.block7[9]) * 16 * 16 + int(data.block7[8])
			if songid != data.songid:
				print('Music ID Wrong! Title is: %s' % title)
				print('Music ID Wrong! Music ID is: %d' % songid)
				print('Music ID Wrong! Slot ID is: %d' % data.songid)
			vol = int(data.block7[12])
			bgadelay = int(data.block7[25]) * 16 * 16 + int(data.block7[24])
			if bgadelay > 32767:
				bgadelay = bgadelay - 65536
			bganame = data.block7[28:48].rstrip(b'\x00')

			song = Song(title=title, alias=alias, genre=genre, artist=artist, version=version,
				spn=spn, sph=sph, spa=spa, dpn=dpn, dph=dph, dpa=dpa, spb=spb, songid=songid, volume=vol,
				bgadelay=bgadelay, bganame=bganame, font=font, fontcolor=fontcolor, otherfolder=otherfolder)
			db.session.add(song)
		flash('文件上传成功')
		return redirect(url_for('.index'))
	return render_template('index.html', form=form, version=version, gtext=gamever_text)

@main.route('/management', methods=['GET', 'POST'])
def management():
	allsongs = Song.query.all()
	songs = []
	converted_titles = []
	form = SearchForm()
	if allsongs != []:
		for i in range(0, len(vername)):
			songs.append([])
			converted_titles.append([])
			for song in allsongs:
				if song.version == i:
					songs[i].append(song)
					try:
						converted_titles[i].append(song.title.decode('shift-jis'))
					except UnicodeDecodeError as e:
						print(song.title[:e.start] + song.title[e.end:])
	
	if form.validate_on_submit():
		searcher = Song.query.filter_by(songid=form.songid.data).first()
		if searcher is None:
			flash('找不到歌曲')
		else:
			return redirect(url_for('.music', id=searcher.id))
	
	return render_template('management.html', vername=vername, songs=songs, 
		converted_titles=converted_titles, form=form)

@main.route('/music/<int:id>', methods=['GET', 'POST'])
def music(id):
	song = Song.query.get_or_404(id)
	rawdata = Rawdata.query.filter_by(songid=song.songid).first()
	try:
		converted_title = song.title.decode('shift-jis')
	except UnicodeDecodeError as e:
		flash('标题编码有问题')
		converted_title = song.title
	try:
		converted_artist = song.artist.decode('shift-jis')
	except UnicodeDecodeError as e:
		flash('艺术家编码有问题')
		converted_artist = song.artist
	try:	
		converted_genre = song.genre.decode('shift-jis')
	except UnicodeDecodeError as e:
		flash('曲风编码有问题')
		converted_genre = song.genre
	try:
		converted_alias = song.alias.decode('shift-jis')
	except UnicodeDecodeError as e:
		flash('英文标题编码有问题')
		converted_alias = song.alias
	try:
		converted_bganame = song.bganame.decode('shift-jis')
	except UnicodeDecodeError as e:
		flash('BGA名称编码有问题')
		converted_bganame = song.bganame
	converted_fontcolor = [math.floor(song.fontcolor / 1000000), 
		math.floor(song.fontcolor / 1000) % 1000, song.fontcolor % 1000]
	
	form = EditMusicForm(vername)
	if form.validate_on_submit():
		newblock4 = bytearray(rawdata.block4)
		newblock7 = bytearray(rawdata.block7)
		if song.songid != form.songid.data:
			check_song = Song.query.filter_by(songid=form.songid.data).first()
			if check_song is not None:
				flash('该歌曲ID已存在！')
				return redirect(url_for('.music', id=song.id))
			song.songid = form.songid.data
			rawdata.songid = form.songid.data
			newsongid = rawdata.songid.to_bytes(2, 'little')
			newblock7[8] = newsongid[0]
			newblock7[9] = newsongid[1]
		song.title = form.title.data.encode('shift-jis')
		rawdata.block0 = song.title + bytes(blksize - len(song.title))
		song.alias = form.alias.data.encode('shift-jis')
		rawdata.block1 = song.alias + bytes(blksize - len(song.alias))
		song.genre = form.genre.data.encode('shift-jis')
		rawdata.block2 = song.genre + bytes(blksize - len(song.genre))
		song.artist = form.artist.data.encode('shift-jis')
		rawdata.block3 = song.artist + bytes(blksize - len(song.artist) - 4)
		song.fontcolor = form.red.data * 1000000 + form.green.data * 1000 + form.blue.data
		if song.fontcolor != 0:
			rawdata.block3 += form.red.data.to_bytes(1, 'little') \
			+ form.green.data.to_bytes(1, 'little') \
			+ form.blue.data.to_bytes(1, 'little') + b'\x01'
		else:
			rawdata.block3 += bytes(4)
		song.version = int(form.version.data)
		newblock4[24] = song.version
		song.spn = form.spn.data
		newblock4[32] = form.spn.data
		song.sph = form.sph.data
		newblock4[33] = form.sph.data
		song.spa = form.spa.data
		newblock4[34] = form.spa.data
		song.dpn = form.dpn.data
		newblock4[35] = form.dpn.data
		song.dph = form.dph.data
		newblock4[36] = form.dph.data
		song.dpa = form.dpa.data
		newblock4[37] = form.dpa.data
		song.spb = form.spb.data
		newblock4[38] = form.spb.data
		song.volume = form.volume.data
		newblock7[12] = form.volume.data
		song.bgadelay = form.bgadelay.data
		newdelay = form.bgadelay.data.to_bytes(2, 'little', signed=True)
		newblock7[24] = newdelay[0]
		newblock7[25] = newdelay[1]
		song.bganame = form.bganame.data.encode('shift-jis')
		newblock7[28:48] = song.bganame + bytes(20 - len(song.bganame))
		song.font = form.font.data
		newblock4[20] = form.font.data
		song.otherfolder = form.otherfolder.data
		if form.otherfolder.data:
			newblock4[26] = 1
		else:
			newblock4[26] = 0
		flash('修改成功')
		rawdata.block4 = bytes(newblock4)
		rawdata.block7 = bytes(newblock7)
		db.session.add(song)
		db.session.add(rawdata)
		return redirect(url_for('.music', id=song.id))
	
	form.songid.data = song.songid
	form.title.data = converted_title
	form.alias.data = converted_alias
	form.genre.data = converted_genre
	form.artist.data = converted_artist
	form.version.data = song.version
	form.spn.data = song.spn
	form.sph.data = song.sph
	form.spa.data = song.spa
	form.dpn.data = song.dpn
	form.dph.data = song.dph
	form.dpa.data = song.dpa
	form.spb.data = song.spb
	form.volume.data = song.volume
	form.bgadelay.data = song.bgadelay
	form.bganame.data = converted_bganame
	form.font.data = song.font
	form.otherfolder.data = song.otherfolder
	form.red.data = math.floor(song.fontcolor / 1000000)
	form.green.data = math.floor(song.fontcolor / 1000) % 1000
	form.blue.data = song.fontcolor % 1000

	return render_template('music.html', song=song, form=form, converted_title=converted_title, 
		version=vername[song.version], converted_artist=converted_artist, converted_genre=converted_genre, 
		converted_alias=converted_alias, converted_bganame=converted_bganame, converted_fontcolor=converted_fontcolor)

@main.route('/delete:<int:id>')
def delete(id):
	song = Song.query.get_or_404(id)
	rawdata = Rawdata.query.get_or_404(id)
	version = Version.query.get_or_404(1)
	version.totalsongs = version.totalsongs - 1
	db.session.delete(song)
	db.session.delete(rawdata)
	db.session.add(version)
	flash('已删除歌曲')
	return redirect(url_for('.management'))

@main.route('/add', methods=['GET', 'POST'])
def add():
	version = Version.query.get_or_404(1)
	form = EditMusicForm(vername)
	if form.validate_on_submit():
		song = Song()
		rawdata = Rawdata()
		newblock4 = bytearray(blksize)
		newblock7 = bytearray(blksize)
		check_song = Song.query.filter_by(songid=form.songid.data).first()
		if check_song is not None:
			flash('该歌曲ID已存在！')
			return redirect(url_for('.add'))
		song.songid = form.songid.data
		rawdata.songid = form.songid.data
		newsongid = rawdata.songid.to_bytes(2, 'little')
		newblock7[8] = newsongid[0]
		newblock7[9] = newsongid[1]
		try:
			song.title = form.title.data.encode('shift-jis')
			song.alias = form.alias.data.encode('shift-jis')
			song.genre = form.genre.data.encode('shift-jis')
			song.artist = form.artist.data.encode('shift-jis')
			song.bganame = form.bganame.data.encode('shift-jis')
		except UnicodeEncodeError as e:
			flash('部分信息无法编码为Shift-JIS：' + str(e))
			return redirect(url_for('.add'))
		rawdata.block0 = song.title + bytes(blksize - len(song.title))
		rawdata.block1 = song.alias + bytes(blksize - len(song.alias))
		rawdata.block2 = song.genre + bytes(blksize - len(song.genre))
		rawdata.block3 = song.artist + bytes(blksize - len(song.artist) - 4)
		song.fontcolor = form.red.data * 1000000 + form.green.data * 1000 + form.blue.data
		if song.fontcolor != 0:
			rawdata.block3 += form.red.data.to_bytes(1, 'little') \
			+ form.green.data.to_bytes(1, 'little') \
			+ form.blue.data.to_bytes(1, 'little') + b'\x01'
		else:
			rawdata.block3 += bytes(4)
		song.version = int(form.version.data)
		newblock4[24] = song.version
		song.spn = form.spn.data
		newblock4[32] = form.spn.data
		song.sph = form.sph.data
		newblock4[33] = form.sph.data
		song.spa = form.spa.data
		newblock4[34] = form.spa.data
		song.dpn = form.dpn.data
		newblock4[35] = form.dpn.data
		song.dph = form.dph.data
		newblock4[36] = form.dph.data
		song.dpa = form.dpa.data
		newblock4[37] = form.dpa.data
		song.spb = form.spb.data
		newblock4[38] = form.spb.data
		song.volume = form.volume.data
		newblock7[12] = form.volume.data
		song.bgadelay = form.bgadelay.data
		newdelay = form.bgadelay.data.to_bytes(2, 'little', signed=True)
		newblock7[16:24] = bytes([48] * 8)
		newblock7[24] = newdelay[0]
		newblock7[25] = newdelay[1]
		song.bganame = form.bganame.data.encode('shift-jis')
		newblock7[28:48] = song.bganame + bytes(20 - len(song.bganame))
		song.font = form.font.data
		newblock4[20] = form.font.data
		song.otherfolder = form.otherfolder.data
		if form.otherfolder.data:
			newblock4[26] = 1
		else:
			newblock4[26] = 0
		newblock4[30] = 1
		rawdata.block4 = bytes(newblock4)
		rawdata.block7 = bytes(newblock7)
		rawdata.block5 = bytes(blksize)
		rawdata.block6 = bytes(blksize)
		rawdata.block8 = bytes(blksize)
		rawdata.block9 = bytes(blksize)
		rawdata.block10 = bytes(blksize)
		rawdata.block11 = bytes(blksize)
		rawdata.block12 = bytes(blksize)
		db.session.add(song)
		db.session.add(rawdata)
		version.totalsongs = version.totalsongs + 1
		db.session.add(version)
		flash('添加成功')
		anosong = Song.query.filter_by(songid=song.songid).first()
		return redirect(url_for('.music', id=anosong.id))
	
	form.spn.data = 0
	form.sph.data = 0
	form.spa.data = 0
	form.dpn.data = 0
	form.dph.data = 0
	form.dpa.data = 0
	form.spb.data = 0
	form.volume.data = 70
	form.bgadelay.data = 5
	form.font.data = 0
	form.red.data = 0
	form.green.data = 0
	form.blue.data = 0

	return render_template('add.html', form=form)

@main.route('/header', methods=['GET', 'POST'])
def header():
	form = EditHeaderForm(vername)
	version = Version.query.get_or_404(1)

	if form.validate_on_submit():
		version.gamever = form.gamever.data
		version.totalslots = form.slots.data
		db.session.add(version)
		return redirect(url_for('.header'))
	
	form.gamever.data = version.gamever
	form.slots.data = version.totalslots

	return render_template('header.html', form=form)

@main.route('/exporter')
def exporter():
	allsongs = Song.query.order_by(Song.songid).all()
	songs = []
	converted_titles = []
	converted_artists = []
	converted_genres = []
	converted_aliases = []
	converted_bganames = []
	converted_fontcolors = []

	if allsongs != []:
		for song in allsongs:
			songs.append(song)
			try:
				converted_titles.append(song.title.decode('shift-jis'))
			except UnicodeDecodeError as e:
				flash(str(song.songid) + '标题编码有问题')
				converted_titles.append(song.title)
			try:
				converted_artists.append(song.artist.decode('shift-jis'))
			except UnicodeDecodeError as e:
				flash(str(song.songid) + '艺术家编码有问题')
				converted_artists.append(song.artist)
			try:	
				converted_genres.append(song.genre.decode('shift-jis'))
			except UnicodeDecodeError as e:
				flash(str(song.songid) + '曲风编码有问题')
				converted_genres.append(song.genre)
			try:
				converted_aliases.append(song.alias.decode('shift-jis'))
			except UnicodeDecodeError as e:
				flash(str(song.songid) + '英文标题编码有问题')
				converted_aliases.append(song.alias)
			try:
				converted_bganames.append(song.bganame.decode('shift-jis'))
			except UnicodeDecodeError as e:
				flash(str(song.songid) + '英文标题编码有问题')
				converted_bganames.append(song.bganame)
			converted_fontcolor = [math.floor(song.fontcolor / 1000000), 
				math.floor(song.fontcolor / 1000) % 1000, song.fontcolor % 1000]
			converted_fontcolors.append(converted_fontcolor)
	
	return render_template('exporter.html', vername=vername, songs=songs,
		converted_titles=converted_titles, converted_artists=converted_artists,
		converted_genres=converted_genres, converted_aliases=converted_aliases,
		converted_bganames=converted_bganames, converted_fontcolors=converted_fontcolors)

@main.route('/downloader')
def downloader():
	filename = 'export_' + str(request.remote_addr).replace('.', '_') + '.bin'
	version = Version.query.get_or_404(1)
	songs = Song.query.order_by(Song.songid).all()
	rawdata = Rawdata.query.order_by(Rawdata.songid).all()
	header = b'\x49\x49\x44\x58' + version.gamever.to_bytes(1, 'little') + bytes(3) \
		+ version.totalsongs.to_bytes(2, 'little') + version.totalslots.to_bytes(2, 'little') + bytes(4)
	p = 0
	slots = bytes()
	for i in range(0, version.totalslots):
		if p < version.totalsongs and i == songs[p].songid:
			slots += p.to_bytes(2, 'little')
			p = p + 1
		else:
			slots += b'\xff\xff'
	songdat = bytes()
	for i in range(0, version.totalsongs):
		songdat += rawdata[i].block0
		songdat += rawdata[i].block1
		songdat += rawdata[i].block2
		songdat += rawdata[i].block3
		songdat += rawdata[i].block4
		songdat += rawdata[i].block5
		songdat += rawdata[i].block6
		songdat += rawdata[i].block7
		songdat += rawdata[i].block8
		songdat += rawdata[i].block9
		songdat += rawdata[i].block10
		songdat += rawdata[i].block11
		songdat += rawdata[i].block12
	with open('app/static/workfiles/' + filename, 'wb') as f:
		f.write(header)
		f.write(slots)
		f.write(songdat)
	filename = 'workfiles/' + filename
	return render_template('downloader.html', filename=filename)

@main.after_app_request
def after_request(response):
	for query in get_debug_queries():
		if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIMEOUT']:
			current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
				(query.statement, query.parameters, query.duration, query.context))
	return response
