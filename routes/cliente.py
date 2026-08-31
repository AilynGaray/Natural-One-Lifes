from app import app
from flask import flash, render_template, request, redirect, session, url_for
from routes.permiso import login_requerido
from config import mysql
import os
from werkzeug.utils import secure_filename

@app.route("/inicio")
@login_requerido
def inicio():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                p.idPro,
                p.nombrePro,
                p.descripcionPro,
                p.imagenesPro,
                p.precioPro,
                p.stockPro,
                p.disponiblePro,
                p.idCategoriaPro,
                c.nombreCat
            FROM productos p
            LEFT JOIN catalogo c
                ON p.idCategoriaPro = c.idCat
            WHERE p.disponiblePro = 1
            ORDER BY p.idPro DESC
            LIMIT 6
        """)

        productos = cursor.fetchall()

        cursor.execute("""
            SELECT
                idCat,
                nombreCat,
                descripcionCat
            FROM catalogo
            WHERE estadoCat = 1
            ORDER BY nombreCat
        """)

        categorias = cursor.fetchall()

        return render_template(
            "cliente/inicio.html",
            productos=productos,
            categorias=categorias
        )

    finally:
        cursor.close()


@app.route("/catalogo")
@login_requerido
def catalogo():

    cursor = mysql.connection.cursor()

    try:

        categoria_id = request.args.get("categoria", type=int)

        buscar = request.args.get("buscar", "").strip()



        if categoria_id and buscar:

            texto_busqueda = f"%{buscar}%"

            cursor.execute("""
                SELECT
                    p.*,
                    c.nombreCat
                FROM productos p

                LEFT JOIN catalogo c
                    ON p.idCategoriaPro = c.idCat

                WHERE p.disponiblePro = 1

                AND p.idCategoriaPro = %s

                AND (
                    p.nombrePro LIKE %s
                    OR p.descripcionPro LIKE %s
                )

                ORDER BY p.idPro DESC

            """, (
                categoria_id,
                texto_busqueda,
                texto_busqueda
            ))


        # --------------------------------------------------
        # SI SOLO HAY CATEGORÍA
        # --------------------------------------------------

        elif categoria_id:

            cursor.execute("""
                SELECT
                    p.*,
                    c.nombreCat
                FROM productos p

                LEFT JOIN catalogo c
                    ON p.idCategoriaPro = c.idCat

                WHERE p.disponiblePro = 1

                AND p.idCategoriaPro = %s

                ORDER BY p.idPro DESC

            """, (categoria_id,))


        # --------------------------------------------------
        # SI SOLO HAY BÚSQUEDA
        # --------------------------------------------------

        elif buscar:

            texto_busqueda = f"%{buscar}%"

            cursor.execute("""
                SELECT
                    p.*,
                    c.nombreCat
                FROM productos p

                LEFT JOIN catalogo c
                    ON p.idCategoriaPro = c.idCat

                WHERE p.disponiblePro = 1

                AND (
                    p.nombrePro LIKE %s
                    OR p.descripcionPro LIKE %s
                )

                ORDER BY p.idPro DESC

            """, (
                texto_busqueda,
                texto_busqueda
            ))


        # --------------------------------------------------
        # SI NO HAY CATEGORÍA NI BÚSQUEDA
        # --------------------------------------------------

        else:

            cursor.execute("""
                SELECT
                    p.*,
                    c.nombreCat
                FROM productos p

                LEFT JOIN catalogo c
                    ON p.idCategoriaPro = c.idCat

                WHERE p.disponiblePro = 1

                ORDER BY p.idPro DESC

            """)


        productos = cursor.fetchall()



        cursor.execute("""
            SELECT
                idCat,
                nombreCat,
                descripcionCat,
                estadoCat
            FROM catalogo

            WHERE estadoCat = 1

            ORDER BY nombreCat
        """)

        categorias = cursor.fetchall()


       
        categoria_seleccionada = None

        if categoria_id:

            cursor.execute("""
                SELECT
                    idCat,
                    nombreCat,
                    descripcionCat
                FROM catalogo

                WHERE idCat = %s

                AND estadoCat = 1

            """, (categoria_id,))

            categoria_seleccionada = cursor.fetchone()


       

        return render_template(
            "cliente/catalogo_de_productos.html",

            productos=productos,

            categorias=categorias,

            categoria_seleccionada=categoria_seleccionada,

            categoria_id=categoria_id,

            buscar=buscar
        )


    except Exception as e:

        print("ERROR AL CARGAR CATÁLOGO:", e)

        return (
            "Ocurrió un error al cargar el catálogo.",
            500
        )


    finally:

        cursor.close()

# ==========================================================
# DETALLE DEL PRODUCTO
# ==========================================================

@app.route("/producto")
@login_requerido
def producto():

    id_producto = request.args.get("id", type=int)

    if not id_producto:
        return redirect(url_for("catalogo"))

    id_usuario = session.get("idUsu")

    cursor = mysql.connection.cursor()

    try:

        # ==================================================
        # OBTENER PRODUCTO
        # ==================================================

        cursor.execute("""
            SELECT
                p.*,
                c.nombreCat
            FROM productos p

            LEFT JOIN catalogo c
                ON p.idCategoriaPro = c.idCat

            WHERE p.idPro = %s

            LIMIT 1
        """, (id_producto,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "El producto no existe.",
                "error"
            )

            return redirect(url_for("catalogo"))


        # ==================================================
        # OBTENER VALORACIONES
        # ==================================================

        cursor.execute("""
            SELECT
                v.idVal,
                v.calificacionVal,
                v.comentarioVal,
                v.fechaVal,

                u.idUsu,
                u.nombreUsu,
                u.apellidoUsu,
                u.fotoUsu

            FROM valoraciones v

            INNER JOIN usuarios u
                ON v.idUsuarioVal = u.idUsu

            WHERE v.idProductoVal = %s

            ORDER BY v.fechaVal DESC, v.idVal DESC

        """, (id_producto,))

        valoraciones = cursor.fetchall()


        # ==================================================
        # CALCULAR PROMEDIO
        # ==================================================

        cursor.execute("""
            SELECT
                COALESCE(
                    AVG(calificacionVal),
                    0
                ) AS promedio,

                COUNT(*) AS total

            FROM valoraciones

            WHERE idProductoVal = %s
        """, (id_producto,))

        resultado = cursor.fetchone()

        promedio = float(
            resultado["promedio"] or 0
        )

        total_valoraciones = int(
            resultado["total"] or 0
        )


        # ==================================================
        # VALORACIÓN DEL USUARIO ACTUAL
        # ==================================================

        mi_valoracion = None

        if id_usuario:

            cursor.execute("""
                SELECT
                    idVal,
                    calificacionVal,
                    comentarioVal,
                    fechaVal

                FROM valoraciones

                WHERE idUsuarioVal = %s

                AND idProductoVal = %s

                LIMIT 1

            """, (
                id_usuario,
                id_producto
            ))

            mi_valoracion = cursor.fetchone()


        # ==================================================
        # INFORMACIÓN DEL USUARIO
        # ==================================================

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

            LIMIT 1

        """, (id_usuario,))

        usuario = cursor.fetchone()


        # ==================================================
        # MOSTRAR PRODUCTO
        # ==================================================

        return render_template(
            "cliente/producto.html",

            producto=producto,

            usuario=usuario,

            valoraciones=valoraciones,

            promedio=promedio,

            total_valoraciones=total_valoraciones,

            mi_valoracion=mi_valoracion
        )


    except Exception as e:

        print(
            "ERROR CARGANDO DETALLE DEL PRODUCTO:",
            e
        )

        return (
            "Ocurrió un error al cargar el detalle del producto.",
            500
        )


    finally:

        cursor.close()
