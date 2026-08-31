from datetime import datetime, time, timedelta

from app import app
from flask import render_template, request, session, redirect, url_for
from config import mysql
from routes.permiso import profesional_requerido

def cancelar_citas_vencidas(cursor, id_profesional=None):

    try:

        if id_profesional:

            cursor.execute("""
                UPDATE citas
                SET
                    estadoCit = 'Cancelada',
                    actualizadoPorCit = NULL
                WHERE idProfesionalCit = %s
                  AND estadoCit IN ('Pendiente', 'Confirmada')
                  AND TIMESTAMP(fechaCit, horaCit) <= NOW()
            """, (id_profesional,))

        else:

            cursor.execute("""
                UPDATE citas
                SET
                    estadoCit = 'Cancelada',
                    actualizadoPorCit = NULL
                WHERE estadoCit IN ('Pendiente', 'Confirmada')
                  AND TIMESTAMP(fechaCit, horaCit) <= NOW()
            """)

        cantidad = cursor.rowcount

        if cantidad > 0:
            print("========================================")
            print("CITAS VENCIDAS CANCELADAS:", cantidad)
            print("========================================")

        return cantidad

    except Exception as e:

        print("ERROR CANCELANDO CITAS VENCIDAS:", e)

        return 0


@app.route("/profesional")
@profesional_requerido
def profesional():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:


        cursor.execute("""
            SELECT
                idProfe,
                nombreProfe,
                especialidadProfe,
                telefonoProfe,
                correoProfe
            FROM profesionales
            WHERE idUsuarioPro = %s
              AND activoProfe = 1
            LIMIT 1
        """, (id_usuario,))

        profesional = cursor.fetchone()

        print("ID USUARIO DASHBOARD:", id_usuario)
        print("PROFESIONAL DASHBOARD:", profesional)

        if not profesional:

            session.clear()

            return redirect(url_for("login"))

        id_profesional = profesional["idProfe"]

      

        cancelar_citas_vencidas(
            cursor,
            id_profesional
        )

        mysql.connection.commit()

        # ====================================================
        # TOTAL DE CITAS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM citas
            WHERE idProfesionalCit = %s
        """, (id_profesional,))

        total_citas = cursor.fetchone()["total"]

        # ====================================================
        # CITAS PENDIENTES
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM citas
            WHERE idProfesionalCit = %s
              AND estadoCit = 'Pendiente'
        """, (id_profesional,))

        citas_pendientes = cursor.fetchone()["total"]

        # ====================================================
        # CITAS CONFIRMADAS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM citas
            WHERE idProfesionalCit = %s
              AND estadoCit = 'Confirmada'
        """, (id_profesional,))

        citas_confirmadas = cursor.fetchone()["total"]

        # ====================================================
        # CITAS COMPLETADAS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM citas
            WHERE idProfesionalCit = %s
              AND estadoCit = 'Completada'
        """, (id_profesional,))

        citas_completadas = cursor.fetchone()["total"]

        return render_template(
            "profesional/dashboard.html",
            profesional=profesional,
            total_citas=total_citas,
            citas_pendientes=citas_pendientes,
            citas_confirmadas=citas_confirmadas,
            citas_completadas=citas_completadas
        )

    finally:

        cursor.close()


