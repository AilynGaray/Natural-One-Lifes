from flask_mysqldb import MySQL

mysql = MySQL()

def configurar(app):
    app.config["MYSQL_HOST"] = "localhost"
    app.config["MYSQL_USER"] = "root"
    app.config["MYSQL_PASSWORD"] = "ailyn16"
    app.config["MYSQL_DB"] = "sistema"
    app.config["MYSQL_CURSORCLASS"] = "DictCursor"