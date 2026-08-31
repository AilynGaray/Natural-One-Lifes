from flask import session, redirect
from functools import wraps


# =========================================================
# USUARIO CON SESIÓN
# =========================================================

def login_requerido(func):

    @wraps(func)
    def decorador(*args, **kwargs):

        if "idUsu" not in session:

            return redirect("/")

        return func(*args, **kwargs)

    return decorador


# =========================================================
# SOLO ADMINISTRADOR
# =========================================================

def administrador_requerido(func):

    @wraps(func)
    def decorador(*args, **kwargs):

       
        if "idUsu" not in session:

            return redirect("/")

        if session.get("rol") != "Administrador":

            rol = session.get("rol")


            if rol == "Profesional":

                return redirect("/profesional")


            if rol == "Cliente":

                return redirect("/inicio")


            session.clear()

            return redirect("/")


        return func(*args, **kwargs)

    return decorador

def profesional_requerido(func):

    @wraps(func)
    def decorador(*args, **kwargs):
        if "idUsu" not in session:

            return redirect("/")
        if session.get("rol") != "Profesional":

            rol = session.get("rol")


            if rol == "Administrador":

                return redirect("/dashboard")


            if rol == "Cliente":

                return redirect("/inicio")


            session.clear()

            return redirect("/")


        return func(*args, **kwargs)

    return decorador


# =========================================================
# SOLO CLIENTE
# =========================================================

def cliente_requerido(func):

    @wraps(func)
    def decorador(*args, **kwargs):

        # -----------------------------------------------
        # NO HA INICIADO SESIÓN
        # -----------------------------------------------

        if "idUsu" not in session:

            return redirect("/")


        # -----------------------------------------------
        # NO ES CLIENTE
        # -----------------------------------------------

        if session.get("rol") != "Cliente":

            rol = session.get("rol")


            if rol == "Administrador":

                return redirect("/dashboard")


            if rol == "Profesional":

                return redirect("/gestion-citas")


            session.clear()

            return redirect("/")


        return func(*args, **kwargs)

    return decorador