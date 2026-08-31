document.addEventListener("DOMContentLoaded", () => {

    const formulario = document.getElementById("registroForm");
    const boton = document.getElementById("btnRegistro");

    const nombre = document.getElementById("nombre");
    const apellido = document.getElementById("apellido");
    const email = document.getElementById("email");
    const usuario = document.getElementById("usuario");
    const password = document.getElementById("password");
    const confirmar = document.getElementById("confirmar");
    const terminos = document.getElementById("terminos");

    // El HTML ya tiene este elemento
    const mensaje = document.getElementById("mensaje");


    // =====================================================
    // VERIFICAR ELEMENTOS
    // =====================================================

    if (!formulario) {
        console.error("ERROR: No se encontró el formulario de registro.");
        return;
    }

    if (!boton) {
        console.error("ERROR: No se encontró el botón de registro.");
        return;
    }


    // =====================================================
    // MOSTRAR MENSAJE
    // =====================================================

    function mostrarMensaje(texto, tipo = "error") {

        if (!mensaje) {
            alert(texto);
            return;
        }

        mensaje.textContent = texto;
        mensaje.style.display = "block";

        if (tipo === "exito") {

            mensaje.className = "mensaje exito";

        } else {

            mensaje.className = "mensaje error";

        }
    }


    // =====================================================
    // OCULTAR MENSAJE
    // =====================================================

    function ocultarMensaje() {

        if (!mensaje) {
            return;
        }

        mensaje.textContent = "";
        mensaje.style.display = "none";
        mensaje.className = "mensaje";
    }


    // =====================================================
    // LIMPIAR ERRORES
    // =====================================================

    function limpiarErrores() {

        const campos = [
            nombre,
            apellido,
            email,
            usuario,
            password,
            confirmar
        ];

        campos.forEach(campo => {

            if (campo) {

                campo.classList.remove("input-error");

                campo.style.borderColor = "";
                campo.style.boxShadow = "";
            }

        });
    }


    // =====================================================
    // MARCAR ERROR
    // =====================================================

    function marcarError(campo) {

        if (!campo) {
            return;
        }

        campo.classList.add("input-error");

        campo.style.borderColor = "#d93025";

        campo.style.boxShadow =
            "0 0 0 3px rgba(217,48,37,.10)";

        campo.focus();
    }


    // =====================================================
    // VALIDAR EMAIL
    // =====================================================

    function emailValido(valor) {

        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);

    }


    // =====================================================
    // SUBMIT
    // =====================================================

    formulario.addEventListener("submit", async function (event) {

        event.preventDefault();

        ocultarMensaje();
        limpiarErrores();


        // =================================================
        // OBTENER VALORES
        // =================================================

        const nombreValor =
            nombre.value.trim();

        const apellidoValor =
            apellido.value.trim();

        const emailValor =
            email.value.trim().toLowerCase();

        const usuarioValor =
            usuario.value.trim();

        const passwordValor =
            password.value;

        const confirmarValor =
            confirmar.value;

        const acepta =
            terminos.checked;


        // =================================================
        // VALIDAR NOMBRE
        // =================================================

        if (nombreValor.length < 2) {

            mostrarMensaje(
                "Ingresa un nombre válido."
            );

            marcarError(nombre);

            return;
        }


        // =================================================
        // VALIDAR APELLIDO
        // =================================================

        if (apellidoValor.length < 2) {

            mostrarMensaje(
                "Ingresa tus apellidos."
            );

            marcarError(apellido);

            return;
        }


        // =================================================
        // VALIDAR EMAIL
        // =================================================

        if (!emailValido(emailValor)) {

            mostrarMensaje(
                "Ingresa un correo electrónico válido."
            );

            marcarError(email);

            return;
        }


        // =================================================
        // VALIDAR USUARIO
        // =================================================

        if (usuarioValor.length < 4) {

            mostrarMensaje(
                "El nombre de usuario debe tener mínimo 4 caracteres."
            );

            marcarError(usuario);

            return;
        }


        // =================================================
        // VALIDAR CONTRASEÑA
        // =================================================

        if (passwordValor.length < 8) {

            mostrarMensaje(
                "La contraseña debe tener mínimo 8 caracteres."
            );

            marcarError(password);

            return;
        }


        // =================================================
        // CONFIRMAR CONTRASEÑA
        // =================================================

        if (passwordValor !== confirmarValor) {

            mostrarMensaje(
                "Las contraseñas no coinciden."
            );

            marcarError(confirmar);

            return;
        }


        // =================================================
        // TÉRMINOS
        // =================================================

        if (!acepta) {

            mostrarMensaje(
                "Debes aceptar los términos y condiciones."
            );

            terminos.focus();

            return;
        }


        // =================================================
        // REGISTRO PÚBLICO
        // =================================================
        // No necesitamos buscar un elemento #rol porque
        // tu HTML no lo tiene.
        //
        // Todo registro público será CLIENTE.
        // =================================================

        const rol = "cliente";


        // =================================================
        // DESACTIVAR BOTÓN
        // =================================================

        boton.disabled = true;
        boton.textContent = "Creando cuenta...";


        try {

            // =================================================
            // ENVIAR DATOS A FLASK
            // =================================================

            const respuesta = await fetch("/registro", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({

                    nombre: nombreValor,

                    apellido: apellidoValor,

                    email: emailValor,

                    usuario: usuarioValor,

                    password: passwordValor,

                    confirmar: confirmarValor,

                    rol: rol

                })

            });


            // =================================================
            // LEER RESPUESTA
            // =================================================

            let data;

            try {

                data = await respuesta.json();

            } catch (error) {

                console.error(
                    "RESPUESTA NO JSON:",
                    error
                );

                mostrarMensaje(
                    "El servidor no devolvió una respuesta válida."
                );

                return;
            }


            console.log(
                "RESPUESTA REGISTRO:",
                respuesta.status,
                data
            );


            // =================================================
            // REGISTRO EXITOSO
            // =================================================

            if (
                respuesta.ok &&
                (
                    data.estado === "ok" ||
                    data.success === true
                )
            ) {

                mostrarMensaje(

                    data.mensaje ||
                    "Cuenta creada correctamente.",

                    "exito"

                );


                formulario.reset();


                // =================================================
                // REDIRIGIR AL LOGIN
                // =================================================

                setTimeout(() => {

                    window.location.href = "/";

                }, 1500);


                return;
            }


            // =================================================
            // ERROR DEL SERVIDOR
            // =================================================

            mostrarMensaje(

                data.mensaje ||
                data.error ||
                "No fue posible crear la cuenta."

            );


            // =================================================
            // MARCAR CAMPO CON ERROR
            // =================================================

            if (data.campo === "email") {

                marcarError(email);

            }

            if (data.campo === "usuario") {

                marcarError(usuario);

            }


        } catch (error) {

            console.error(
                "ERROR REGISTRO:",
                error
            );


            mostrarMensaje(
                "No se pudo conectar con el servidor. Inténtalo nuevamente."
            );


        } finally {

            boton.disabled = false;
            boton.textContent = "Crear cuenta";

        }

    });

});