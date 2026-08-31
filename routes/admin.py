from app import app

from flask import (
    render_template,
    redirect,
    session,
    request,
    jsonify,
    url_for,
    flash
)
from werkzeug.utils import secure_filename
import os
from routes.cliente import producto
from routes.permiso import administrador_requerido

from config import mysql

from werkzeug.security import generate_password_hash


@app.route("/dashboard")
@administrador_requerido
def dashboard():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/")

    cursor = mysql.connection.cursor()

    try:

    

        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                emailUsu,
                telefonoUsu,
                fotoUsu
            FROM usuarios
            WHERE idUsu = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario:
            return "Usuario no encontrado", 404


       

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM productos
        """)

        total_productos = cursor.fetchone()["total"]


        cursor.execute("""
            SELECT
                SUM(precioPro * stockPro) AS valor
            FROM productos
        """)

        resultado = cursor.fetchone()

        valor_inventario = (
            resultado["valor"]
            if resultado["valor"] is not None
            else 0
        )



        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM productos
            WHERE stockPro <= stockMinimoPro
        """)

        poco_stock = cursor.fetchone()["total"]



        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE estadoPed = 'Pendiente'
        """)

        pedidos_pendientes = cursor.fetchone()["total"]


        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM citas
            WHERE fechaCit >= CURDATE()
            AND estadoCit IN ('Pendiente', 'Confirmada')
        """)

        citas_proximas = cursor.fetchone()["total"]


       

        cursor.execute("""
            SELECT nombrePro
            FROM productos
            WHERE stockPro <= stockMinimoPro
        """)

        productos_bajos = cursor.fetchall()


        alertas = []

        for producto in productos_bajos:

            alertas.append(
                "Producto con poco stock: "
                + producto["nombrePro"]
            )


        # ----------------------------------------------------
        # TOTAL PROFESIONALES
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM profesionales
            WHERE activoProfe = 1
        """)

        total_profesionales = cursor.fetchone()["total"]


        return render_template(
            "admin/dashboard.html",

            usuario=usuario,

            total_productos=total_productos,

            valor_inventario=valor_inventario,

            poco_stock=poco_stock,

            pedidos_pendientes=pedidos_pendientes,

            citas_proximas=citas_proximas,

            total_profesionales=total_profesionales,

            alertas=alertas
        )

    finally:

        cursor.close()


@app.route("/perfil-admin")
@administrador_requerido
def perfil_admin():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/")

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                emailUsu,
                telefonoUsu,
                fotoUsu
            FROM usuarios
            WHERE idUsu = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

    finally:

        cursor.close()


    if not usuario:

        return "Usuario no encontrado", 404


    return render_template(
        "admin/perfil-admin.html",
        usuario=usuario
    )


@app.route("/editar-perfil-admin", methods=["GET", "POST"])
@administrador_requerido
def editar_perfil_admin():



    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/")


    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                usuarioUsu,
                emailUsu,
                telefonoUsu,
                fotoUsu
            FROM usuarios
            WHERE idUsu = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

    finally:

        cursor.close()



    if not usuario:

        return "Usuario no encontrado", 404


   

    if request.method == "POST":

        nombre = request.form.get(
            "nombreUsu",
            ""
        ).strip()

        apellido = request.form.get(
            "apellidoUsu",
            ""
        ).strip()

        email = request.form.get(
            "emailUsu",
            ""
        ).strip().lower()

        telefono = request.form.get(
            "telefonoUsu",
            ""
        ).strip()


       

        if not nombre:

            flash(
                "El nombre es obligatorio.",
                "error"
            )

            return redirect(
                url_for("editar_perfil_admin")
            )


        if not apellido:

            flash(
                "El apellido es obligatorio.",
                "error"
            )

            return redirect(
                url_for("editar_perfil_admin")
            )


        if not email:

            flash(
                "El correo electrónico es obligatorio.",
                "error"
            )

            return redirect(
                url_for("editar_perfil_admin")
            )


        # ----------------------------------------------------
        # VALIDAR CORREO REPETIDO
        # ----------------------------------------------------

        cursor = mysql.connection.cursor()

        try:

            cursor.execute("""
                SELECT idUsu
                FROM usuarios
                WHERE LOWER(emailUsu) = LOWER(%s)
                AND idUsu != %s
                LIMIT 1
            """, (
                email,
                id_usuario
            ))

            correo_existente = cursor.fetchone()

        finally:

            cursor.close()


        if correo_existente:

            flash(
                "El correo electrónico ya está registrado por otro usuario.",
                "error"
            )

            return redirect(
                url_for("editar_perfil_admin")
            )


       

        foto = request.files.get("fotoUsu")

        # Mantener la foto actual
        nombre_foto = usuario["fotoUsu"]


        if foto and foto.filename:

          

            extensiones_permitidas = {
                "jpg",
                "jpeg",
                "png",
                "webp"
            }

            extension = foto.filename.rsplit(
                ".",
                1
            )[-1].lower()


            if extension not in extensiones_permitidas:

                flash(
                    "Formato de imagen no permitido. Usa JPG, JPEG, PNG o WEBP.",
                    "error"
                )

                return redirect(
                    url_for("editar_perfil_admin")
                )


            # ------------------------------------------------
            # CARPETA
            # ------------------------------------------------

            carpeta = os.path.join(
                app.root_path,
                "static",
                "img",
                "perfiles"
            )

            os.makedirs(
                carpeta,
                exist_ok=True
            )


            if usuario["fotoUsu"]:

                foto_anterior = os.path.join(
                    carpeta,
                    usuario["fotoUsu"]
                )

                if os.path.exists(foto_anterior):

                    try:

                        os.remove(
                            foto_anterior
                        )

                    except Exception as e:

                        print(
                            "No se pudo eliminar la foto anterior:",
                            e
                        )


            nombre_foto = (
                str(id_usuario)
                + "_perfil."
                + extension
            )


            ruta_foto = os.path.join(
                carpeta,
                secure_filename(nombre_foto)
            )

            foto.save(
                ruta_foto
            )

        cursor = mysql.connection.cursor()

        try:

            cursor.execute("""
                UPDATE usuarios
                SET
                    nombreUsu = %s,
                    apellidoUsu = %s,
                    emailUsu = %s,
                    telefonoUsu = %s,
                    fotoUsu = %s
                WHERE idUsu = %s
            """, (
                nombre,
                apellido,
                email,
                telefono if telefono else None,
                nombre_foto,
                id_usuario
            ))


            mysql.connection.commit()


        except Exception as e:

            mysql.connection.rollback()

            print(
                "ERROR ACTUALIZANDO PERFIL:",
                e
            )

            flash(
                "No fue posible actualizar el perfil.",
                "error"
            )

            return redirect(
                url_for("editar_perfil_admin")
            )


        finally:

            cursor.close()


      

        session["nombreUsu"] = nombre
        session["apellidoUsu"] = apellido
        session["emailUsu"] = email


    

        flash(
            "Perfil actualizado correctamente.",
            "success"
        )



        return redirect(
            url_for("perfil_admin")
        )


    return render_template(
        "admin/editar_perfil.html",
        usuario=usuario
    )

@app.route("/panel-alertas")
@administrador_requerido
def panel_alertas():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                nombrePro,
                stockPro,
                stockMinimoPro
            FROM productos
            WHERE stockPro <= stockMinimoPro
            ORDER BY stockPro ASC
        """)

        productos_bajos = cursor.fetchall()


        alertas = []

        for producto in productos_bajos:

            alertas.append({

                "tipo": "stock",

                "mensaje":
                    "Producto con poco stock: "
                    + producto["nombrePro"],

                "stock":
                    producto["stockPro"],

                "minimo":
                    producto["stockMinimoPro"]

            })


        return render_template(
            "admin/alertas.html",
            alertas=alertas
        )

    finally:

        cursor.close()