@app.route("/perfil")
@login_requerido
def perfil():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:


        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                emailUsu,
                telefonoUsu,
                direccionUsu,
                fotoUsu,
                fechaNacimientoUsu,
                activoUsu,
                registroUsu,
                idRol,
                notificaciones_pedidos,
                recordatorios_citas,
                promociones
            FROM usuarios
            WHERE idUsu = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario:
            session.clear()
            return redirect(url_for("login"))

       

        cursor.execute("""
            SELECT
                idPed,
                fechaPed,
                estadoPed,
                totalPed,
                direccionEnvioPed,
                nombreEnvioPed,
                telefonoEnvioPed,
                ciudadEnvioPed,
                departamentoEnvioPed,
                codigoPostalEnvioPed,
                transportistaPed,
                metodoPagoPed
            FROM pedidos
            WHERE idUsuarioPed = %s
            ORDER BY fechaPed DESC, idPed DESC
        """, (id_usuario,))

        pedidos_db = cursor.fetchall()

        pedidos = []

        for pedido in pedidos_db:

            pedidos.append({
                "id": pedido["idPed"],
                "fecha": pedido["fechaPed"],
                "estado": pedido["estadoPed"] or "Pendiente",
                "total": pedido["totalPed"] or 0,
                "direccion": pedido["direccionEnvioPed"] or "",
                "nombre": pedido["nombreEnvioPed"] or "",
                "telefono": pedido["telefonoEnvioPed"] or "",
                "ciudad": pedido["ciudadEnvioPed"] or "",
                "departamento": pedido["departamentoEnvioPed"] or "",
                "codigo_postal": pedido["codigoPostalEnvioPed"] or "",
                "transportista": pedido["transportistaPed"] or "Pendiente",
                "metodo_pago": pedido["metodoPagoPed"] or "Pendiente"
            })

       

        cursor.execute("""
            SELECT
                c.idCit,
                c.fechaCit,
                c.horaCit,
                c.estadoCit,
                c.motivoCit,

                p.nombreProfe,
                p.especialidadProfe,
                p.telefonoProfe,
                p.correoProfe

            FROM citas c

            LEFT JOIN profesionales p
                ON c.idProfesionalCit = p.idProfe

            WHERE c.idUsuarioCit = %s

            ORDER BY
                c.fechaCit DESC,
                c.horaCit DESC,
                c.idCit DESC
        """, (id_usuario,))

        citas_db = cursor.fetchall()

        citas = []

        for cita in citas_db:

            citas.append({
                "id": cita["idCit"],
                "fecha": cita["fechaCit"],
                "hora": cita["horaCit"],
                "estado": cita["estadoCit"] or "Pendiente",
                "motivo": cita["motivoCit"] or "",
                "profesional": cita["nombreProfe"] or "No asignado",
                "especialidad": cita["especialidadProfe"] or "No especificada",
                "telefono": cita["telefonoProfe"] or "",
                "correo": cita["correoProfe"] or ""
            })

       

        return render_template(
            "cliente/perfil.html",
            usuario=usuario,
            pedidos=pedidos,
            citas=citas
        )

    except Exception as e:

        print("ERROR AL CARGAR PERFIL:", e)

        return "Ocurrió un error al cargar el perfil.", 500

    finally:

        cursor.close()

