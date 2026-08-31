document.addEventListener("DOMContentLoaded", function () {

    const formulario = document.getElementById("recuperarForm");
    const emailInput = document.getElementById("email");
    const boton = document.getElementById("btnRecuperar");
    const mensaje = document.getElementById("mensaje");


    // ======================================================
    // MOSTRAR MENSAJE
    // ======================================================

    function mostrarMensaje(texto, tipo) {

        mensaje.textContent = texto;

        mensaje.className = "mensaje " + tipo;

    }


    // ======================================================
    // OCULTAR MENSAJE
    // ======================================================

    function ocultarMensaje() {

        mensaje.textContent = "";

        mensaje.className = "mensaje";

    }


    // ======================================================
    // ENVIAR FORMULARIO
    // ======================================================

    formulario.addEventListener("submit", async function (e) {

        e.preventDefault();

        ocultarMensaje();

        const email = emailInput.value.trim().toLowerCase();


        // --------------------------------------------------
        // VALIDAR CORREO
        // --------------------------------------------------

        if (!email) {

            mostrarMensaje(
                "Ingresa tu correo electrónico.",
                "error"
            );

            emailInput.focus();

            return;
        }


        // --------------------------------------------------
        // VALIDACIÓN BÁSICA
        // --------------------------------------------------

        const formatoEmail =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!formatoEmail.test(email)) {

            mostrarMensaje(
                "Ingresa un correo electrónico válido.",
                "error"
            );

            emailInput.focus();

            return;
        }


        // --------------------------------------------------
        // DESACTIVAR BOTÓN
        // --------------------------------------------------

        boton.disabled = true;

        boton.textContent = "Enviando...";


        try {

            // ------------------------------------------------
            // ENVIAR AL SERVIDOR
            // ------------------------------------------------

            const respuesta = await fetch(
                "/recuperar",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email
                    })
                }
            );


            // ------------------------------------------------
            // LEER RESPUESTA
            // ------------------------------------------------

            const data = await respuesta.json();


            // ------------------------------------------------
            // RESPUESTA CORRECTA
            // ------------------------------------------------

            if (respuesta.ok && data.estado === "ok") {

                mostrarMensaje(
                    data.mensaje,
                    "exito"
                );

                boton.textContent = "Correo enviado";

                emailInput.disabled = true;

                return;
            }


            // ------------------------------------------------
            // ERROR DEL SERVIDOR
            // ------------------------------------------------

            mostrarMensaje(
                data.mensaje ||
                "No fue posible procesar la solicitud.",
                "error"
            );

            boton.disabled = false;

            boton.textContent = "Enviar enlace";


        } catch (error) {

            console.error(
                "ERROR RECUPERACIÓN:",
                error
            );

            mostrarMensaje(
                "No fue posible conectar con el servidor.",
                "error"
            );

            boton.disabled = false;

            boton.textContent = "Enviar enlace";

        }

    });

});
