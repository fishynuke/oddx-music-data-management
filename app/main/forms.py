from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import Required, InputRequired, NumberRange, Length
from flask_wtf.file import FileField, FileRequired, FileAllowed

class WorkUploadForm(FlaskForm):
	workfile = FileField('上传文件')
	submit = SubmitField('提交')
	
	def __init__(self, *args, **kwargs):
		super(WorkUploadForm, self).__init__(*args, **kwargs)
		self.workfile.validators = [FileRequired(), FileAllowed(['bin'], '文件格式不正确，应为bin')]

class EditMusicForm(FlaskForm):
	songid = IntegerField('歌曲ID', validators=[Required(), NumberRange(1000, 100000)])
	title = StringField('标题', validators=[Required(), Length(1, 64)])
	alias = StringField('英文标题', validators=[Required(), Length(1, 64)])
	genre = StringField('曲风', validators=[Required(), Length(1, 64)])
	artist = StringField('艺术家', validators=[Required(), Length(1, 64)])
	version = SelectField('版本', coerce=int)
	spn = IntegerField('SPN', validators=[InputRequired(), NumberRange(0, 13)])
	sph = IntegerField('SPH', validators=[InputRequired(), NumberRange(0, 13)])
	spa = IntegerField('SPA', validators=[InputRequired(), NumberRange(0, 13)])
	dpn = IntegerField('DPN', validators=[InputRequired(), NumberRange(0, 13)])
	dph = IntegerField('DPH', validators=[InputRequired(), NumberRange(0, 13)])
	dpa = IntegerField('DPA', validators=[InputRequired(), NumberRange(0, 13)])
	spb = IntegerField('SPB', validators=[InputRequired(), NumberRange(0, 13)])
	volume = IntegerField('音量', validators=[Required(), NumberRange(1, 128)])
	bgadelay = IntegerField('BGA延迟', validators=[Required(), NumberRange(-32768, 32768)])
	bganame = StringField('BGA名称', validators=[Required(), Length(1, 64)])
	font = IntegerField('字体编号', validators=[InputRequired(), NumberRange(0, 5)])
	red = IntegerField('字体颜色红', validators=[NumberRange(0, 255)])
	green = IntegerField('字体颜色绿', validators=[NumberRange(0, 255)])
	blue = IntegerField('字体颜色蓝', validators=[NumberRange(0, 255)])
	otherfolder = BooleanField('放进OTHERS文件夹？')
	submit = SubmitField('提交')

	def __init__(self, vername, *args, **kwargs):
		super(EditMusicForm, self).__init__(*args, **kwargs)
		self.version.choices = [(vername.index(vers), vers) for vers in vername]

class SearchForm(FlaskForm):
	songid = IntegerField('跳转歌曲ID', validators=[Required(), NumberRange(1000, 100000)])
	submit = SubmitField('跳转')

class EditHeaderForm(FlaskForm):
	gamever = SelectField('游戏版本', coerce=int)
	slots = IntegerField('歌曲Slot总数', validators=[Required(), NumberRange(25000, 100000)])
	submit = SubmitField('提交')

	def __init__(self, vername, *args, **kwargs):
		super(EditHeaderForm, self).__init__(*args, **kwargs)
		self.gamever.choices = [(vername.index(vers), vers) for vers in vername]