@app.route("/editar-perfil", methods=["GET", "POST"])
@login_requerido
def editar_perfil():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:

        if request.method == "POST":

            nombre = request.form.get("nombre")
            correo = request.form.get("correo")
            telefono = request.form.get("telefono")

            foto = request.files.get("foto")

            cursor.execute("""
                UPDATE usuarios
                SET
                    nombreUsu = %s,
                    emailUsu = %s,
                    telefonoUsu = %s
                WHERE idUsu = %s
            """, (
                nombre,
                correo,
                telefono,
                id_usuario
            ))


            if foto and foto.filename:

                nombre_foto = secure_filename(foto.filename)

                carpeta = os.path.join(
                    app.root_path,
                    "static",
                    "img",
                    "perfiles"
                )

                os.makedirs(carpeta, exist_ok=True)

                ruta = os.path.join(
                    carpeta,
                    nombre_foto
                )

                foto.save(ruta)

                cursor.execute("""
                    UPDATE usuarios
                    SET fotoUsu = %s
                    WHERE idUsu = %s
                """, (
                    nombre_foto,
                    id_usuario
                ))

            mysql.connection.commit()

            return redirect(url_for("perfil"))

        

        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE idUsu = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario:
            session.clear()
            return redirect(url_for("login"))

        return render_template(
            "cliente/editar_perfil.html",
            usuario=usuario
        )

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR EDITANDO PERFIL:", e)

        return "Ocurrió un error al editar el perfil.", 500

    finally:

        cursor.close()




@app.route("/subir-examen")
@login_requerido
def subir_examen():

    return render_template(
        "cliente/subir_examen.html"
    )


