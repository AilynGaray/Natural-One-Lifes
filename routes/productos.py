from app import app
from flask import render_template, request, redirect, flash
from config import mysql
import os
from werkzeug.utils import secure_filename
from routes.permiso import administrador_requerido


CARPETA = "static/img/productos"


@app.route("/producto/<int:id>")
def detalle_producto(id):

    cursor = mysql.connection.cursor()

    try:
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

        if not producto:
            flash("El producto no existe.", "danger")
            return redirect("/catalogo")

        return render_template(
            "cliente/producto.html",
            producto=producto
        )

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR CONSULTANDO PRODUCTO:", e)

        flash(
            "No fue posible consultar el producto.",
            "danger"
        )

        return redirect("/catalogo")

    finally:
        cursor.close()


@app.route("/gestion-productos")
@administrador_requerido
def gestion_productos():

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                productos.*,
                catalogo.nombreCat
            FROM productos
            INNER JOIN catalogo
                ON productos.idCategoriaPro = catalogo.idCat
            ORDER BY productos.idPro DESC
        """)

        productos = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM catalogo
            ORDER BY nombreCat
        """)

        categorias = cursor.fetchall()

        return render_template(
            "admin/gestion_productos.html",
            productos=productos,
            categorias=categorias
        )

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR CARGANDO PRODUCTOS:", e)

        flash(
            "No fue posible cargar los productos.",
            "danger"
        )

        return redirect("/")

    finally:
        cursor.close()


@app.route("/nuevo-producto")
@administrador_requerido
def nuevo_producto():

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM catalogo
            ORDER BY nombreCat
        """)

        categorias = cursor.fetchall()

        return render_template(
            "admin/nuevo_producto.html",
            categorias=categorias
        )

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR CARGANDO CATEGORÍAS:", e)

        flash(
            "No fue posible cargar las categorías.",
            "danger"
        )

        return redirect("/gestion-productos")

    finally:
        cursor.close()


@app.route("/guardar-producto", methods=["POST"])
@administrador_requerido
def guardar_producto():

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio", "").strip()
    stock = request.form.get("stock", "").strip()
    categoria = request.form.get("categoria", "").strip()

    # Validación básica de los datos recibidos desde el formulario.
    if not nombre or not precio or not stock or not categoria:

        flash(
            "Completa todos los campos obligatorios.",
            "warning"
        )

        return redirect("/nuevo-producto")

    try:
        precio = float(precio)
        stock = int(stock)
        categoria = int(categoria)

    except ValueError:

        flash(
            "El precio, stock y categoría deben tener valores válidos.",
            "warning"
        )

        return redirect("/nuevo-producto")

    if precio < 0 or stock < 0:

        flash(
            "El precio y el stock no pueden ser negativos.",
            "warning"
        )

        return redirect("/nuevo-producto")

    imagen = request.files.get("imagen")

    nombreImagen = ""

    if imagen and imagen.filename:

        nombreImagen = secure_filename(imagen.filename)

        os.makedirs(CARPETA, exist_ok=True)

        imagen.save(
            os.path.join(CARPETA, nombreImagen)
        )

    cursor = mysql.connection.cursor()

    try:

        # Regla de negocio:
        # un producto solo está disponible si tiene stock mayor a cero.
        disponible = 1 if stock > 0 else 0

        cursor.execute("""
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
                %s,
                %s,
                NOW(),
                NOW()
            )
        """, (
            nombre,
            descripcion,
            nombreImagen,
            precio,
            stock,
            disponible,
            categoria
        ))

        mysql.connection.commit()

        flash(
            "Producto registrado correctamente.",
            "success"
        )

        return redirect("/gestion-productos")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR GUARDANDO PRODUCTO:", e)

        # Si la BD falla después de guardar la imagen,
        # se intenta eliminar el archivo para evitar archivos huérfanos.
        if nombreImagen:

            ruta = os.path.join(
                CARPETA,
                nombreImagen
            )

            if os.path.exists(ruta):

                try:
                    os.remove(ruta)
                except OSError:
                    pass

        flash(
            "No fue posible registrar el producto.",
            "danger"
        )

        return redirect("/nuevo-producto")

    finally:
        cursor.close()


@app.route("/eliminar-producto/<int:id>")
@administrador_requerido
def eliminar_producto(id):

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT imagenesPro
            FROM productos
            WHERE idPro = %s
        """, (id,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "El producto no existe.",
                "warning"
            )

            return redirect("/gestion-productos")

        nombre_imagen = producto["imagenesPro"]

        cursor.execute("""
            DELETE FROM productos
            WHERE idPro = %s
        """, (id,))

        mysql.connection.commit()

        # La imagen se elimina después de confirmar
        # correctamente la eliminación del registro.
        if nombre_imagen:

            ruta = os.path.join(
                CARPETA,
                nombre_imagen
            )

            if os.path.exists(ruta):

                try:
                    os.remove(ruta)
                except OSError as error:
                    print(
                        "No se pudo eliminar la imagen:",
                        error
                    )

        flash(
            "Producto eliminado correctamente.",
            "success"
        )

        return redirect("/gestion-productos")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR ELIMINANDO PRODUCTO:", e)

        flash(
            "No fue posible eliminar el producto.",
            "danger"
        )

        return redirect("/gestion-productos")

    finally:
        cursor.close()


