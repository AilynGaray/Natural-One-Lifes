from app import app
from flask import session, request, redirect, url_for, flash
from config import mysql
from datetime import datetime

from routes.permiso import login_requerido


# ==========================================================
# ACTUALIZAR CITAS VENCIDAS
# ==========================================================

def actualizar_citas_vencidas():

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        ahora = datetime.now()

        cursor.execute("""
            UPDATE citas
            SET estadoCit = 'Cancelada'

            WHERE estadoCit IN ('Pendiente', 'Confirmada')

            AND TIMESTAMP(fechaCit, horaCit) <= %s
        """, (ahora,))

        mysql.connection.commit()

        print("Citas vencidas actualizadas correctamente.")

    except Exception as e:

        print(
            "ERROR ACTUALIZANDO CITAS VENCIDAS:",
            e
        )

        try:
            mysql.connection.rollback()
        except:
            pass

    finally:

        try:
            if cursor:
                cursor.close()
        except:
            pass


# ==========================================================
# GUARDAR CITA
# ==========================================================

@app.route("/guardar-cita", methods=["POST"])
def guardar_cita():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    # Actualizar citas vencidas antes de crear una nueva
    actualizar_citas_vencidas()

    # ------------------------------------------------------
    # DATOS DEL FORMULARIO
    # ------------------------------------------------------

    id_profesional = request.form.get(
        "idProfesionalCit"
    )

    fecha = request.form.get(
        "fechaCit"
    )

    hora = request.form.get(
        "horaCit"
    )

    motivo = request.form.get(
        "motivoCit",
        ""
    ).strip()

    # ------------------------------------------------------
    # VALIDAR DATOS
    # ------------------------------------------------------

    if not id_profesional or not fecha or not hora:

        return """
            <script>
                alert("Debe seleccionar profesional, fecha y hora.");
                window.history.back();
            </script>
        """, 400

    cursor = None

    try:

        # --------------------------------------------------
        # CONVERTIR FECHA Y HORA
        # --------------------------------------------------

        fecha_hora_cita = datetime.strptime(
            f"{fecha} {hora}",
            "%Y-%m-%d %H:%M"
        )

        ahora = datetime.now()

        # --------------------------------------------------
        # COMPROBAR QUE NO SEA UNA FECHA PASADA
        # --------------------------------------------------

        if fecha_hora_cita <= ahora:

            return """
                <script>
                    alert("La fecha u hora seleccionada ya pasó. Seleccione otro horario.");
                    window.history.back();
                </script>
            """, 400

        cursor = mysql.connection.cursor()

        # --------------------------------------------------
        # COMPROBAR DISPONIBILIDAD DEL PROFESIONAL
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idDisp,
                horaInicioDisp,
                horaFinDisp

            FROM disponibilidad

            WHERE idProfesionalDisp = %s

            AND fechaDisp = %s

            AND estadoDisp = 1

            AND horaInicioDisp <= %s

            AND horaFinDisp >= ADDTIME(
                %s,
                '01:00:00'
            )

            LIMIT 1
        """, (
            id_profesional,
            fecha,
            hora,
            hora
        ))

        disponibilidad = cursor.fetchone()

        if not disponibilidad:

            return """
                <script>
                    alert("Ese horario ya no está disponible.");
                    window.history.back();
                </script>
            """, 400

        # --------------------------------------------------
        # COMPROBAR SI YA EXISTE UNA CITA
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idCit

            FROM citas

            WHERE idProfesionalCit = %s

            AND fechaCit = %s

            AND horaCit = %s

            AND estadoCit IN (
                'Pendiente',
                'Confirmada'
            )

            LIMIT 1
        """, (
            id_profesional,
            fecha,
            hora
        ))

        cita_existente = cursor.fetchone()

        if cita_existente:

            return """
                <script>
                    alert("Ese horario ya fue ocupado por otra persona.");
                    window.history.back();
                </script>
            """, 400

        # --------------------------------------------------
        # CREAR CITA
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO citas (
                idUsuarioCit,
                idProfesionalCit,
                fechaCit,
                horaCit,
                estadoCit,
                motivoCit
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                'Pendiente',
                %s
            )
        """, (
            id_usuario,
            id_profesional,
            fecha,
            hora,
            motivo
        ))

        # --------------------------------------------------
        # ID DE LA CITA
        # --------------------------------------------------

        id_cita = cursor.lastrowid

        # --------------------------------------------------
        # NOTIFICACIÓN DE CITA CREADA
        # --------------------------------------------------

        mensaje = (
            f"Tu cita #{id_cita} "
            f"ha sido registrada correctamente y se encuentra "
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
                'cita',
                %s,
                NOW(),
                0,
                %s
            )
        """, (
            id_usuario,
            mensaje,
            id_cita
        ))

        # --------------------------------------------------
        # GUARDAR CAMBIOS
        # --------------------------------------------------

        mysql.connection.commit()

        return redirect(
            url_for("gestion_citas")
        )

    except Exception as e:

        print(
            "ERROR GUARDANDO CITA:",
            e
        )

        try:
            mysql.connection.rollback()
        except:
            pass

        return """
            <script>
                alert("Ocurrió un error al guardar la cita.");
                window.history.back();
            </script>
        """, 500

    finally:

        try:
            if cursor:
                cursor.close()
        except:
            pass


