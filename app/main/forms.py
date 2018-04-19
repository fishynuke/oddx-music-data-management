from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed

class WorkUploadForm(FlaskForm):
	workfile = FileField('上传文件')
	submit = SubmitField('提交')
	
	def __init__(self, *args, **kwargs):
		super(WorkUploadForm, self).__init__(*args, **kwargs)
		self.workfile.validators = [FileRequired(), FileAllowed(['bin'], '文件格式不正确，应为bin')]
