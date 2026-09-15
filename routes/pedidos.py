from app import app
from flask import (
    render_template,
    request,
    redirect,
    session,
    flash
)

from config import mysql


# ==========================================================
# CHECKOUT
# ==========================================================

@app.route("/checkout")
def checkout():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    cursor = mysql.connection.cursor()

    try:

        # --------------------------------------------------
        # OBTENER CARRITO ACTIVO
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idCar

            FROM carrito

            WHERE idUsuarioCar = %s

            AND estadoCar = 1

            LIMIT 1
        """, (
            id_usuario,
        ))

        carrito = cursor.fetchone()

        if not carrito:

            flash(
                "Tu carrito está vacío.",
                "error"
            )

            return redirect("/carrito")

        # --------------------------------------------------
        # PRODUCTOS DEL CARRITO
        # --------------------------------------------------

        cursor.execute("""
            SELECT

                productos.idPro,

                productos.nombrePro,

                carritoItems.cantidadCai,

                carritoItems.precioUnitarioCai,

                (
                    carritoItems.cantidadCai *
                    carritoItems.precioUnitarioCai
                ) AS subtotal

            FROM carritoItems

            INNER JOIN productos
                ON carritoItems.idProductoCai =
                   productos.idPro

            WHERE carritoItems.idCarritoCai = %s
        """, (
            carrito["idCar"],
        ))

        items = cursor.fetchall()

        if not items:

            flash(
                "Tu carrito está vacío.",
                "error"
            )

            return redirect("/carrito")

        # --------------------------------------------------
        # CALCULAR TOTAL
        # --------------------------------------------------

        total = sum(
            float(item["subtotal"])
            for item in items
        )

        # --------------------------------------------------
        # OBTENER USUARIO
        # --------------------------------------------------

        cursor.execute("""
            SELECT *

            FROM usuarios

            WHERE idUsu = %s

            LIMIT 1
        """, (
            id_usuario,
        ))

        usuario = cursor.fetchone()

        # --------------------------------------------------
        # MOSTRAR CHECKOUT
        # --------------------------------------------------

        return render_template(
            "cliente/checkout.html",
            items=items,
            total=total,
            usuario=usuario
        )

    except Exception as e:

        print(
            "ERROR EN CHECKOUT:",
            e
        )

        flash(
            "Ocurrió un error al cargar el checkout.",
            "error"
        )

        return redirect("/carrito")

    finally:

        cursor.close()


# ==========================================================
# CREAR PEDIDO
# ==========================================================

@app.route(
    "/crear-pedido",
    methods=["POST"]
)
def crear_pedido():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    # ------------------------------------------------------
    # DATOS DEL FORMULARIO
    # ------------------------------------------------------

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    telefono = request.form.get(
        "telefono",
        ""
    ).strip()

    direccion = request.form.get(
        "direccion",
        ""
    ).strip()

    ciudad = request.form.get(
        "ciudad",
        ""
    ).strip()

    departamento = request.form.get(
        "departamento",
        ""
    ).strip()

    codigo_postal = request.form.get(
        "codigoPostal",
        ""
    ).strip()

    transportista = request.form.get(
        "transportista",
        ""
    ).strip()

    metodo_pago = request.form.get(
        "metodo_pago",
        ""
    ).strip()

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if not nombre:

        flash(
            "Debe ingresar el nombre completo.",
            "error"
        )

        return redirect("/checkout")

    if not telefono:

        flash(
            "Debe ingresar el número de teléfono.",
            "error"
        )

        return redirect("/checkout")

    if not direccion:

        flash(
            "Debe ingresar la dirección de envío.",
            "error"
        )

        return redirect("/checkout")

    if not ciudad:

        flash(
            "Debe ingresar la ciudad.",
            "error"
        )

        return redirect("/checkout")

    if not departamento:

        flash(
            "Debe ingresar el departamento.",
            "error"
        )

        return redirect("/checkout")

    if not transportista:

        flash(
            "Debe seleccionar un transportista.",
            "error"
        )

        return redirect("/checkout")

    if not metodo_pago:

        flash(
            "Debe seleccionar un método de pago.",
            "error"
        )

        return redirect("/checkout")

    cursor = mysql.connection.cursor()

    try:

        # --------------------------------------------------
        # OBTENER CARRITO ACTIVO
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idCar

            FROM carrito

            WHERE idUsuarioCar = %s

            AND estadoCar = 1

            LIMIT 1
        """, (
            id_usuario,
        ))

        carrito = cursor.fetchone()

        if not carrito:

            flash(
                "No tienes un carrito activo.",
                "error"
            )

            return redirect("/carrito")

        id_carrito = carrito["idCar"]

        # --------------------------------------------------
        # VERIFICAR PRODUCTOS
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS cantidad

            FROM carritoItems

            WHERE idCarritoCai = %s
        """, (
            id_carrito,
        ))

        resultado_cantidad = cursor.fetchone()

        cantidad = resultado_cantidad["cantidad"]

        if cantidad == 0:

            flash(
                "Tu carrito está vacío.",
                "error"
            )

            return redirect("/carrito")

        # --------------------------------------------------
        # CALCULAR TOTAL
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                SUM(
                    cantidadCai *
                    precioUnitarioCai
                ) AS total

            FROM carritoItems

            WHERE idCarritoCai = %s
        """, (
            id_carrito,
        ))

        resultado = cursor.fetchone()

        total = resultado["total"] or 0

        # --------------------------------------------------
        # CREAR PEDIDO
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO pedidos (
                idUsuarioPed,
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
                metodoPagoPed,
                notificadoPed
            )

            VALUES (
                %s,
                NOW(),
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (

            id_usuario,

            "Pendiente",

            total,

            direccion,

            nombre,

            telefono,

            ciudad,

            departamento,

            codigo_postal,

            transportista,

            metodo_pago,

            0
        ))

        # --------------------------------------------------
        # OBTENER ID DEL PEDIDO
        # --------------------------------------------------

        pedido_id = cursor.lastrowid

        # --------------------------------------------------
        # COPIAR PRODUCTOS DEL CARRITO AL PEDIDO
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO pedidoItems (
                idPedidoPei,
                idProductoPei,
                cantidadPei,
                precioUnitarioPei,
                subtotalPei
            )

            SELECT

                %s,

                idProductoCai,

                cantidadCai,

                precioUnitarioCai,

                cantidadCai *
                precioUnitarioCai

            FROM carritoItems

            WHERE idCarritoCai = %s
        """, (
            pedido_id,
            id_carrito
        ))

        # --------------------------------------------------
        # NOTIFICACIÓN DE PEDIDO CREADO
        # --------------------------------------------------

        mensaje = (
            f"Tu pedido #{pedido_id} "
            f"ha sido creado correctamente y se encuentra "
            f"en estado: Pendiente."
        )

        cursor.execute("""
            INSERT INTO notificaciones (
                idUsuarioNot,
                tipoNot,
                mensajeNot,
                fechaEnvioNot,
                leidaNot,
                referenciaIdNot
            )

            VALUES (
                %s,
                'pedido',
                %s,
                NOW(),
                0,
                %s
            )
        """, (
            id_usuario,
            mensaje,
            pedido_id
        ))

        # --------------------------------------------------
        # GUARDAR
        # --------------------------------------------------

        mysql.connection.commit()

        # --------------------------------------------------
        # IR AL PAGO
        # --------------------------------------------------

        return redirect(
            f"/pago/{pedido_id}"
        )

    except Exception as e:

        mysql.connection.rollback()

        print(
            "ERROR CREANDO PEDIDO:",
            e
        )

        flash(
            "Ocurrió un error al crear el pedido.",
            "error"
        )

        return redirect("/checkout")

    finally:

        cursor.close()


# ==========================================================
# LISTAR PEDIDOS
# ==========================================================

@app.route("/pedidos")
def pedidos():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    cursor = mysql.connection.cursor()

    try:

        # --------------------------------------------------
        # OBTENER PEDIDOS
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idPed,
                idUsuarioPed,
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

            ORDER BY fechaPed DESC
        """)

        pedidos = cursor.fetchall()

        return render_template(
            "admin/pedidos.html",
            pedidos=pedidos
        )

    except Exception as e:

        print(
            "ERROR CARGANDO PEDIDOS:",
            e
        )

        flash(
            "No se pudieron cargar los pedidos.",
            "error"
        )

        return redirect("/dashboard")

    finally:

        cursor.close()


