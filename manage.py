#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Version, Song
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

for line in open('env.txt'):
	var = line.strip().split('=')
	os.environ[var[0]] = var[1]

FLASK_CONFIG = os.environ.get('FLASK_CONFIG') or 'development'
SERVED_HOST = os.environ.get('SERVED_HOST') or '0.0.0.0'
OPEN_PORT = os.environ.get('OPEN_PORT') or 5000
print('Running in ' + FLASK_CONFIG + ' mode.')
app = create_app(FLASK_CONFIG)
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
	return dict(app=app, db=db, Version=Version, Song=Song)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(use_reloader=True, 
	host=SERVED_HOST, port=OPEN_PORT, threaded=True))

if __name__ == '__main__':
	manager.run()
