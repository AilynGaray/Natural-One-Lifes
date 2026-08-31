document.addEventListener("DOMContentLoaded", () => {

    const formulario =
        document.getElementById("loginForm");


    const boton =
        formulario.querySelector("button");


    const usuario =
        document.getElementById("correo");


    const password =
        document.getElementById("password");


    const mensaje =
        document.getElementById("mensajeLogin");


    // =====================================================
    // MOSTRAR MENSAJE
    // =====================================================

    function mostrarMensaje(
        texto,
        tipo = "error"
    ) {

        mensaje.textContent = texto;

        mensaje.style.display = "block";


        if (tipo === "exito") {

            mensaje.style.background = "#eef9f0";

            mensaje.style.border =
                "1px solid #b7dfbd";

            mensaje.style.color = "#246b2c";

        } else {

            mensaje.style.background = "#fff1f1";

            mensaje.style.border =
                "1px solid #f2b8b8";

            mensaje.style.color = "#b42318";

        }

    }


    // =====================================================
    // OCULTAR MENSAJE
    // =====================================================

    function ocultarMensaje() {

        mensaje.textContent = "";

        mensaje.style.display = "none";

    }


    // =====================================================
    // ERROR CAMPO
    // =====================================================

    function marcarError(campo) {

        campo.style.border = "2px solid #d93025";

        campo.style.boxShadow =
            "0 0 8px rgba(217,48,37,.15)";

    }


    // =====================================================
    // LIMPIAR ERRORES
    // =====================================================

    function limpiarErrores() {

        usuario.style.border = "";

        usuario.style.boxShadow = "";

        password.style.border = "";

        password.style.boxShadow = "";

    }


    // =====================================================
    // LOGIN
    // =====================================================

    formulario.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            ocultarMensaje();

            limpiarErrores();


            const usuarioValor =
                usuario.value.trim();


            const passwordValor =
                password.value;


            // =================================================
            // VALIDAR USUARIO
            // =================================================

            if (!usuarioValor) {

                mostrarMensaje(
                    "Ingresa tu correo o nombre de usuario."
                );

                marcarError(usuario);

                usuario.focus();

                return;

            }


            // =================================================
            // VALIDAR CONTRASEÑA
            // =================================================

            if (!passwordValor) {

                mostrarMensaje(
                    "Ingresa tu contraseña."
                );

                marcarError(password);

                password.focus();

                return;

            }


            // =================================================
            // BOTÓN
            // =================================================

            boton.disabled = true;

            boton.textContent = "Verificando...";


            try {

                const respuesta = await fetch(
                    "/validar_login",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            usuario: usuarioValor,

                            password: passwordValor

                        })
                    }
                );


                const data =
                    await respuesta.json();


                // =================================================
                // LOGIN CORRECTO
                // =================================================

                if (data.estado === "ok") {

                    mostrarMensaje(
                        "Inicio de sesión correcto. Redirigiendo...",
                        "exito"
                    );


                    setTimeout(() => {

                        window.location.href =
                            data.redirect || "/";

                    }, 700);


                    return;

                }


                // =================================================
                // LOGIN INCORRECTO
                // =================================================

                mostrarMensaje(
                    data.mensaje ||
                    "Usuario o contraseña incorrectos."
                );


                password.value = "";

                marcarError(password);


            } catch (error) {

                console.error(
                    "ERROR LOGIN:",
                    error
                );


                mostrarMensaje(
                    "No se pudo conectar con el servidor."
                );


            } finally {

                boton.disabled = false;

                boton.textContent =
                    "Iniciar sesión";

            }

        }
    );


    // =====================================================
    // LIMPIAR ERROR AL ESCRIBIR
    // =====================================================

    usuario.addEventListener(
        "input",
        () => {

            usuario.style.border = "";

            usuario.style.boxShadow = "";

        }
    );


    password.addEventListener(
        "input",
        () => {

            password.style.border = "";

            password.style.boxShadow = "";

        }
    );

});