@app.route("/guardar-examen", methods=["POST"])
@login_requerido
def guardar_examen():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    materia = request.form.get("materia")
    archivo = request.files.get("archivo")

    if not titulo or not descripcion or not materia or not archivo:
        return "Todos los campos son obligatorios.", 400

    if archivo.filename == "":
        return "Debes seleccionar un archivo.", 400

    nombre_archivo = secure_filename(
        archivo.filename
    )

    carpeta = os.path.join(
        app.root_path,
        "static",
        "uploads",
        "examenes"
    )

    os.makedirs(
        carpeta,
        exist_ok=True
    )

    ruta_archivo = os.path.join(
        carpeta,
        nombre_archivo
    )

    archivo.save(ruta_archivo)

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO examenes (
                idUsuarioExamen,
                tituloExamen,
                descripcionExamen,
                materiaExamen,
                archivoExamen
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            id_usuario,
            titulo,
            descripcion,
            materia,
            nombre_archivo
        ))

        mysql.connection.commit()

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR GUARDANDO EXAMEN:", e)

        return "Ocurrió un error al guardar el examen.", 500

    finally:

        cursor.close()

    return redirect(
        url_for("subir_examen")
    )



@app.route("/gestion-citas")
@app.route("/gestion_citas")
@login_requerido
def gestion_citas():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:


        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE idUsu = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario:

            session.clear()

            return redirect(url_for("login"))

        
        cursor.execute("""
            SELECT
                idDisp,
                idProfesionalDisp,
                diaDisp,
                horaInicioDisp,
                horaFinDisp,
                estadoDisp,
                fechaDisp
            FROM disponibilidad
            WHERE estadoDisp = 1
            ORDER BY fechaDisp, horaInicioDisp
        """)

        disponibilidad_db = cursor.fetchall()

        disponibilidad = []

        for dia in disponibilidad_db:

            disponibilidad.append({
                "idDisp": dia["idDisp"],
                "idProfesionalDisp": dia["idProfesionalDisp"],
                "diaDisp": str(dia["diaDisp"]),
                "horaInicioDisp": str(dia["horaInicioDisp"]),
                "horaFinDisp": str(dia["horaFinDisp"]),
                "estadoDisp": int(dia["estadoDisp"]),
                "fechaDisp": str(dia["fechaDisp"])
            })

       

        cursor.execute("""
            SELECT
                idProfe,
                nombreProfe,
                especialidadProfe
            FROM profesionales
            WHERE activoProfe = 1
            ORDER BY nombreProfe
        """)

        profesionales = cursor.fetchall()

       

        cursor.execute("""
            SELECT
                c.idCit,
                c.fechaCit,
                c.horaCit,
                c.estadoCit,
                c.motivoCit,
                p.nombreProfe,
                p.especialidadProfe

            FROM citas c

            INNER JOIN profesionales p
                ON c.idProfesionalCit = p.idProfe

            WHERE c.idUsuarioCit = %s

            ORDER BY
                c.fechaCit DESC,
                c.horaCit DESC
        """, (id_usuario,))

        citas = cursor.fetchall()

        return render_template(
            "cliente/gestion_citas_usuarios.html",
            disponibilidad=disponibilidad,
            profesionales=profesionales,
            citas=citas,
            usuario=usuario
        )

    except Exception as e:

        print("ERROR GESTION CITAS:", e)

        return "Ocurrió un error al cargar las citas.", 500

    finally:

        cursor.close()



@app.route("/carrito")
@login_requerido
def carrito():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                carritoItems.idCai,
                carritoItems.idProductoCai,
                productos.nombrePro,
                productos.descripcionPro,
                productos.imagenesPro,
                productos.stockPro,
                carritoItems.cantidadCai,
                carritoItems.precioUnitarioCai,

                (
                    carritoItems.cantidadCai *
                    carritoItems.precioUnitarioCai
                ) AS subtotal

            FROM carritoItems

            INNER JOIN carrito
                ON carritoItems.idCarritoCai =
                   carrito.idCar

            INNER JOIN productos
                ON carritoItems.idProductoCai =
                   productos.idPro

            WHERE carrito.idUsuarioCar = %s
            AND carrito.estadoCar = 1

            ORDER BY carritoItems.idCai DESC
        """, (id_usuario,))

        items = cursor.fetchall()

        total = 0

        for item in items:

            total += float(
                item["subtotal"] or 0
            )

        return render_template(
            "cliente/carrito.html",
            items=items,
            total=total
        )

    finally:

        cursor.close()


@app.route("/guardar-notificaciones", methods=["POST"])
@login_requerido
def guardar_notificaciones():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    pedidos = 1 if request.form.get("pedidos") else 0
    citas = 1 if request.form.get("citas") else 0
    promociones = 1 if request.form.get("promociones") else 0

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            UPDATE usuarios
            SET
                notificaciones_pedidos = %s,
                recordatorios_citas = %s,
                promociones = %s
            WHERE idUsu = %s
        """, (
            pedidos,
            citas,
            promociones,
            id_usuario
        ))

        mysql.connection.commit()

    except Exception as e:

        mysql.connection.rollback()

        print(
            "ERROR GUARDANDO NOTIFICACIONES:",
            e
        )

        return "No se pudieron guardar las notificaciones.", 500

    finally:

        cursor.close()

    return redirect(
        url_for("perfil")
    )