# ==========================================================
# ACTUALIZAR ESTADO DEL PEDIDO
# ==========================================================

@app.route(
    "/actualizar-estado-pedido/<int:id_pedido>",
    methods=["POST"]
)
def actualizar_estado_pedido(id_pedido):

    # ------------------------------------------------------
    # COMPROBAR SESIÓN
    # ------------------------------------------------------

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    # ------------------------------------------------------
    # OBTENER NUEVO ESTADO
    # ------------------------------------------------------

    nuevo_estado = request.form.get(
        "estado",
        ""
    ).strip()

    # ------------------------------------------------------
    # ESTADOS PERMITIDOS
    # ------------------------------------------------------

    estados_permitidos = [
        "Pendiente",
        "En proceso",
        "Enviado",
        "Completado",
        "Cancelado"
    ]

    # ------------------------------------------------------
    # VALIDAR ESTADO
    # ------------------------------------------------------

    if nuevo_estado not in estados_permitidos:

        flash(
            "El estado seleccionado no es válido.",
            "error"
        )

        return redirect("/pedidos")

    cursor = mysql.connection.cursor()

    try:

        # --------------------------------------------------
        # OBTENER PEDIDO
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idPed,
                idUsuarioPed,
                estadoPed

            FROM pedidos

            WHERE idPed = %s

            LIMIT 1
        """, (
            id_pedido,
        ))

        pedido = cursor.fetchone()

        if not pedido:

            flash(
                "El pedido no existe.",
                "error"
            )

            return redirect("/pedidos")

        # --------------------------------------------------
        # ESTADO ANTERIOR
        # --------------------------------------------------

        estado_anterior = pedido["estadoPed"]

        # --------------------------------------------------
        # COMPROBAR SI REALMENTE CAMBIÓ
        # --------------------------------------------------

        if estado_anterior == nuevo_estado:

            flash(
                "El pedido ya tiene ese estado.",
                "error"
            )

            return redirect("/pedidos")

        # --------------------------------------------------
        # ACTUALIZAR ESTADO
        # --------------------------------------------------

        cursor.execute("""
            UPDATE pedidos

            SET
                estadoPed = %s

            WHERE idPed = %s
        """, (
            nuevo_estado,
            id_pedido
        ))

        # --------------------------------------------------
        # CREAR NOTIFICACIÓN
        # --------------------------------------------------

        mensaje = (
            f"El estado de tu pedido #{id_pedido} "
            f"ha cambiado a: {nuevo_estado}."
        )

        cursor.execute("""
            INSERT INTO notificaciones (
                idUsuarioNot,
                tipoNot,
                mensajeNot,
                fechaEnvioNot,
                leidaNot,
                referenciaIdNot
            )

            VALUES (
                %s,
                'pedido',
                %s,
                NOW(),
                0,
                %s
            )
        """, (
            pedido["idUsuarioPed"],
            mensaje,
            id_pedido
        ))

        # --------------------------------------------------
        # GUARDAR CAMBIOS
        # --------------------------------------------------

        mysql.connection.commit()

        flash(
            f"El pedido #{id_pedido} fue actualizado correctamente a '{nuevo_estado}'.",
            "success"
        )

    except Exception as e:

        mysql.connection.rollback()

        print(
            "ERROR ACTUALIZANDO ESTADO DEL PEDIDO:",
            e
        )

        flash(
            "No se pudo actualizar el estado del pedido.",
            "error"
        )

    finally:

        cursor.close()

    return redirect("/pedidos")