@app.route("/citas")
@profesional_requerido
def profesional_citas():

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:

        

        cursor.execute("""
            SELECT
                idProfe,
                nombreProfe,
                especialidadProfe,
                telefonoProfe,
                correoProfe
            FROM profesionales
            WHERE idUsuarioPro = %s
              AND activoProfe = 1
            LIMIT 1
        """, (id_usuario,))

        profesional = cursor.fetchone()

        print("ID USUARIO SESIÓN:", id_usuario)
        print("PROFESIONAL ENCONTRADO:", profesional)

        if not profesional:

            session.clear()

            return redirect(url_for("login"))

        id_profesional = profesional["idProfe"]

        cancelar_citas_vencidas(
            cursor,
            id_profesional
        )

        mysql.connection.commit()

        # ----------------------------------------------------
        # CONSULTAR CITAS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                c.idCit,
                c.fechaCit,
                c.horaCit,
                c.estadoCit,
                c.motivoCit,
                c.notificadoCit,
                c.actualizadoPorCit,

                u.idUsu,
                u.nombreUsu,
                u.apellidoUsu,
                u.telefonoUsu,
                u.emailUsu

            FROM citas c

            INNER JOIN usuarios u
                ON c.idUsuarioCit = u.idUsu

            WHERE c.idProfesionalCit = %s

            ORDER BY
                c.fechaCit ASC,
                c.horaCit ASC
        """, (id_profesional,))

        citas = cursor.fetchall()

        return render_template(
            "profesional/citas.html",
            profesional=profesional,
            citas=citas
        )

    finally:

        cursor.close()


@app.route("/profesional/confirmar-cita/<int:id>")
@profesional_requerido
def profesional_confirmar_cita(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:

      

        cursor.execute("""
            SELECT idProfe
            FROM profesionales
            WHERE idUsuarioPro = %s
              AND activoProfe = 1
            LIMIT 1
        """, (id_usuario,))

        profesional = cursor.fetchone()

        if not profesional:

            session.clear()

            return redirect(url_for("login"))

        id_profesional = profesional["idProfe"]


        cancelar_citas_vencidas(
            cursor,
            id_profesional
        )

        mysql.connection.commit()

        # ----------------------------------------------------
        # BUSCAR LA CITA
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                idCit,
                fechaCit,
                horaCit,
                estadoCit
            FROM citas
            WHERE idCit = %s
              AND idProfesionalCit = %s
            LIMIT 1
        """, (
            id,
            id_profesional
        ))

        cita = cursor.fetchone()

        if not cita:

            return """
            <script>
                alert("La cita no existe o no pertenece a este profesional.");
                window.location.href = "/citas";
            </script>
            """

        # ----------------------------------------------------
        # COMPROBAR ESTADO
        # ----------------------------------------------------

        if cita["estadoCit"] != "Pendiente":

            return """
            <script>
                alert("Esta cita ya no está disponible para confirmar.");
                window.location.href = "/citas";
            </script>
            """

        # ----------------------------------------------------
        # COMPROBAR FECHA Y HORA
        # ----------------------------------------------------

        fecha_cita = cita["fechaCit"]
        hora_cita = cita["horaCit"]

        if isinstance(fecha_cita, str):

            fecha_cita = datetime.strptime(
                fecha_cita,
                "%Y-%m-%d"
            ).date()

        if isinstance(hora_cita, str):
            hora_cita = datetime.strptime(
            hora_cita,
            "%H:%M:%S"
            ).time()
        elif isinstance(hora_cita, timedelta):
            segundos = int(hora_cita.total_seconds())
            hora_cita = time(
                hour=segundos // 3600,
                minute=(segundos % 3600) // 60,
                second=segundos % 60
                )

        fecha_hora_cita = datetime.combine(
            fecha_cita,
            hora_cita
        )

        if fecha_hora_cita <= datetime.now():

            # ------------------------------------------------
            # CANCELAR POR VENCIMIENTO
            # ------------------------------------------------

            cursor.execute("""
                UPDATE citas
                SET
                    estadoCit = 'Cancelada',
                    actualizadoPorCit = NULL
                WHERE idCit = %s
                  AND idProfesionalCit = %s
                  AND estadoCit = 'Pendiente'
            """, (
                id,
                id_profesional
            ))

            mysql.connection.commit()

            return """
            <script>
                alert("No puedes confirmar esta cita porque la fecha y hora ya pasaron.");
                window.location.href = "/citas";
            </script>
            """

        # ----------------------------------------------------
        # CONFIRMAR CITA
        # ----------------------------------------------------

        cursor.execute("""
            UPDATE citas
            SET
                estadoCit = 'Confirmada',
                actualizadoPorCit = %s
            WHERE idCit = %s
              AND idProfesionalCit = %s
              AND estadoCit = 'Pendiente'
              AND TIMESTAMP(fechaCit, horaCit) > NOW()
        """, (
            id_usuario,
            id,
            id_profesional
        ))

        mysql.connection.commit()

        # ----------------------------------------------------
        # COMPROBAR SI REALMENTE SE ACTUALIZÓ
        # ----------------------------------------------------

        if cursor.rowcount == 0:

            return """
            <script>
                alert("La cita ya no puede ser confirmada.");
                window.location.href = "/citas";
            </script>
            """

        return redirect(url_for("profesional_citas"))

    except Exception as e:

        print("ERROR CONFIRMANDO CITA:", e)

        try:
            mysql.connection.rollback()
        except Exception:
            pass

        return "No fue posible confirmar la cita.", 500

    finally:

        cursor.close()


