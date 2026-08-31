from app import app
from flask import session, request, redirect, url_for
from config import mysql
from datetime import datetime


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

        print("ERROR ACTUALIZANDO CITAS VENCIDAS:", e)

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


@app.route("/guardar-cita", methods=["POST"])
def guardar_cita():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    actualizar_citas_vencidas()


    id_profesional = request.form.get("idProfesionalCit")
    fecha = request.form.get("fechaCit")
    hora = request.form.get("horaCit")
    motivo = request.form.get("motivoCit")

    if not id_profesional or not fecha or not hora:

        return """
            <script>
                alert("Debe seleccionar profesional, fecha y hora.");
                window.history.back();
            </script>
        """, 400


    cursor = None

    try:

        fecha_hora_cita = datetime.strptime(
            f"{fecha} {hora}",
            "%Y-%m-%d %H:%M"
        )

        ahora = datetime.now()


        if fecha_hora_cita <= ahora:

            return """
                <script>
                    alert("La fecha u hora seleccionada ya pasó. Seleccione otro horario.");
                    window.history.back();
                </script>
            """, 400


        cursor = mysql.connection.cursor()


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
            AND horaFinDisp >= ADDTIME(%s, '01:00:00')
            LIMIT 1
        """, (
            id_profesional,
            fecha,
            hora,
            hora
        ))

        disponibilidad = cursor.fetchone()


        if not disponibilidad:

            cursor.close()

            return """
                <script>
                    alert("Ese horario ya no está disponible.");
                    window.history.back();
                </script>
            """, 400


        cursor.execute("""
            SELECT idCit
            FROM citas
            WHERE idProfesionalCit = %s
            AND fechaCit = %s
            AND horaCit = %s
            AND estadoCit IN ('Pendiente', 'Confirmada')
            LIMIT 1
        """, (
            id_profesional,
            fecha,
            hora
        ))

        cita_existente = cursor.fetchone()


        if cita_existente:

            cursor.close()

            return """
                <script>
                    alert("Ese horario ya fue ocupado por otra persona.");
                    window.history.back();
                </script>
            """, 400

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


        mysql.connection.commit()

        cursor.close()


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


        try:

            if cursor:
                cursor.close()

        except:

            pass


        return """
            <script>
                alert("Ocurrió un error al guardar la cita.");
                window.history.back();
            </script>
        """, 500
