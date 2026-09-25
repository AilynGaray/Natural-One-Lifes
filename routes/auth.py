from app import app

from flask import (
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from email_service import enviar_correo_recuperacion

from datetime import datetime, timedelta

import secrets

from models.usuario import (
    buscar_por_email,
    buscar_por_usuario_o_email,
    buscar_rol_cliente,
    existe_email,
    existe_usuario,
    crear_usuario,
    actualizar_password
)

from models.tokens import (
    crear_token_recuperacion,
    buscar_token,
    marcar_token_usado
)


# ============================================================
# VALIDACIÓN DE DATOS DEL REGISTRO
# ============================================================

def validar_datos_registro(datos):
    nombre = datos.get("nombre", "").strip()
    apellido = datos.get("apellido", "").strip()
    usuario = datos.get("usuario", "").strip()
    email = datos.get("email", "").strip().lower()

    password = datos.get("password", "")
    confirmar = datos.get("confirmar", "")

    if not nombre:
        return None, "Ingresa tu nombre."

    if not apellido:
        return None, "Ingresa tus apellidos."

    if not usuario:
        return None, "Ingresa un nombre de usuario."

    if len(usuario) < 4:
        return None, "El usuario debe tener mínimo 4 caracteres."

    if not email:
        return None, "Ingresa tu correo electrónico."

    if not password:
        return None, "Ingresa una contraseña."

    if len(password) < 8:
        return None, "La contraseña debe tener mínimo 8 caracteres."

    if password != confirmar:
        return None, "Las contraseñas no coinciden."

    # El rol no se confía al cliente.
    # Si viene informado, únicamente se permite "cliente".
    rol = (datos.get("rol") or "cliente").strip().lower()

    if rol != "cliente":
        return None, (
            "El registro de este tipo de usuario "
            "no está permitido."
        )

    return {
        "nombre": nombre,
        "apellido": apellido,
        "usuario": usuario,
        "email": email,
        "password": password
    }, None


# ============================================================
# LOGIN
# ============================================================

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


# ============================================================
# REGISTRO
# ============================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "GET":
        return render_template("registro.html")

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                "estado": "error",
                "mensaje": "No se recibieron los datos."
            }), 400

        datos_validos, error = validar_datos_registro(datos)

        if error:
            return jsonify({
                "estado": "error",
                "mensaje": error
            }), 400

        nombre = datos_validos["nombre"]
        apellido = datos_validos["apellido"]
        usuario = datos_validos["usuario"]
        email = datos_validos["email"]
        password = datos_validos["password"]

        # --------------------------------------------------
        # VALIDAR CORREO EXISTENTE
        # --------------------------------------------------

        if existe_email(email):
            return jsonify({
                "estado": "error",
                "campo": "email",
                "mensaje": (
                    "Este correo electrónico "
                    "ya está registrado."
                )
            }), 409

        # --------------------------------------------------
        # VALIDAR USUARIO EXISTENTE
        # --------------------------------------------------

        if existe_usuario(usuario):
            return jsonify({
                "estado": "error",
                "campo": "usuario",
                "mensaje": (
                    "Este nombre de usuario "
                    "ya está en uso."
                )
            }), 409

        # --------------------------------------------------
        # OBTENER ROL CLIENTE
        # --------------------------------------------------

        rol_cliente = buscar_rol_cliente()

        if not rol_cliente:
            return jsonify({
                "estado": "error",
                "mensaje": (
                    "El rol Cliente no está "
                    "configurado en el sistema."
                )
            }), 500

        # --------------------------------------------------
        # GENERAR HASH DE CONTRASEÑA
        # --------------------------------------------------

        password_hash = generate_password_hash(password)

        # --------------------------------------------------
        # CREAR USUARIO
        # --------------------------------------------------

        crear_usuario(
            nombre,
            apellido,
            usuario,
            email,
            password_hash,
            rol_cliente["idRol"]
        )

        return jsonify({
            "estado": "ok",
            "mensaje": "Cuenta creada correctamente."
        }), 201

    except Exception as e:

        print("ERROR REGISTRO:", e)

        return jsonify({
            "estado": "error",
            "mensaje": (
                "No fue posible crear la cuenta. "
                "Inténtalo nuevamente."
            )
        }), 500


# ============================================================
# LOGIN DEL USUARIO
# ============================================================

