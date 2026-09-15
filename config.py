from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv

load_dotenv()

mysql = MySQL()


def configurar(app):
    app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
    app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
    app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
    app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "sistema")
    app.config["MYSQL_CURSORCLASS"] = "DictCursor"