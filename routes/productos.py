from app import app
from flask import render_template, request, redirect, flash, session
from config import mysql
import os
from werkzeug.utils import secure_filename


CARPETA = "static/img/productos"

@app.route("/producto/<int:id>")
def detalle_producto(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            productos.*,
            catalogo.nombreCat
        FROM productos
        LEFT JOIN catalogo
            ON productos.idCategoriaPro = catalogo.idCat
        WHERE productos.idPro = %s
    """, (id,))

    producto = cursor.fetchone()

    cursor.close()

    if not producto:
        flash("El producto no existe.", "danger")
        return redirect("/catalogo")

    return render_template(
        "cliente/producto.html",
        producto=producto
    )

@app.route("/gestion-productos")
def gestion_productos():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            productos.*,
            catalogo.nombreCat
        FROM productos
        INNER JOIN catalogo
            ON productos.idCategoriaPro = catalogo.idCat
        ORDER BY idPro DESC
    """)

    productos = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM catalogo
        ORDER BY nombreCat
    """)

    categorias = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin/gestion_productos.html",
        productos=productos,
        categorias=categorias
    )

@app.route("/nuevo-producto")
def nuevo_producto():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM catalogo
        ORDER BY nombreCat
    """)

    categorias = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin/nuevo_producto.html",
        categorias=categorias
    )

@app.route("/guardar-producto", methods=["POST"])
def guardar_producto():

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    stock = request.form["stock"]
    categoria = request.form["categoria"]

    imagen = request.files.get("imagen")

    nombreImagen = ""

    if imagen and imagen.filename != "":
        nombreImagen = secure_filename(imagen.filename)

        os.makedirs(CARPETA, exist_ok=True)

        imagen.save(
            os.path.join(CARPETA, nombreImagen)
        )

    cursor = mysql.connection.cursor()

    sql = """
        INSERT INTO productos
        (
            nombrePro,
            descripcionPro,
            imagenesPro,
            precioPro,
            stockPro,
            stockMinimoPro,
            disponiblePro,
            idCategoriaPro,
            fechaCreacionPro,
            fechaActualizacionPro
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            5,
            1,
            %s,
            NOW(),
            NOW()
        )
    """

    cursor.execute(sql, (
        nombre,
        descripcion,
        nombreImagen,
        precio,
        stock,
        categoria
    ))

    mysql.connection.commit()

    cursor.close()

    flash("Producto registrado correctamente.", "success")

    return redirect("/gestion-productos")

@app.route("/eliminar-producto/<int:id>")
def eliminar_producto(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT imagenesPro
        FROM productos
        WHERE idPro = %s
        """,
        (id,)
    )

    producto = cursor.fetchone()

    if producto and producto["imagenesPro"]:

        ruta = os.path.join(
            CARPETA,
            producto["imagenesPro"]
        )

        if os.path.exists(ruta):
            os.remove(ruta)

    cursor.execute(
        """
        DELETE FROM productos
        WHERE idPro = %s
        """,
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    flash("Producto eliminado correctamente.", "success")

    return redirect("/gestion-productos")

@app.route("/editar-producto/<int:id>")
def editar_producto(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM productos
        WHERE idPro = %s
        """,
        (id,)
    )

    producto = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM catalogo
        ORDER BY nombreCat
        """
    )

    categorias = cursor.fetchall()

    cursor.close()

    if not producto:
        flash("Producto no encontrado.", "danger")
        return redirect("/gestion-productos")

    return render_template(
        "admin/editar_producto.html",
        producto=producto,
        categorias=categorias
    )
@app.route("/actualizar-producto/<int:id>", methods=["POST"])
def actualizar_producto(id):

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    stock = request.form["stock"]
    categoria = request.form["categoria"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE productos
        SET
            nombrePro = %s,
            descripcionPro = %s,
            precioPro = %s,
            stockPro = %s,
            disponiblePro = CASE
                WHEN %s > 0 THEN 1
                ELSE 0
            END,
            idCategoriaPro = %s,
            fechaActualizacionPro = NOW()
        WHERE idPro = %s
        """,
        (
            nombre,
            descripcion,
            precio,
            stock,
            stock,
            categoria,
            id
        )
    )

    mysql.connection.commit()

    cursor.close()

    flash("Producto actualizado correctamente.", "success")

    return redirect("/gestion-productos")