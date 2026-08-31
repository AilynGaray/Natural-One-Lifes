
import os
import smtplib

from email.message import EmailMessage


# ==========================================================
# CONFIGURACIÓN SMTP
# ==========================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


# ==========================================================
# ENVIAR CORREO DE RECUPERACIÓN
# ==========================================================

def enviar_correo_recuperacion(
    correo_destino,
    nombre_usuario,
    enlace
):

    # ------------------------------------------------------
    # COMPROBAR CREDENCIALES
    # ------------------------------------------------------

    if not SMTP_EMAIL:
        raise Exception(
            "La variable SMTP_EMAIL no está configurada."
        )

    if not SMTP_PASSWORD:
        raise Exception(
            "La variable SMTP_PASSWORD no está configurada."
        )

    # ------------------------------------------------------
    # CREAR MENSAJE
    # ------------------------------------------------------

    mensaje = EmailMessage()

    mensaje["Subject"] = (
        "Recuperación de contraseña - Natural One Life"
    )

    mensaje["From"] = SMTP_EMAIL
    mensaje["To"] = correo_destino

    mensaje.set_content(
        f"""Hola {nombre_usuario},

Recibimos una solicitud para restablecer la contraseña
de tu cuenta de Natural One Life.

Para crear una nueva contraseña, haz clic en el siguiente enlace:

{enlace}

Este enlace es válido durante 30 minutos y solamente
puede utilizarse una vez.

Si tú no solicitaste recuperar tu contraseña,
puedes ignorar este correo.

Saludos,

Natural One Life
"""
    )

    # ------------------------------------------------------
    # CONECTAR CON GMAIL
    # ------------------------------------------------------

    try:

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        ) as servidor:

            servidor.ehlo()

            servidor.starttls()

            servidor.ehlo()

            servidor.login(
                SMTP_EMAIL,
                SMTP_PASSWORD
            )

            servidor.send_message(
                mensaje
            )

            print(
                "CORREO DE RECUPERACIÓN ENVIADO A:",
                correo_destino
            )

    except smtplib.SMTPAuthenticationError as e:

        print(
            "ERROR AUTENTICACIÓN SMTP:",
            e
        )

        raise Exception(
            "No fue posible autenticar la cuenta de Gmail. "
            "Verifica SMTP_EMAIL y SMTP_PASSWORD."
        )

    except smtplib.SMTPException as e:

        print(
            "ERROR SMTP:",
            e
        )

        raise Exception(
            "No fue posible enviar el correo."
        )

    except Exception as e:

        print(
            "ERROR CORREO:",
            e
        )

        raise