@app.route("/validar_login", methods=["POST"])
def validar_login():

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
                "mensaje": (
                    "Ingresa tu usuario y contraseña."
                )
            }), 400

        # --------------------------------------------------
        # BUSCAR USUARIO
        # --------------------------------------------------

        resultado = buscar_por_usuario_o_email(usuario)

        if not resultado:
            return jsonify({
                "estado": "error",
                "mensaje": (
                    "El usuario o la contraseña "
                    "son incorrectos."
                )
            }), 401

        # --------------------------------------------------
        # VALIDAR ESTADO DE LA CUENTA
        # --------------------------------------------------

        if resultado["activoUsu"] != 1:
            return jsonify({
                "estado": "error",
                "mensaje": (
                    "Esta cuenta se encuentra inactiva."
                )
            }), 403

        # --------------------------------------------------
        # VALIDAR CONTRASEÑA
        # --------------------------------------------------

        if not check_password_hash(
            resultado["passwordUsu"],
            password
        ):
            return jsonify({
                "estado": "error",
                "mensaje": (
                    "El usuario o la contraseña "
                    "son incorrectos."
                )
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
        # REDIRECCIÓN SEGÚN ROL
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

        # --------------------------------------------------
        # ROL NO VÁLIDO
        # --------------------------------------------------

        session.clear()

        return jsonify({
            "estado": "error",
            "mensaje": "El rol de esta cuenta no es válido."
        }), 403

    except Exception as e:

        print("ERROR LOGIN:", e)

        return jsonify({
            "estado": "error",
            "mensaje": (
                "Ocurrió un error al iniciar sesión."
            )
        }), 500


# ============================================================
# CERRAR SESIÓN
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# RECUPERAR CONTRASEÑA
# ============================================================

@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():

    if request.method == "GET":
        return render_template(
            "recuperar-contraseña.html"
        )

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
                "mensaje": (
                    "Ingresa tu correo electrónico."
                )
            }), 400

        # --------------------------------------------------
        # BUSCAR USUARIO
        # --------------------------------------------------

        usuario = buscar_por_email(email)

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
        # VALIDAR CUENTA ACTIVA
        # --------------------------------------------------

        if usuario["activoUsu"] != 1:
            return jsonify({
                "estado": "ok",
                "mensaje": mensaje_generico
            }), 200

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

        crear_token_recuperacion(
            usuario["idUsu"],
            token,
            expiracion
        )

        # --------------------------------------------------
        # CREAR ENLACE
        # --------------------------------------------------

        enlace = url_for(
            "nueva_contrasena",
            token=token,
            _external=True
        )

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

        return jsonify({
            "estado": "error",
            "mensaje": (
                "No fue posible enviar el correo "
                "de recuperación. Verifica la configuración "
                "del correo e inténtalo nuevamente."
            )
        }), 500


# ============================================================
# NUEVA CONTRASEÑA
# ============================================================

@app.route(
    "/nueva-contrasena/<token>",
    methods=["GET", "POST"]
)
def nueva_contrasena(token):

    try:

        # --------------------------------------------------
        # BUSCAR TOKEN
        # --------------------------------------------------

        token_data = buscar_token(token)

        if not token_data:
            return render_template(
                "nueva-contraseña.html",
                valido=False,
                mensaje=(
                    "El enlace de recuperación "
                    "no es válido."
                )
            )

        # --------------------------------------------------
        # TOKEN USADO
        # --------------------------------------------------

        if token_data["usadoToken"] == 1:
            return render_template(
                "nueva-contraseña.html",
                valido=False,
                mensaje=(
                    "Este enlace ya fue utilizado."
                )
            )

        # --------------------------------------------------
        # TOKEN EXPIRADO
        # --------------------------------------------------

        if datetime.now() > token_data["expiracionToken"]:

            marcar_token_usado(
                token_data["idToken"]
            )

            return render_template(
                "nueva-contraseña.html",
                valido=False,
                mensaje=(
                    "El enlace de recuperación "
                    "ha expirado. Solicita uno nuevo."
                )
            )

        # --------------------------------------------------
        # MOSTRAR FORMULARIO
        # --------------------------------------------------

        if request.method == "GET":

            return render_template(
                "nueva-contraseña.html",
                valido=True,
                token=token
            )

        # --------------------------------------------------
        # RECIBIR NUEVA CONTRASEÑA
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
                "mensaje": (
                    "Ingresa una nueva contraseña."
                )
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
                "mensaje": (
                    "Las contraseñas no coinciden."
                )
            }), 400

        # Se consulta nuevamente el token para evitar trabajar con información antigua.
        token_actual = buscar_token(token)

        if not token_actual:
            return jsonify({
                "estado": "error",
                "mensaje": (
                    "El enlace de recuperación "
                    "no es válido."
                )
            }), 400

        if token_actual["usadoToken"] == 1:
            return jsonify({
                "estado": "error",
                "mensaje": (
                    "Este enlace ya fue utilizado."
                )
            }), 400

        if datetime.now() > token_actual["expiracionToken"]:

            marcar_token_usado(
                token_actual["idToken"]
            )

            return jsonify({
                "estado": "error",
                "mensaje": (
                    "El enlace ha expirado. "
                    "Solicita uno nuevo."
                )
            }), 400

        # Se genera un hash

        password_hash = generate_password_hash(
            password
        )

        # se actualiza la contraseña del usuario

        actualizar_password(
            token_actual["idUsuToken"],
            password_hash
        )

        # marcarse el token como usado

        marcar_token_usado(
            token_actual["idToken"]
        )

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

        return jsonify({
            "estado": "error",
            "mensaje": (
                "No fue posible actualizar "
                "la contraseña."
            )
        }), 500