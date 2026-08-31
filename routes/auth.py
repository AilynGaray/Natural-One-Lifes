from app import app

from flask import (
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from config import mysql

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from email_service import enviar_correo_recuperacion

from datetime import datetime, timedelta

import secrets


@app.route("/")
def login():

    if "idUsu" not in session:
        return render_template("login.html")

    rol = session.get("rol")

    if rol == "Administrador":
        return redirect("/dashboard")

    if rol == "Profesional":
        return redirect("/profesional")

    if rol == "Cliente":
        return redirect("/inicio")

    session.clear()

    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "GET":
        return render_template("registro.html")

    cursor = None

    try:

        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                "estado": "error",
                "mensaje": "No se recibieron los datos."
            }), 400

        nombre = datos.get("nombre", "").strip()
        apellido = datos.get("apellido", "").strip()
        usuario = datos.get("usuario", "").strip()
        email = datos.get("email", "").strip().lower()

        password = datos.get("password", "")
        confirmar = datos.get("confirmar", "")

        # --------------------------------------------------
        # VALIDACIONES
        # --------------------------------------------------

        if not nombre:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa tu nombre."
            }), 400

        if not apellido:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa tus apellidos."
            }), 400

        if not usuario:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa un nombre de usuario."
            }), 400

        if len(usuario) < 4:
            return jsonify({
                "estado": "error",
                "mensaje": "El usuario debe tener mínimo 4 caracteres."
            }), 400

        if not email:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa tu correo electrónico."
            }), 400

        if not password:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa una contraseña."
            }), 400

        if len(password) < 8:
            return jsonify({
                "estado": "error",
                "mensaje": "La contraseña debe tener mínimo 8 caracteres."
            }), 400

        if password != confirmar:
            return jsonify({
                "estado": "error",
                "mensaje": "Las contraseñas no coinciden."
            }), 400

        # --------------------------------------------------
        # SOLO CLIENTES
        # --------------------------------------------------

        rol = datos.get("rol", "cliente").strip().lower()

        if rol != "cliente":
            return jsonify({
                "estado": "error",
                "mensaje": "El registro de este tipo de usuario no está permitido."
            }), 403

        cursor = mysql.connection.cursor()

        # --------------------------------------------------
        # BUSCAR ROL CLIENTE
        # --------------------------------------------------

        cursor.execute("""
            SELECT idRol
            FROM roles
            WHERE nombreRol = 'Cliente'
            LIMIT 1
        """)

        rol_cliente = cursor.fetchone()

        if not rol_cliente:
            return jsonify({
                "estado": "error",
                "mensaje": "El rol Cliente no está configurado en el sistema."
            }), 500

        id_rol_cliente = rol_cliente["idRol"]

        # --------------------------------------------------
        # COMPROBAR CORREO
        # --------------------------------------------------

        cursor.execute("""
            SELECT idUsu
            FROM usuarios
            WHERE LOWER(emailUsu) = LOWER(%s)
            LIMIT 1
        """, (email,))

        if cursor.fetchone():
            return jsonify({
                "estado": "error",
                "campo": "email",
                "mensaje": "Este correo electrónico ya está registrado."
            }), 409

        # --------------------------------------------------
        # COMPROBAR USUARIO
        # --------------------------------------------------

        cursor.execute("""
            SELECT idUsu
            FROM usuarios
            WHERE usuarioUsu = %s
            LIMIT 1
        """, (usuario,))

        if cursor.fetchone():
            return jsonify({
                "estado": "error",
                "campo": "usuario",
                "mensaje": "Este nombre de usuario ya está en uso."
            }), 409

        # --------------------------------------------------
        # CIFRAR CONTRASEÑA
        # --------------------------------------------------

        password_hash = generate_password_hash(password)

        # --------------------------------------------------
        # INSERTAR
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO usuarios (
                nombreUsu,
                apellidoUsu,
                usuarioUsu,
                emailUsu,
                passwordUsu,
                activoUsu,
                idRol
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                1,
                %s
            )
        """, (
            nombre,
            apellido,
            usuario,
            email,
            password_hash,
            id_rol_cliente
        ))

        mysql.connection.commit()

        return jsonify({
            "estado": "ok",
            "mensaje": "Cuenta creada correctamente."
        }), 201

    except Exception as e:

        try:
            mysql.connection.rollback()
        except Exception:
            pass

        print("ERROR REGISTRO:", e)

        return jsonify({
            "estado": "error",
            "mensaje": "No fue posible crear la cuenta. Inténtalo nuevamente."
        }), 500

    finally:

        if cursor:
            cursor.close()


@app.route("/validar_login", methods=["POST"])
def validar_login():

    cursor = None

    try:

        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                "estado": "error",
                "mensaje": "No se recibieron los datos."
            }), 400

        usuario = datos.get("usuario", "").strip()
        password = datos.get("password", "")

        if not usuario or not password:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa tu usuario y contraseña."
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                u.idUsu,
                u.nombreUsu,
                u.apellidoUsu,
                u.usuarioUsu,
                u.emailUsu,
                u.passwordUsu,
                u.activoUsu,
                u.idRol,
                r.nombreRol
            FROM usuarios u
            INNER JOIN roles r
                ON u.idRol = r.idRol
            WHERE LOWER(u.emailUsu) = LOWER(%s)
               OR LOWER(u.usuarioUsu) = LOWER(%s)
            LIMIT 1
        """, (
            usuario,
            usuario
        ))

        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({
                "estado": "error",
                "mensaje": "El usuario o correo no está registrado."
            }), 401

        if resultado["activoUsu"] != 1:
            return jsonify({
                "estado": "error",
                "mensaje": "Esta cuenta se encuentra inactiva."
            }), 403

        if not check_password_hash(
            resultado["passwordUsu"],
            password
        ):
            return jsonify({
                "estado": "error",
                "mensaje": "El usuario o la contraseña son incorrectos."
            }), 401

        # --------------------------------------------------
        # CREAR SESIÓN
        # --------------------------------------------------

        session.clear()

        session["idUsu"] = resultado["idUsu"]
        session["nombreUsu"] = resultado["nombreUsu"]
        session["apellidoUsu"] = resultado["apellidoUsu"]
        session["usuarioUsu"] = resultado["usuarioUsu"]
        session["emailUsu"] = resultado["emailUsu"]
        session["idRol"] = resultado["idRol"]
        session["rol"] = resultado["nombreRol"]

        # --------------------------------------------------
        # REDIRECCIÓN
        # --------------------------------------------------

        if resultado["nombreRol"] == "Administrador":
            return jsonify({
                "estado": "ok",
                "rol": "Administrador",
                "redirect": "/dashboard"
            })

        if resultado["nombreRol"] == "Profesional":
            return jsonify({
                "estado": "ok",
                "rol": "Profesional",
                "redirect": "/profesional"
            })

        if resultado["nombreRol"] == "Cliente":
            return jsonify({
                "estado": "ok",
                "rol": "Cliente",
                "redirect": "/inicio"
            })

        session.clear()

        return jsonify({
            "estado": "error",
            "mensaje": "El rol de esta cuenta no es válido."
        }), 403

    except Exception as e:

        print("ERROR LOGIN:", e)

        return jsonify({
            "estado": "error",
            "mensaje": "Ocurrió un error al iniciar sesión."
        }), 500

    finally:

        if cursor:
            cursor.close()

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():

    if request.method == "GET":

        return render_template(
            "recuperar-contraseña.html"
        )

    cursor = None

    try:

        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                "estado": "error",
                "mensaje": "No se recibieron los datos."
            }), 400

        email = datos.get(
            "email",
            ""
        ).strip().lower()

        if not email:
            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa tu correo electrónico."
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                emailUsu,
                activoUsu
            FROM usuarios
            WHERE LOWER(emailUsu) = LOWER(%s)
            LIMIT 1
        """, (email,))

        usuario = cursor.fetchone()

        mensaje_generico = (
            "Si el correo está registrado, "
            "recibirás un enlace para recuperar "
            "tu contraseña."
        )

        # No revelar si el correo existe

        if not usuario:

            return jsonify({
                "estado": "ok",
                "mensaje": mensaje_generico
            }), 200

        # --------------------------------------------------
        # CUENTA INACTIVA
        # --------------------------------------------------

        if usuario["activoUsu"] != 1:

            return jsonify({
                "estado": "ok",
                "mensaje": mensaje_generico
            }), 200

        # --------------------------------------------------
        # INVALIDAR TOKENS ANTERIORES
        # --------------------------------------------------

        cursor.execute("""
            UPDATE tokens_recuperacion
            SET usadoToken = 1
            WHERE idUsuToken = %s
              AND usadoToken = 0
        """, (
            usuario["idUsu"],
        ))

        # --------------------------------------------------
        # GENERAR TOKEN
        # --------------------------------------------------

        token = secrets.token_urlsafe(64)

        expiracion = (
            datetime.now()
            + timedelta(minutes=30)
        )

        # --------------------------------------------------
        # GUARDAR TOKEN
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO tokens_recuperacion (
                idUsuToken,
                tokenToken,
                expiracionToken,
                usadoToken
            )
            VALUES (
                %s,
                %s,
                %s,
                0
            )
        """, (
            usuario["idUsu"],
            token,
            expiracion
        ))

        # --------------------------------------------------
        # CREAR ENLACE
        # --------------------------------------------------

        enlace = url_for(
            "nueva_contrasena",
            token=token,
            _external=True
        )

        print("=" * 70)
        print("RECUPERACIÓN DE CONTRASEÑA")
        print("Correo:", usuario["emailUsu"])
        print("Enlace:", enlace)
        print("Expira:", expiracion)
        print("=" * 70)

        # --------------------------------------------------
        # GUARDAR TOKEN ANTES DE ENVIAR
        # --------------------------------------------------

        mysql.connection.commit()

        # --------------------------------------------------
        # ENVIAR CORREO
        # --------------------------------------------------

        enviar_correo_recuperacion(
            usuario["emailUsu"],
            usuario["nombreUsu"],
            enlace
        )

        return jsonify({
            "estado": "ok",
            "mensaje": mensaje_generico
        }), 200

    except Exception as e:

        print("ERROR RECUPERACIÓN:", e)

        try:
            mysql.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "estado": "error",
            "mensaje": (
                "No fue posible enviar el correo "
                "de recuperación. Verifica la configuración "
                "del correo e inténtalo nuevamente."
            )
        }), 500

    finally:

        if cursor:
            cursor.close()