# ==========================================================
# VALORACIONES DE PRODUCTOS
# ==========================================================
# ==========================================================
# VALORAR PRODUCTO
# ==========================================================

@app.route(
    "/producto/<int:id>/valorar",
    methods=["POST"]
)
@login_requerido
def valorar_producto(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:

        flash(
            "Debes iniciar sesión para valorar un producto.",
            "error"
        )

        return redirect(
            url_for("producto", id=id)
        )

    # ======================================================
    # DATOS
    # ======================================================

    calificacion = request.form.get(
        "calificacion",
        ""
    ).strip()

    comentario = request.form.get(
        "comentario",
        ""
    ).strip()

    # ======================================================
    # VALIDAR CALIFICACIÓN
    # ======================================================

    try:

        calificacion = int(calificacion)

    except (ValueError, TypeError):

        flash(
            "Debes seleccionar una calificación.",
            "error"
        )

        return redirect(
            url_for("producto", id=id)
        )

    if calificacion < 1 or calificacion > 5:

        flash(
            "La calificación debe estar entre 1 y 5 estrellas.",
            "error"
        )

        return redirect(
            url_for("producto", id=id)
        )

    # ======================================================
    # VALIDAR COMENTARIO
    # ======================================================

    if not comentario:

        flash(
            "Debes escribir un comentario.",
            "error"
        )

        return redirect(
            url_for("producto", id=id)
        )

    if len(comentario) < 5:

        flash(
            "El comentario debe tener al menos 5 caracteres.",
            "error"
        )

        return redirect(
            url_for("producto", id=id)
        )

    if len(comentario) > 1000:

        flash(
            "El comentario no puede superar los 1000 caracteres.",
            "error"
        )

        return redirect(
            url_for("producto", id=id)
        )

    cursor = mysql.connection.cursor()

    try:

        # ==================================================
        # COMPROBAR PRODUCTO
        # ==================================================

        cursor.execute("""
            SELECT idPro
            FROM productos
            WHERE idPro = %s
            LIMIT 1
        """, (id,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "El producto no existe.",
                "error"
            )

            return redirect(
                url_for("catalogo")
            )

        # ==================================================
        # BUSCAR VALORACIÓN EXISTENTE
        # ==================================================

        cursor.execute("""
            SELECT idVal
            FROM valoraciones

            WHERE idUsuarioVal = %s
            AND idProductoVal = %s

            LIMIT 1
        """, (
            id_usuario,
            id
        ))

        existente = cursor.fetchone()

        # ==================================================
        # ACTUALIZAR
        # ==================================================

        if existente:

            cursor.execute("""
                UPDATE valoraciones

                SET
                    calificacionVal = %s,
                    comentarioVal = %s,
                    fechaVal = NOW()

                WHERE idVal = %s
            """, (
                calificacion,
                comentario,
                existente["idVal"]
            ))

            mensaje = (
                "Tu valoración fue actualizada correctamente."
            )

        # ==================================================
        # CREAR
        # ==================================================

        else:

            cursor.execute("""
                INSERT INTO valoraciones
                (
                    idUsuarioVal,
                    idProductoVal,
                    calificacionVal,
                    comentarioVal,
                    fechaVal
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
            """, (
                id_usuario,
                id,
                calificacion,
                comentario
            ))

            mensaje = (
                "Tu valoración fue publicada correctamente."
            )

        mysql.connection.commit()

        flash(
            mensaje,
            "success"
        )

    except Exception as e:

        mysql.connection.rollback()

        print(
            "ERROR GUARDANDO VALORACIÓN:",
            e
        )

        flash(
            "No se pudo guardar la valoración.",
            "error"
        )

    finally:

        cursor.close()

    return redirect(
        url_for(
            "producto",
            id=id
        )
    )