# ==========================================================
# ACTUALIZAR ESTADO DE CITA
# ==========================================================

@app.route(
    "/actualizar-cita/<int:id_cita>",
    methods=["POST"])
@login_requerido
def actualizar_cita(id_cita):

    estado = request.form.get(
        "estado",
        ""
    ).strip()

    # ------------------------------------------------------
    # ESTADOS PERMITIDOS
    # ------------------------------------------------------

    estados_permitidos = [
        "Pendiente",
        "Confirmada",
        "Cancelada",
        "Completada"
    ]

    if estado not in estados_permitidos:

        flash(
            "El estado seleccionado no es válido.",
            "error"
        )

        return redirect(
            url_for("gestion_citas")
        )

    cursor = mysql.connection.cursor()

    try:

        # --------------------------------------------------
        # OBTENER CITA
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                idCit,
                idUsuarioCit,
                estadoCit

            FROM citas

            WHERE idCit = %s

            LIMIT 1
        """, (
            id_cita,
        ))

        cita = cursor.fetchone()

        if not cita:

            flash(
                "La cita no existe.",
                "error"
            )

            return redirect(
                url_for("gestion_citas")
            )

        # --------------------------------------------------
        # GUARDAR ESTADO ANTERIOR
        # --------------------------------------------------

        estado_anterior = cita["estadoCit"]

        # --------------------------------------------------
        # SI EL ESTADO ES EL MISMO
        # --------------------------------------------------

        if estado_anterior == estado:

            flash(
                "La cita ya tiene ese estado.",
                "error"
            )

            return redirect(
                url_for("gestion_citas")
            )

        # --------------------------------------------------
        # ACTUALIZAR ESTADO
        # --------------------------------------------------

        cursor.execute("""
            UPDATE citas

            SET estadoCit = %s

            WHERE idCit = %s
        """, (
            estado,
            id_cita
        ))

        # --------------------------------------------------
        # CREAR NOTIFICACIÓN
        # --------------------------------------------------

        mensaje = (
            f"Tu cita #{id_cita} "
            f"ahora se encuentra en estado: "
            f"{estado}."
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
                'cita',
                %s,
                NOW(),
                0,
                %s
            )
        """, (
            cita["idUsuarioCit"],
            mensaje,
            id_cita
        ))

        # --------------------------------------------------
        # GUARDAR
        # --------------------------------------------------

        mysql.connection.commit()

        flash(
            "Estado de la cita actualizado correctamente.",
            "success"
        )

    except Exception as e:

        mysql.connection.rollback()

        print(
            "ERROR ACTUALIZANDO CITA:",
            e
        )

        flash(
            "No se pudo actualizar la cita.",
            "error"
        )

    finally:

        cursor.close()

    return redirect(
        url_for("gestion_citas")
    )