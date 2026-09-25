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


def obtener_producto_disponible(id_producto):
    cursor = mysql.connection.cursor()

    try:
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
        """, (id_producto,))

        return cursor.fetchone()

    finally:
        cursor.close()


def validar_stock_disponible(producto, cantidad):
    stock = int(producto["stockPro"] or 0)

    if stock <= 0:
        return False, 0

    if cantidad > stock:
        return True, stock

    return True, cantidad


def obtener_item_carrito(id_carrito, id_producto):
    cursor = mysql.connection.cursor()

    try:
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
            id_producto
        ))

        return cursor.fetchone()

    finally:
        cursor.close()