@app.route("/editar-producto/<int:id>")
@administrador_requerido
def editar_producto(id):

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE idPro = %s
        """, (id,))

        producto = cursor.fetchone()

        if not producto:

            flash(
                "Producto no encontrado.",
                "danger"
            )

            return redirect("/gestion-productos")

        cursor.execute("""
            SELECT *
            FROM catalogo
            ORDER BY nombreCat
        """)

        categorias = cursor.fetchall()

        return render_template(
            "admin/editar_producto.html",
            producto=producto,
            categorias=categorias
        )

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR CARGANDO PRODUCTO:", e)

        flash(
            "No fue posible cargar el producto.",
            "danger"
        )

        return redirect("/gestion-productos")

    finally:
        cursor.close()


@app.route("/actualizar-producto/<int:id>", methods=["POST"])
@administrador_requerido
def actualizar_producto(id):

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio", "").strip()
    stock = request.form.get("stock", "").strip()
    categoria = request.form.get("categoria", "").strip()

    if not nombre or not precio or not stock or not categoria:

        flash(
            "Completa todos los campos obligatorios.",
            "warning"
        )

        return redirect(f"/editar-producto/{id}")

    try:

        precio = float(precio)
        stock = int(stock)
        categoria = int(categoria)

    except ValueError:

        flash(
            "Los valores ingresados no son válidos.",
            "warning"
        )

        return redirect(f"/editar-producto/{id}")

    if precio < 0 or stock < 0:

        flash(
            "El precio y el stock no pueden ser negativos.",
            "warning"
        )

        return redirect(f"/editar-producto/{id}")

    cursor = mysql.connection.cursor()

    try:

        # Regla de negocio:
        # si el stock es mayor a cero, el producto queda disponible.
        disponible = 1 if stock > 0 else 0

        cursor.execute("""
            UPDATE productos
            SET
                nombrePro = %s,
                descripcionPro = %s,
                precioPro = %s,
                stockPro = %s,
                disponiblePro = %s,
                idCategoriaPro = %s,
                fechaActualizacionPro = NOW()
            WHERE idPro = %s
        """, (
            nombre,
            descripcion,
            precio,
            stock,
            disponible,
            categoria,
            id
        ))

        mysql.connection.commit()

        flash(
            "Producto actualizado correctamente.",
            "success"
        )

        return redirect("/gestion-productos")

    except Exception as e:

        mysql.connection.rollback()

        print("ERROR ACTUALIZANDO PRODUCTO:", e)

        flash(
            "No fue posible actualizar el producto.",
            "danger"
        )

        return redirect(f"/editar-producto/{id}")

    finally:
        cursor.close()