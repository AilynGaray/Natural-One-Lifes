from app import app
from flask import render_template, redirect, session, request, flash
from config import mysql



def obtener_carrito(id_usuario):

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT idCar
            FROM carrito
            WHERE idUsuarioCar = %s
            AND estadoCar = 1
            LIMIT 1
        """, (id_usuario,))

        carrito = cursor.fetchone()

        if carrito:
            return carrito["idCar"]

        cursor.execute("""
            INSERT INTO carrito
            (
                idUsuarioCar,
                fechaCreacionCar,
                estadoCar
            )
            VALUES
            (
                %s,
                CURDATE(),
                1
            )
        """, (id_usuario,))

        mysql.connection.commit()

        return cursor.lastrowid

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR OBTENIENDO CARRITO:", e)

        raise

    finally:

        cursor.close()


@app.route("/agregar-carrito/<int:id>", methods=["GET", "POST"])
def agregar_carrito(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:

        flash(
            "Debes iniciar sesión para agregar productos al carrito.",
            "warning"
        )

        return redirect("/login")

    cantidad = request.form.get(
        "cantidad",
        1,
        type=int
    )

    if cantidad < 1:
        cantidad = 1

    cursor = mysql.connection.cursor()

    try:

        # ----------------------------------------------------
        # BUSCAR PRODUCTO
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                idPro,
                nombrePro,
                precioPro,
                stockPro,
                disponiblePro
            FROM productos
            WHERE idPro = %s
            AND disponiblePro = 1
            LIMIT 1
        """, (id,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "El producto no está disponible.",
                "danger"
            )

            return redirect("/catalogo")

        stock = int(producto["stockPro"] or 0)

        if stock <= 0:

            flash(
                "Este producto está agotado.",
                "danger"
            )

            return redirect(f"/producto/{id}")

        # ----------------------------------------------------
        # OBTENER CARRITO
        # ----------------------------------------------------

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

        else:

            cursor.execute("""
                INSERT INTO carrito
                (
                    idUsuarioCar,
                    fechaCreacionCar,
                    estadoCar
                )
                VALUES
                (
                    %s,
                    CURDATE(),
                    1
                )
            """, (id_usuario,))

            id_carrito = cursor.lastrowid

        # ----------------------------------------------------
        # VERIFICAR PRODUCTO EXISTENTE
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                idCai,
                cantidadCai
            FROM carritoItems
            WHERE idCarritoCai = %s
            AND idProductoCai = %s
            LIMIT 1
        """, (
            id_carrito,
            id
        ))

        existe = cursor.fetchone()

        if existe:

            nueva_cantidad = (
                int(existe["cantidadCai"]) + cantidad
            )

            if nueva_cantidad > stock:

                nueva_cantidad = stock

                flash(
                    "Se agregó solamente la cantidad disponible.",
                    "warning"
                )

            cursor.execute("""
                UPDATE carritoItems
                SET cantidadCai = %s
                WHERE idCai = %s
            """, (
                nueva_cantidad,
                existe["idCai"]
            ))

        else:

            if cantidad > stock:

                cantidad = stock

                flash(
                    "Se agregó solamente la cantidad disponible.",
                    "warning"
                )

            cursor.execute("""
                INSERT INTO carritoItems
                (
                    idCarritoCai,
                    idProductoCai,
                    cantidadCai,
                    precioUnitarioCai
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                id_carrito,
                id,
                cantidad,
                producto["precioPro"]
            ))

        mysql.connection.commit()

        flash(
            "Producto agregado al carrito correctamente.",
            "success"
        )

        return redirect("/carrito")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR AGREGANDO PRODUCTO:", e)

        flash(
            "Ocurrió un error al agregar el producto.",
            "danger"
        )

        return redirect("/catalogo")

    finally:

        cursor.close()


