from app import app
from flask import render_template, request, redirect, session, flash
from config import mysql

@app.route("/pago/<int:id>")
def pago(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    cursor = mysql.connection.cursor()

    try:

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

            WHERE idPed = %s
            AND idUsuarioPed = %s

            LIMIT 1

        """, (
            id,
            id_usuario
        ))

        pedido = cursor.fetchone()

        if not pedido:

            flash(
                "El pedido no existe.",
                "error"
            )

            return redirect("/carrito")

       

        if pedido["estadoPed"] == "Pagado":

            session["pedido_exitoso"] = {
                "id": pedido["idPed"],
                "total": float(
                    pedido["totalPed"] or 0
                )
            }

            return redirect("/carrito")

    

        if pedido["estadoPed"] == "Rechazado":

            flash(
                "Este pedido tiene un pago rechazado. Tu carrito permanece disponible.",
                "error"
            )

            return redirect("/carrito")

        return render_template(
            "cliente/pago.html",
            pedido=pedido
        )

    except Exception as e:

        print(
            "ERROR MOSTRANDO PAGO:",
            e
        )

        flash(
            "Ocurrió un error al cargar el pago.",
            "error"
        )

        return redirect("/carrito")

    finally:

        cursor.close()

@app.route("/procesar-pago", methods=["POST"])
def procesar_pago():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    id_pedido = request.form.get(
        "pedido"
    )

    resultado = request.form.get(
        "resultado"
    )

    if not id_pedido:

        flash(
            "No se encontró el pedido.",
            "error"
        )

        return redirect("/carrito")

    cursor = mysql.connection.cursor()

    try:

       

        cursor.execute("""
            SELECT

                idPed,
                idUsuarioPed,
                totalPed,
                estadoPed,
                metodoPagoPed

            FROM pedidos

            WHERE idPed = %s
            AND idUsuarioPed = %s

            LIMIT 1

        """, (
            id_pedido,
            id_usuario
        ))

        pedido = cursor.fetchone()

        if not pedido:

            flash(
                "El pedido no existe.",
                "error"
            )

            return redirect("/carrito")

       

        if pedido["estadoPed"] == "Pagado":

            session["pedido_exitoso"] = {
                "id": pedido["idPed"],
                "total": float(
                    pedido["totalPed"] or 0
                )
            }

            return redirect("/carrito")

        metodo = pedido["metodoPagoPed"]

       

        if resultado == "aprobado":

          

            cursor.execute("""
                UPDATE pedidos

                SET estadoPed = 'Pagado'

                WHERE idPed = %s
                AND idUsuarioPed = %s

            """, (
                id_pedido,
                id_usuario
            ))

           

            cursor.execute("""
                INSERT INTO facturas
                (
                    idUsuarioFac,
                    idPedidoFac,
                    fechaEmisionFac,
                    totalFac,
                    estadoFac,
                    metodoPagoFac
                )

                SELECT

                    idUsuarioPed,
                    idPed,
                    NOW(),
                    totalPed,
                    'Generada',
                    %s

                FROM pedidos

                WHERE idPed = %s

            """, (
                metodo,
                id_pedido
            ))

          

            cursor.execute("""
                UPDATE pedidos

                SET notificadoPed = 0

                WHERE idPed = %s
                AND idUsuarioPed = %s

            """, (
                id_pedido,
                id_usuario
            ))


            cursor.execute("""
                SELECT idCar
                FROM carrito

                WHERE idUsuarioCar = %s
                AND estadoCar = 1

                LIMIT 1

            """, (id_usuario,))

            carrito = cursor.fetchone()

            

            if carrito:

                id_carrito = carrito["idCar"]

                cursor.execute("""
                    UPDATE carrito

                    SET estadoCar = 0

                    WHERE idCar = %s
                    AND idUsuarioCar = %s

                """, (
                    id_carrito,
                    id_usuario
                ))

            

            mysql.connection.commit()


            session["pedido_exitoso"] = {
                "id": int(pedido["idPed"]),
                "total": float(
                    pedido["totalPed"] or 0
                )
            }

            return redirect("/carrito")

        else:

            cursor.execute("""
                UPDATE pedidos

                SET estadoPed = 'Rechazado'

                WHERE idPed = %s
                AND idUsuarioPed = %s

            """, (
                id_pedido,
                id_usuario
            ))

            mysql.connection.commit()

            return redirect("/pago-rechazado")

    except Exception as e:

        mysql.connection.rollback()

        print(
            "ERROR AL PROCESAR PAGO:",
            e
        )

        flash(
            "Ocurrió un error al procesar el pago.",
            "error"
        )

        return redirect(
            "/pago/" + str(id_pedido)
        )

    finally:

        cursor.close()



@app.route("/pago-exitoso")
def pago_exitoso():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")


    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                idPed,
                totalPed

            FROM pedidos

            WHERE idUsuarioPed = %s
            AND estadoPed = 'Pagado'

            ORDER BY idPed DESC

            LIMIT 1

        """, (id_usuario,))

        pedido = cursor.fetchone()

        if pedido:

            session["pedido_exitoso"] = {
                "id": int(pedido["idPed"]),
                "total": float(
                    pedido["totalPed"] or 0
                )
            }

        return redirect("/carrito")

    except Exception as e:

        print(
            "ERROR EN PAGO EXITOSO:",
            e
        )

        return redirect("/carrito")

    finally:

        cursor.close()



@app.route("/pago-rechazado")
def pago_rechazado():

    return render_template(
        "cliente/pago_rechazado.html"
    )