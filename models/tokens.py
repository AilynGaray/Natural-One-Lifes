from config import mysql


def invalidar_tokens_usuario(id_usuario):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            UPDATE tokens_recuperacion
            SET usadoToken = 1
            WHERE idUsuToken = %s
              AND usadoToken = 0
        """, (id_usuario,))

    finally:
        if cursor:
            cursor.close()


def crear_token(id_usuario, token, expiracion):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            INSERT INTO tokens_recuperacion (
                idUsuToken,
                tokenToken,
                expiracionToken,
                usadoToken
            )
            VALUES (
                %s,
                %s,
                %s,
                0
            )
        """, (
            id_usuario,
            token,
            expiracion
        ))

    finally:
        if cursor:
            cursor.close()


def buscar_token(token):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                idToken,
                idUsuToken,
                tokenToken,
                expiracionToken,
                usadoToken
            FROM tokens_recuperacion
            WHERE tokenToken = %s
            LIMIT 1
        """, (token,))

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()


def marcar_token_usado(id_token):
    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            UPDATE tokens_recuperacion
            SET usadoToken = 1
            WHERE idToken = %s
        """, (id_token,))

    finally:
        if cursor:
            cursor.close()