@app.route("/comprar-ahora/<int:id>", methods=["POST"])
def comprar_ahora(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:

        flash(
            "Debes iniciar sesión para comprar.",
            "warning"
        )

        return redirect("/login")

    cantidad = request.form.get(
        "cantidad",
        1,
        type=int
    )

    if cantidad < 1:
        cantidad = 1

    cursor = mysql.connection.cursor()

    try:

        # ----------------------------------------------------
        # BUSCAR PRODUCTO
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                idPro,
                nombrePro,
                precioPro,
                stockPro
            FROM productos
            WHERE idPro = %s
            AND disponiblePro = 1
            LIMIT 1
        """, (id,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "El producto no está disponible.",
                "danger"
            )

            return redirect("/catalogo")

        stock = int(producto["stockPro"] or 0)

        if stock <= 0:

            flash(
                "El producto está agotado.",
                "danger"
            )

            return redirect(f"/producto/{id}")

        if cantidad > stock:
            cantidad = stock

        # ----------------------------------------------------
        # OBTENER CARRITO
        # ----------------------------------------------------

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

        else:

            cursor.execute("""
                INSERT INTO carrito
                (
                    idUsuarioCar,
                    fechaCreacionCar,
                    estadoCar
                )
                VALUES
                (
                    %s,
                    CURDATE(),
                    1
                )
            """, (id_usuario,))

            id_carrito = cursor.lastrowid

        # ----------------------------------------------------
        # VERIFICAR PRODUCTO
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                idCai,
                cantidadCai
            FROM carritoItems
            WHERE idCarritoCai = %s
            AND idProductoCai = %s
            LIMIT 1
        """, (
            id_carrito,
            id
        ))

        existe = cursor.fetchone()

        if existe:

            nueva_cantidad = (
                int(existe["cantidadCai"]) + cantidad
            )

            if nueva_cantidad > stock:
                nueva_cantidad = stock

            cursor.execute("""
                UPDATE carritoItems
                SET cantidadCai = %s
                WHERE idCai = %s
            """, (
                nueva_cantidad,
                existe["idCai"]
            ))

        else:

            cursor.execute("""
                INSERT INTO carritoItems
                (
                    idCarritoCai,
                    idProductoCai,
                    cantidadCai,
                    precioUnitarioCai
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                id_carrito,
                id,
                cantidad,
                producto["precioPro"]
            ))

        mysql.connection.commit()

        return redirect("/checkout")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR EN COMPRAR AHORA:", e)

        flash(
            "Ocurrió un error al procesar la compra.",
            "danger"
        )

        return redirect(f"/producto/{id}")

    finally:

        cursor.close()


@app.route("/carrito")
def ver_carrito():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    
    pedido_exitoso = session.pop(
        "pedido_exitoso",
        None
    )

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
                productos.disponiblePro,

                carritoItems.cantidadCai,
                carritoItems.precioUnitarioCai,

                (
                    carritoItems.cantidadCai *
                    carritoItems.precioUnitarioCai
                ) AS subtotal

            FROM carritoItems

            INNER JOIN carrito
                ON carritoItems.idCarritoCai = carrito.idCar

            INNER JOIN productos
                ON carritoItems.idProductoCai = productos.idPro

            WHERE carrito.idUsuarioCar = %s
            AND carrito.estadoCar = 1

            ORDER BY carritoItems.idCai DESC

        """, (id_usuario,))

        items = cursor.fetchall()

        total = 0

        for item in items:

            item["cantidadCai"] = int(
                item["cantidadCai"] or 0
            )

            item["stockPro"] = int(
                item["stockPro"] or 0
            )

            item["precioUnitarioCai"] = float(
                item["precioUnitarioCai"] or 0
            )

            item["subtotal"] = (
                item["cantidadCai"] *
                item["precioUnitarioCai"]
            )

            total += item["subtotal"]

       
        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE idUsu = %s
            LIMIT 1
        """, (id_usuario,))

        usuario = cursor.fetchone()

        return render_template(
            "cliente/carrito.html",
            items=items,
            total=total,
            usuario=usuario,
            pedido_exitoso=pedido_exitoso
        )

    except Exception as e:

        print("ERROR CARGANDO CARRITO:", e)

        return (
            "Ocurrió un error al cargar el carrito.",
            500
        )

    finally:

        cursor.close()


@app.route("/aumentar/<int:id>")
def aumentar(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                carritoItems.idCai,
                carritoItems.cantidadCai,
                productos.stockPro

            FROM carritoItems

            INNER JOIN carrito
                ON carritoItems.idCarritoCai = carrito.idCar

            INNER JOIN productos
                ON carritoItems.idProductoCai = productos.idPro

            WHERE carritoItems.idCai = %s
            AND carrito.idUsuarioCar = %s
            AND carrito.estadoCar = 1

            LIMIT 1

        """, (
            id,
            id_usuario
        ))

        item = cursor.fetchone()

        if not item:

            flash(
                "El producto no existe en tu carrito.",
                "danger"
            )

            return redirect("/carrito")

        cantidad_actual = int(
            item["cantidadCai"] or 0
        )

        stock = int(
            item["stockPro"] or 0
        )

        if cantidad_actual < stock:

            cursor.execute("""
                UPDATE carritoItems
                SET cantidadCai = cantidadCai + 1
                WHERE idCai = %s
            """, (id,))

            mysql.connection.commit()

        else:

            flash(
                "No hay más unidades disponibles.",
                "warning"
            )

        return redirect("/carrito")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR AUMENTANDO CANTIDAD:", e)

        flash(
            "No fue posible aumentar la cantidad.",
            "danger"
        )

        return redirect("/carrito")

    finally:

        cursor.close()


@app.route("/disminuir/<int:id>")
def disminuir(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                carritoItems.cantidadCai

            FROM carritoItems

            INNER JOIN carrito
                ON carritoItems.idCarritoCai = carrito.idCar

            WHERE carritoItems.idCai = %s
            AND carrito.idUsuarioCar = %s
            AND carrito.estadoCar = 1

            LIMIT 1

        """, (
            id,
            id_usuario
        ))

        item = cursor.fetchone()

        if not item:
            return redirect("/carrito")

        cantidad = int(
            item["cantidadCai"] or 0
        )

        if cantidad > 1:

            cursor.execute("""
                UPDATE carritoItems
                SET cantidadCai = cantidadCai - 1
                WHERE idCai = %s
            """, (id,))

            mysql.connection.commit()

        else:

            flash(
                "La cantidad mínima es 1.",
                "warning"
            )

        return redirect("/carrito")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR DISMINUYENDO CANTIDAD:", e)

        flash(
            "No fue posible disminuir la cantidad.",
            "danger"
        )

        return redirect("/carrito")

    finally:

        cursor.close()


@app.route("/eliminar-carrito/<int:id>")
def eliminar_carrito(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect("/login")

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            DELETE carritoItems
            FROM carritoItems

            INNER JOIN carrito
                ON carritoItems.idCarritoCai = carrito.idCar

            WHERE carritoItems.idCai = %s
            AND carrito.idUsuarioCar = %s
            AND carrito.estadoCar = 1

        """, (
            id,
            id_usuario
        ))

        mysql.connection.commit()

        if cursor.rowcount > 0:

            flash(
                "Producto eliminado del carrito.",
                "success"
            )

        else:

            flash(
                "El producto no se encontró en tu carrito.",
                "warning"
            )

        return redirect("/carrito")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR ELIMINANDO PRODUCTO:", e)

        flash(
            "No fue posible eliminar el producto.",
            "danger"
        )

        return redirect("/carrito")

    finally:

        cursor.close()