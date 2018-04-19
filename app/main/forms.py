from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import Required, Length, Regexp
from flask_pagedown.fields import PageDownField
from ..models import Role, User

class EditProfileAdminForm(FlaskForm):
	username = StringField('Username', validators=[Required(), Length(1, 64)])
	confirmed = BooleanField('Confirmed')
	role = SelectField('Role', coerce=int)
	name = StringField('Real name', validators=[Length(0, 64)])
	location = StringField('Location', validators=[Length(0, 64)])
	about_me = TextAreaField('About me')
	submit = SubmitField('Submit')
	
	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name)
			for role in Role.query.order_by(Role.name).all()]
		self.user = user
		
	def validate_username(self, field):
		if field.data != self.user.username and User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use.')
