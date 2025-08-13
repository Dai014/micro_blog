import os

from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)  # <-- Thêm Mail vào ứng dụng Flask

login = LoginManager(app)
login.login_view = 'login'

if not app.debug: # chỉ bật khi app không ở chế độ debug
    if app.config['MAIL_SERVER']: # <-- Chỉ bật khi có cấu hình mail server
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'],
            subject='Microblog Failure',
            credentials=auth,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR) # <-- Chỉ gửi email khi lỗi cấp độ ERROR trở lên
        app.logger.addHandler(mail_handler)

    if not os.path.exists('logs'):  # <-- Tạo thư mục logs nếu chưa có
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)  # <-- Cấu hình RotatingFileHandler
    file_handler.setFormatter(logging.Formatter(  # <-- Định dạng log message
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)  # <-- Đặt cấp độ log
    app.logger.addHandler(file_handler)  # <-- Thêm handler vào app.logger

    app.logger.setLevel(logging.INFO)  # <-- Đặt cấp độ log của ứng dụng
    app.logger.info('Microblog startup')  # <-- Ghi log khi ứng dụng khởi động


from app import routes, models, errors