@app.route("/admin/profesionales")
@administrador_requerido
def profesionales():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                p.idProfe,
                p.idUsuarioPro,
                p.nombreProfe,
                p.especialidadProfe,
                p.telefonoProfe,
                p.correoProfe,
                p.activoProfe,
                u.usuarioUsu,
                u.emailUsu
            FROM profesionales p

            LEFT JOIN usuarios u
                ON p.idUsuarioPro = u.idUsu

            ORDER BY
                p.nombreProfe ASC
        """)

        profesionales = cursor.fetchall()


        return render_template(
            "admin/profesionales.html",
            profesionales=profesionales
        )

    finally:

        cursor.close()


@app.route("/admin/profesionales/nuevo")
@administrador_requerido
def nuevo_profesional():

    return render_template(
        "admin/nuevo_profesional.html"
    )


@app.route(
    "/admin/profesionales/crear",
    methods=["POST"]
)
@administrador_requerido
def crear_profesional():

    cursor = None

    try:

        datos = request.get_json(silent=True)


        if not datos:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "No se recibieron los datos."

            }), 400

        nombre = datos.get(
            "nombre",
            ""
        ).strip()


        apellido = datos.get(
            "apellido",
            ""
        ).strip()


        usuario = datos.get(
            "usuario",
            ""
        ).strip()


        email = datos.get(
            "email",
            ""
        ).strip().lower()


        telefono = datos.get(
            "telefono",
            ""
        ).strip()


        especialidad = datos.get(
            "especialidad",
            ""
        ).strip()


        password = datos.get(
            "password",
            ""
        )


        confirmar = datos.get(
            "confirmar",
            ""
        )

        if not nombre:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "El nombre es obligatorio."

            }), 400


        if not apellido:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "Los apellidos son obligatorios."

            }), 400


        if len(usuario) < 4:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "El usuario debe tener mínimo 4 caracteres."

            }), 400


        if not email:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "El correo electrónico es obligatorio."

            }), 400


        if not especialidad:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "La especialidad es obligatoria."

            }), 400


        if len(password) < 8:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "La contraseña debe tener mínimo 8 caracteres."

            }), 400


        if password != confirmar:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "Las contraseñas no coinciden."

            }), 400


        # ----------------------------------------------------
        # CURSOR
        # ----------------------------------------------------

        cursor = mysql.connection.cursor()


        # ----------------------------------------------------
        # BUSCAR ROL PROFESIONAL
        # ----------------------------------------------------

        cursor.execute("""
            SELECT idRol
            FROM roles
            WHERE nombreRol = 'Profesional'
            LIMIT 1
        """)

        rol = cursor.fetchone()


        if not rol:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "El rol Profesional no existe en la base de datos."

            }), 500


        id_rol_profesional = rol["idRol"]


        # ----------------------------------------------------
        # COMPROBAR USUARIO
        # ----------------------------------------------------

        cursor.execute("""
            SELECT idUsu
            FROM usuarios
            WHERE LOWER(usuarioUsu) = LOWER(%s)
            LIMIT 1
        """, (usuario,))


        usuario_existente = cursor.fetchone()


        if usuario_existente:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "El nombre de usuario ya está registrado."

            }), 409


        # ----------------------------------------------------
        # COMPROBAR CORREO
        # ----------------------------------------------------

        cursor.execute("""
            SELECT idUsu
            FROM usuarios
            WHERE LOWER(emailUsu) = LOWER(%s)
            LIMIT 1
        """, (email,))


        correo_existente = cursor.fetchone()


        if correo_existente:

            return jsonify({

                "estado": "error",

                "mensaje":
                    "El correo electrónico ya está registrado."

            }), 409


        # ----------------------------------------------------
        # CIFRAR CONTRASEÑA
        # ----------------------------------------------------

        password_hash = generate_password_hash(
            password
        )


        # ----------------------------------------------------
        # CREAR USUARIO
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO usuarios (
                nombreUsu,
                apellidoUsu,
                usuarioUsu,
                emailUsu,
                telefonoUsu,
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
                %s,
                1,
                %s
            )
        """, (

            nombre,

            apellido,

            usuario,

            email,

            telefono,

            password_hash,

            id_rol_profesional

        ))


        id_usuario = cursor.lastrowid


        # ----------------------------------------------------
        # CREAR PROFESIONAL
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO profesionales (
                idUsuarioPro,
                nombreProfe,
                especialidadProfe,
                telefonoProfe,
                correoProfe,
                activoProfe
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                1
            )
        """, (

            id_usuario,

            nombre + " " + apellido,

            especialidad,

            telefono,

            email

        ))


        # ----------------------------------------------------
        # CONFIRMAR
        # ----------------------------------------------------

        mysql.connection.commit()


        return jsonify({

            "estado": "ok",

            "mensaje":
                "Profesional creado correctamente."

        }), 201


    except Exception as e:

        print(
            "ERROR CREANDO PROFESIONAL:",
            e
        )


        try:

            mysql.connection.rollback()

        except Exception:

            pass


        return jsonify({

            "estado": "error",

            "mensaje":
                "No fue posible crear el profesional."

        }), 500


    finally:

        if cursor:

            cursor.close()

@app.route("/disponibilidad")
@administrador_requerido
def disponibilidad():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                d.idDisp,
                d.idProfesionalDisp,
                d.diaDisp,
                d.horaInicioDisp,
                d.horaFinDisp,
                d.estadoDisp,
                d.fechaDisp,

                p.nombreProfe,
                p.especialidadProfe

            FROM disponibilidad d

            INNER JOIN profesionales p
                ON d.idProfesionalDisp = p.idProfe

            ORDER BY
                d.fechaDisp ASC,
                d.horaInicioDisp ASC
        """)

        disponibilidad = cursor.fetchall()


        return render_template(
            "admin/disponibilidad.html",
            disponibilidad=disponibilidad
        )

    finally:

        cursor.close()


