import os
basedir = os.path.abspath(os.path.dirname(__file__))
for line in open('env.txt'):
	var = line.strip().split('=')
	os.environ[var[0]] = var[1]

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY')
	FLASKY_ADMIN = 'webadmin'
	SQLALCHEMY_RECORD_QUERIES = True
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	FLASKY_SLOW_DB_QUERY_TIMEOUT = 0.5
	SSL_REDIRECT = False
	BOOTSTRAP_SERVE_LOCAL = True
	@staticmethod
	def init_app(app):
		pass

class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
	
class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
	'development': DevelopmentConfig,
	'production': ProductionConfig,
	}