@app.route(
    "/nueva-contrasena/<token>",
    methods=["GET", "POST"]
)
def nueva_contrasena(token):

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                idToken,
                idUsuToken,
                tokenToken,
                expiracionToken,
                usadoToken
            FROM tokens_recuperacion
            WHERE tokenToken = %s
            LIMIT 1
        """, (
            token,
        ))

        token_data = cursor.fetchone()

        if not token_data:

            return render_template(
                "nueva-contraseña.html",
                valido=False,
                mensaje="El enlace de recuperación no es válido."
            )

        # --------------------------------------------------
        # TOKEN USADO
        # --------------------------------------------------

        if token_data["usadoToken"] == 1:

            return render_template(
                "nueva-contraseña.html",
                valido=False,
                mensaje="Este enlace ya fue utilizado."
            )

        # --------------------------------------------------
        # TOKEN EXPIRADO
        # --------------------------------------------------

        if datetime.now() > token_data["expiracionToken"]:

            cursor.execute("""
                UPDATE tokens_recuperacion
                SET usadoToken = 1
                WHERE idToken = %s
            """, (
                token_data["idToken"],
            ))

            mysql.connection.commit()

            return render_template(
                "nueva-contraseña.html",
                valido=False,
                mensaje=(
                    "El enlace de recuperación ha expirado. "
                    "Solicita uno nuevo."
                )
            )

        # --------------------------------------------------
        # GET
        # --------------------------------------------------

        if request.method == "GET":

            return render_template(
                "nueva-contraseña.html",
                valido=True,
                token=token
            )

        # --------------------------------------------------
        # POST
        # --------------------------------------------------

        datos = request.get_json(silent=True)

        if not datos:

            return jsonify({
                "estado": "error",
                "mensaje": "No se recibieron los datos."
            }), 400

        password = datos.get(
            "password",
            ""
        )

        confirmar = datos.get(
            "confirmar",
            ""
        )

        # --------------------------------------------------
        # VALIDACIONES
        # --------------------------------------------------

        if not password:

            return jsonify({
                "estado": "error",
                "mensaje": "Ingresa una nueva contraseña."
            }), 400

        if len(password) < 8:

            return jsonify({
                "estado": "error",
                "mensaje": (
                    "La contraseña debe tener "
                    "mínimo 8 caracteres."
                )
            }), 400

        if password != confirmar:

            return jsonify({
                "estado": "error",
                "mensaje": "Las contraseñas no coinciden."
            }), 400

        # --------------------------------------------------
        # VOLVER A VALIDAR TOKEN
        # --------------------------------------------------

        if token_data["usadoToken"] == 1:

            return jsonify({
                "estado": "error",
                "mensaje": "Este enlace ya fue utilizado."
            }), 400

        if datetime.now() > token_data["expiracionToken"]:

            cursor.execute("""
                UPDATE tokens_recuperacion
                SET usadoToken = 1
                WHERE idToken = %s
            """, (
                token_data["idToken"],
            ))

            mysql.connection.commit()

            return jsonify({
                "estado": "error",
                "mensaje": (
                    "El enlace ha expirado. "
                    "Solicita uno nuevo."
                )
            }), 400

        # --------------------------------------------------
        # CIFRAR CONTRASEÑA
        # --------------------------------------------------

        password_hash = generate_password_hash(
            password
        )

        # --------------------------------------------------
        # ACTUALIZAR USUARIO
        # --------------------------------------------------

        cursor.execute("""
            UPDATE usuarios
            SET
                passwordUsu = %s,
                intentosFallidosUsu = 0,
                bloqueoHastaUsu = NULL
            WHERE idUsu = %s
        """, (
            password_hash,
            token_data["idUsuToken"]
        ))

        # --------------------------------------------------
        # MARCAR TOKEN COMO USADO
        # --------------------------------------------------

        cursor.execute("""
            UPDATE tokens_recuperacion
            SET usadoToken = 1
            WHERE idToken = %s
        """, (
            token_data["idToken"],
        ))

        # --------------------------------------------------
        # GUARDAR
        # --------------------------------------------------

        mysql.connection.commit()

        return jsonify({
            "estado": "ok",
            "mensaje": (
                "Tu contraseña fue actualizada "
                "correctamente."
            )
        }), 200

    except Exception as e:

        print(
            "ERROR NUEVA CONTRASEÑA:",
            e
        )

        try:
            mysql.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "estado": "error",
            "mensaje": (
                "No fue posible actualizar "
                "la contraseña."
            )
        }), 500

    finally:

        if cursor:
            cursor.close()
