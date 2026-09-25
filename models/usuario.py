from config import mysql
def buscar_por_email(email):
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                usuarioUsu,
                emailUsu,
                passwordUsu,
                activoUsu,
                idRol
            FROM usuarios
            WHERE LOWER(emailUsu) = LOWER(%s)
            LIMIT 1
        """, (email,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
def buscar_por_usuario_o_email(usuario):
    cursor = None
    try:
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
        """, (usuario, usuario))

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()


def buscar_rol_cliente():
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT idRol
            FROM roles
            WHERE nombreRol = 'Cliente'
            LIMIT 1
        """)

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()


def existe_email(email):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT idUsu
            FROM usuarios
            WHERE LOWER(emailUsu) = LOWER(%s)
            LIMIT 1
        """, (email,))

        return cursor.fetchone() is not None

    finally:
        if cursor:
            cursor.close()


def existe_usuario(usuario):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT idUsu
            FROM usuarios
            WHERE usuarioUsu = %s
            LIMIT 1
        """, (usuario,))

        return cursor.fetchone() is not None

    finally:
        if cursor:
            cursor.close()


def crear_usuario(
    nombre,
    apellido,
    usuario,
    email,
    password_hash,
    id_rol
):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

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
            id_rol
        ))

        mysql.connection.commit()

        return cursor.lastrowid

    except Exception:
        mysql.connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()


def obtener_usuario_por_id(id_usuario):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                idUsu,
                nombreUsu,
                apellidoUsu,
                usuarioUsu,
                emailUsu,
                activoUsu,
                idRol
            FROM usuarios
            WHERE idUsu = %s
            LIMIT 1
        """, (id_usuario,))

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()


def actualizar_password(id_usuario, password_hash):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            UPDATE usuarios
            SET
                passwordUsu = %s,
                intentosFallidosUsu = 0,
                bloqueoHastaUsu = NULL
            WHERE idUsu = %s
        """, (
            password_hash,
            id_usuario
        ))

        mysql.connection.commit()

    except Exception:
        mysql.connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()