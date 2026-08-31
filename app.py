from flask import Flask, session
from config import mysql, configurar
import os
import secrets
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

configurar(app)


app.config["UPLOAD_FOLDER"] = "static/img/productos"

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


mysql.init_app(app)


@app.context_processor
def datos_usuario():

    usuario = None
    cursor = None

    if "idUsu" in session:

        try:

            cursor = mysql.connection.cursor()

            cursor.execute("""
                SELECT
                    u.idUsu,
                    u.nombreUsu,
                    u.apellidoUsu,
                    u.usuarioUsu,
                    u.emailUsu,
                    u.telefonoUsu,
                    u.direccionUsu,
                    u.fotoUsu,
                    u.fechaNacimientoUsu,
                    u.activoUsu,
                    u.idRol,
                    r.nombreRol
                FROM usuarios u
                INNER JOIN roles r
                    ON u.idRol = r.idRol
                WHERE u.idUsu = %s
                LIMIT 1
            """, (session["idUsu"],))

            usuario = cursor.fetchone()
            if not usuario:

                session.clear()

                usuario = None

            elif usuario["activoUsu"] != 1:

                session.clear()

                usuario = None

            else:

                session["rol"] = usuario["nombreRol"]
                session["idRol"] = usuario["idRol"]


        except Exception as e:

            print("ERROR DATOS USUARIO:", e)

            usuario = None


        finally:

            if cursor:

                cursor.close()


    return {
        "usuario": usuario
    }

from routes.auth import *
from routes.admin import *
from routes.cliente import *
from routes.productos import *
from routes.citas import *
from routes.carrito import *
from routes.pedidos import *
from routes.pagos import *
from routes.profesional import*
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )