document.addEventListener("DOMContentLoaded", () => {

    const formulario =
        document.getElementById("nuevaPasswordForm");

    const token =
        document.getElementById("token");

    const password =
        document.getElementById("password");

    const confirmar =
        document.getElementById("confirmar");

    const boton =
        document.getElementById("btnCambiar");

    const mensaje =
        document.getElementById("mensaje");


    function mostrarMensaje(texto, tipo) {

        mensaje.textContent = texto;

        mensaje.className =
            "mensaje " + tipo;

    }


    formulario.addEventListener("submit", async (e) => {

        e.preventDefault();


        const nuevaPassword =
            password.value;

        const confirmarPassword =
            confirmar.value;


        password.classList.remove("input-error");
        confirmar.classList.remove("input-error");


        if (nuevaPassword.length < 8) {

            password.classList.add("input-error");

            mostrarMensaje(
                "La contraseña debe tener mínimo 8 caracteres.",
                "error"
            );

            return;
        }


        if (nuevaPassword !== confirmarPassword) {

            confirmar.classList.add("input-error");

            mostrarMensaje(
                "Las contraseñas no coinciden.",
                "error"
            );

            return;
        }


        boton.disabled = true;

        boton.textContent =
            "Actualizando...";


        try {

            const respuesta = await fetch(
                "/cambiar-password",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        token:
                            token.value,

                        password:
                            nuevaPassword,

                        confirmar:
                            confirmarPassword

                    })
                }
            );


            const data =
                await respuesta.json();


            if (data.estado === "ok") {

                mostrarMensaje(
                    data.mensaje,
                    "exito"
                );


                formulario.reset();


                setTimeout(() => {

                    window.location.href = "/";

                }, 2000);


            } else {

                mostrarMensaje(
                    data.mensaje ||
                    "No fue posible cambiar la contraseña.",
                    "error"
                );

            }


        } catch (error) {

            console.error(error);

            mostrarMensaje(
                "No fue posible conectar con el servidor.",
                "error"
            );

        } finally {

            boton.disabled = false;

            boton.textContent =
                "Cambiar contraseña";

        }

    });

});