@app.route("/supervision-citas")
@administrador_requerido
def supervision_citas():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT

                c.idCit,
                c.fechaCit,
                c.horaCit,
                c.estadoCit,
                c.motivoCit,
                c.notificadoCit,
                c.actualizadoPorCit,

                u.idUsu,
                u.nombreUsu,
                u.apellidoUsu,
                u.telefonoUsu,
                u.emailUsu,

                p.idProfe,
                p.nombreProfe,
                p.especialidadProfe

            FROM citas c

            INNER JOIN usuarios u
                ON c.idUsuarioCit = u.idUsu

            INNER JOIN profesionales p
                ON c.idProfesionalCit = p.idProfe

            ORDER BY
                c.fechaCit DESC,
                c.horaCit DESC
        """)

        citas = cursor.fetchall()


        return render_template(
            "admin/supervision_citas.html",
            citas=citas
        )

    finally:

        cursor.close()


@app.route("/inventario")
@administrador_requerido
def inventario():

    cursor = mysql.connection.cursor()

    try:

        # ====================================================
        # OBTENER PRODUCTOS
        # ====================================================

        cursor.execute("""
            SELECT
                idPro,
                nombrePro,
                precioPro,
                stockPro,
                stockMinimoPro
            FROM productos
            ORDER BY nombrePro ASC
        """)

        productos = cursor.fetchall()


        # ====================================================
        # PRODUCTOS CON POCO STOCK
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM productos
            WHERE stockPro <= stockMinimoPro
        """)

        resultado = cursor.fetchone()

        poco_stock = resultado["total"]


        # ====================================================
        # VALOR TOTAL DEL INVENTARIO
        # ====================================================

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(precioPro * stockPro),
                    0
                ) AS total
            FROM productos
        """)

        resultado = cursor.fetchone()

        valor_inventario = resultado["total"]


        # ====================================================
        # PRODUCTOS SIN STOCK
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM productos
            WHERE stockPro <= 0
        """)

        resultado = cursor.fetchone()

        sin_stock = resultado["total"]


        # ====================================================
        # RENDERIZAR
        # ====================================================

        return render_template(
            "admin/inventario.html",
            productos=productos,
            poco_stock=poco_stock,
            valor_inventario=valor_inventario,
            sin_stock=sin_stock
        )


    finally:

        cursor.close()