@app.route("/profesional/cancelar-cita/<int:id>")
@profesional_requerido
def profesional_cancelar_cita(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT idProfe
            FROM profesionales
            WHERE idUsuarioPro = %s
              AND activoProfe = 1
            LIMIT 1
        """, (id_usuario,))

        profesional = cursor.fetchone()

        if not profesional:

            session.clear()

            return redirect(url_for("login"))

        id_profesional = profesional["idProfe"]


        cursor.execute("""
            UPDATE citas
            SET
                estadoCit = 'Cancelada',
                actualizadoPorCit = %s
            WHERE idCit = %s
              AND idProfesionalCit = %s
              AND estadoCit = 'Pendiente'
              AND TIMESTAMP(fechaCit, horaCit) > NOW()
        """, (
            id_usuario,
            id,
            id_profesional
        ))

        mysql.connection.commit()

        return redirect(url_for("profesional_citas"))

    finally:

        cursor.close()


@app.route("/profesional/completar-cita/<int:id>")
@profesional_requerido
def profesional_completar_cita(id):

    id_usuario = session.get("idUsu")

    if not id_usuario:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT idProfe
            FROM profesionales
            WHERE idUsuarioPro = %s
              AND activoProfe = 1
            LIMIT 1
        """, (id_usuario,))

        profesional = cursor.fetchone()

        if not profesional:

            session.clear()

            return redirect(url_for("login"))

        id_profesional = profesional["idProfe"]


        cancelar_citas_vencidas(
            cursor,
            id_profesional
        )

        mysql.connection.commit()

       
        cursor.execute("""
            UPDATE citas
            SET
                estadoCit = 'Completada',
                actualizadoPorCit = %s
            WHERE idCit = %s
              AND idProfesionalCit = %s
              AND estadoCit = 'Confirmada'
              AND TIMESTAMP(fechaCit, horaCit) > NOW()
        """, (
            id_usuario,
            id,
            id_profesional
        ))

        mysql.connection.commit()

        return redirect(url_for("profesional_citas"))

    finally:

        cursor.close()