@app.route("/inventario/movimiento", methods=["POST"])
@administrador_requerido
def movimiento_inventario():

    cursor = None

    try:

        id_producto = request.form.get("idProducto")
        tipo = request.form.get("tipoMov")
        cantidad = request.form.get("cantidadMov")
        motivo = request.form.get("motivoMov", "").strip()

        id_usuario = session.get("idUsu")

        if not id_producto or not tipo or not cantidad or not motivo:
            flash(
                "Todos los campos son obligatorios.",
                "error"
            )

            return redirect(url_for("inventario"))

        try:
            cantidad = int(cantidad)
        except ValueError:

            flash(
                "La cantidad debe ser un número válido.",
                "error"
            )

            return redirect(url_for("inventario"))

        if cantidad <= 0:

            flash(
                "La cantidad debe ser mayor que cero.",
                "error"
            )

            return redirect(url_for("inventario"))

        if tipo not in ["Entrada", "Salida", "Ajuste"]:

            flash(
                "Tipo de movimiento no válido.",
                "error"
            )

            return redirect(url_for("inventario"))

        cursor = mysql.connection.cursor()

        # ------------------------------------------------
        # BUSCAR PRODUCTO
        # ------------------------------------------------

        cursor.execute("""
            SELECT
                idPro,
                nombrePro,
                stockPro
            FROM productos
            WHERE idPro = %s
            FOR UPDATE
        """, (id_producto,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "El producto no existe.",
                "error"
            )

            return redirect(url_for("inventario"))

        stock_actual = producto["stockPro"]

        # ------------------------------------------------
        # CALCULAR NUEVO STOCK
        # ------------------------------------------------

        if tipo == "Entrada":

            nuevo_stock = stock_actual + cantidad

        elif tipo == "Salida":

            nuevo_stock = stock_actual - cantidad

            if nuevo_stock < 0:

                flash(
                    "No hay suficiente stock para realizar esta salida.",
                    "error"
                )

                return redirect(url_for("inventario"))

        else:

            # Ajuste establece directamente el stock
            nuevo_stock = cantidad

        # ------------------------------------------------
        # ACTUALIZAR PRODUCTO
        # ------------------------------------------------

        cursor.execute("""
            UPDATE productos
            SET stockPro = %s
            WHERE idPro = %s
        """, (
            nuevo_stock,
            id_producto
        ))

        # ------------------------------------------------
        # REGISTRAR MOVIMIENTO
        # ------------------------------------------------

        cursor.execute("""
            INSERT INTO movimientos_inventario (
                idProductoMov,
                tipoMov,
                cantidadMov,
                idUsuarioMov,
                motivoMov
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            id_producto,
            tipo,
            cantidad,
            id_usuario,
            motivo
        ))

        mysql.connection.commit()

        flash(
            "Movimiento de inventario registrado correctamente.",
            "success"
        )

        return redirect(
            url_for("inventario")
        )

    except Exception as e:

        if mysql.connection:
            mysql.connection.rollback()

        print(
            "ERROR EN MOVIMIENTO DE INVENTARIO:",
            e
        )

        flash(
            "No fue posible realizar el movimiento.",
            "error"
        )

        return redirect(
            url_for("inventario")
        )

    finally:

        if cursor:
            cursor.close()
@app.route("/inventario/movimientos")
@administrador_requerido
def movimientos_inventario():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                m.idMov,
                p.nombrePro,
                m.tipoMov,
                m.cantidadMov,
                m.fechaMov,
                m.motivoMov,
                CONCAT(
                    u.nombreUsu,
                    ' ',
                    u.apellidoUsu
                ) AS usuario
            FROM movimientos_inventario m

            INNER JOIN productos p
                ON m.idProductoMov = p.idPro

            INNER JOIN usuarios u
                ON m.idUsuarioMov = u.idUsu

            ORDER BY m.fechaMov DESC
        """)

        movimientos = cursor.fetchall()

        return render_template(
            "admin/movimientos_inventario.html",
            movimientos=movimientos
        )

    finally:

        cursor.close()