@app.route("/profesional/disponibilidad", methods=["GET", "POST"])
@profesional_requerido
def profesional_disponibilidad():

    id_usuario = session.get("idUsu")

    if not id_usuario:

        return redirect("/")

    cursor = mysql.connection.cursor()

    try:


        cursor.execute("""
            SELECT
                idProfe,
                nombreProfe,
                especialidadProfe,
                telefonoProfe,
                correoProfe
            FROM profesionales
            WHERE idUsuarioPro = %s
              AND activoProfe = 1
            LIMIT 1
        """, (id_usuario,))

        profesional = cursor.fetchone()

        print("ID USUARIO:", id_usuario)
        print("PROFESIONAL:", profesional)

        if not profesional:

            return redirect("/")

        id_profesional = profesional["idProfe"]

       
        if request.method == "POST":

            fecha = request.form.get(
                "fecha",
                ""
            ).strip()

            hora_inicio = request.form.get(
                "hora_inicio",
                ""
            ).strip()

            hora_fin = request.form.get(
                "hora_fin",
                ""
            ).strip()

            estado = request.form.get(
                "estado",
                "1"
            ).strip()

        

            dia = ""

            if fecha:

                try:

                    fecha_obj = datetime.strptime(
                        fecha,
                        "%Y-%m-%d"
                    ).date()

                    dias_semana = [
                        "Lunes",
                        "Martes",
                        "Miércoles",
                        "Jueves",
                        "Viernes",
                        "Sábado",
                        "Domingo"
                    ]

                    dia = dias_semana[
                        fecha_obj.weekday()
                    ]

                except ValueError:

                    dia = ""

            # ------------------------------------------------
            # VALIDAR CAMPOS
            # ------------------------------------------------

            if not dia or not fecha or not hora_inicio or not hora_fin:

                disponibilidad = obtener_disponibilidad(
                    cursor,
                    id_profesional
                )

                return render_template(
                    "profesional/disponibilidad.html",
                    profesional=profesional,
                    disponibilidad=disponibilidad,
                    error="Todos los campos son obligatorios."
                )

            # ------------------------------------------------
            # VALIDAR FECHA
            # ------------------------------------------------

            fecha_obj = datetime.strptime(
                fecha,
                "%Y-%m-%d"
            ).date()

            if fecha_obj < datetime.now().date():

                disponibilidad = obtener_disponibilidad(
                    cursor,
                    id_profesional
                )

                return render_template(
                    "profesional/disponibilidad.html",
                    profesional=profesional,
                    disponibilidad=disponibilidad,
                    error="No puedes registrar disponibilidad para una fecha pasada."
                )

            # ------------------------------------------------
            # VALIDAR HORARIO
            # ------------------------------------------------

            if hora_inicio >= hora_fin:

                disponibilidad = obtener_disponibilidad(
                    cursor,
                    id_profesional
                )

                return render_template(
                    "profesional/disponibilidad.html",
                    profesional=profesional,
                    disponibilidad=disponibilidad,
                    error="La hora de inicio debe ser menor que la hora de finalización."
                )

            # ------------------------------------------------
            # ESTADO
            # ------------------------------------------------

            estado = 1 if estado == "1" else 0

            # ------------------------------------------------
            # VERIFICAR DUPLICADO
            # ------------------------------------------------

            cursor.execute("""
                SELECT idDisp
                FROM disponibilidad
                WHERE idProfesionalDisp = %s
                  AND fechaDisp = %s
                  AND horaInicioDisp = %s
                  AND horaFinDisp = %s
                LIMIT 1
            """, (
                id_profesional,
                fecha,
                hora_inicio,
                hora_fin
            ))

            existe = cursor.fetchone()

            if existe:

                disponibilidad = obtener_disponibilidad(
                    cursor,
                    id_profesional
                )

                return render_template(
                    "profesional/disponibilidad.html",
                    profesional=profesional,
                    disponibilidad=disponibilidad,
                    error="Ese horario ya está registrado."
                )

            # ------------------------------------------------
            # INSERTAR DISPONIBILIDAD
            # ------------------------------------------------

            cursor.execute("""
                INSERT INTO disponibilidad (
                    idProfesionalDisp,
                    diaDisp,
                    horaInicioDisp,
                    horaFinDisp,
                    estadoDisp,
                    fechaDisp
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                id_profesional,
                dia,
                hora_inicio,
                hora_fin,
                estado,
                fecha
            ))

            mysql.connection.commit()

            print("========================================")
            print("DISPONIBILIDAD GUARDADA")
            print("PROFESIONAL:", id_profesional)
            print("DÍA:", dia)
            print("FECHA:", fecha)
            print("INICIO:", hora_inicio)
            print("FIN:", hora_fin)
            print("ESTADO:", estado)
            print("========================================")

            return redirect(
                "/profesional/disponibilidad"
            )

        # ====================================================
        # CONSULTAR DISPONIBILIDAD
        # ====================================================

        disponibilidad = obtener_disponibilidad(
            cursor,
            id_profesional
        )

        return render_template(
            "profesional/disponibilidad.html",
            profesional=profesional,
            disponibilidad=disponibilidad
        )

    finally:

        cursor.close()



def obtener_disponibilidad(
    cursor,
    id_profesional
):

    cursor.execute("""
        SELECT
            idDisp,
            idProfesionalDisp,
            diaDisp,
            horaInicioDisp,
            horaFinDisp,
            estadoDisp,
            fechaDisp
        FROM disponibilidad
        WHERE idProfesionalDisp = %s
        ORDER BY
            fechaDisp ASC,
            horaInicioDisp ASC
    """, (id_profesional,))

    datos = cursor.fetchall()

    disponibilidad = []

    for dia in datos:

        disponibilidad.append({

            "idDisp": dia["idDisp"],

            "idProfesionalDisp":
                dia["idProfesionalDisp"],

            "diaDisp":
                dia["diaDisp"],

            "horaInicioDisp":
                str(dia["horaInicioDisp"]),

            "horaFinDisp":
                str(dia["horaFinDisp"]),

            "estadoDisp":
                int(dia["estadoDisp"]),

            "fechaDisp":
                str(dia["fechaDisp"])
        })

    return disponibilidad