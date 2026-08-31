document.addEventListener(
    "DOMContentLoaded",
    () => {


    const formulario =
        document.getElementById(
            "profesionalForm"
        );


    const boton =
        document.getElementById(
            "btnCrear"
        );


    const mensaje =
        document.getElementById(
            "mensaje"
        );


    function mostrarMensaje(
        texto,
        tipo = "error"
    ){

        mensaje.textContent = texto;

        mensaje.style.display = "block";


        if(tipo === "exito"){

            mensaje.style.background =
                "#eef9f0";

            mensaje.style.border =
                "1px solid #b7dfbd";

            mensaje.style.color =
                "#246b2c";

        }else{

            mensaje.style.background =
                "#fff1f1";

            mensaje.style.border =
                "1px solid #f2b8b8";

            mensaje.style.color =
                "#b42318";
        }

    }


    formulario.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();


            mensaje.style.display =
                "none";


            const datos = {

                nombre:
                    document
                    .getElementById("nombre")
                    .value
                    .trim(),

                apellido:
                    document
                    .getElementById("apellido")
                    .value
                    .trim(),

                email:
                    document
                    .getElementById("email")
                    .value
                    .trim()
                    .toLowerCase(),

                usuario:
                    document
                    .getElementById("usuario")
                    .value
                    .trim(),

                telefono:
                    document
                    .getElementById("telefono")
                    .value
                    .trim(),

                especialidad:
                    document
                    .getElementById("especialidad")
                    .value
                    .trim(),

                password:
                    document
                    .getElementById("password")
                    .value,

                confirmar:
                    document
                    .getElementById("confirmar")
                    .value
            };


            // =============================================
            // VALIDACIONES
            // =============================================

            if(datos.nombre.length < 2){

                mostrarMensaje(
                    "Ingresa un nombre válido."
                );

                return;
            }


            if(datos.apellido.length < 2){

                mostrarMensaje(
                    "Ingresa los apellidos."
                );

                return;
            }


            if(datos.usuario.length < 4){

                mostrarMensaje(
                    "El usuario debe tener mínimo 4 caracteres."
                );

                return;
            }


            if(datos.especialidad === ""){

                mostrarMensaje(
                    "Ingresa la especialidad del profesional."
                );

                return;
            }


            if(datos.password.length < 8){

                mostrarMensaje(
                    "La contraseña debe tener mínimo 8 caracteres."
                );

                return;
            }


            if(
                datos.password !==
                datos.confirmar
            ){

                mostrarMensaje(
                    "Las contraseñas no coinciden."
                );

                return;
            }


            // =============================================
            // DESACTIVAR BOTÓN
            // =============================================

            boton.disabled = true;

            boton.textContent =
                "Creando profesional...";


            try{

                const respuesta =
                    await fetch(
                        "/admin/profesionales/crear",
                        {
                            method:"POST",

                            headers:{
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    datos
                                )
                        }
                    );


                const resultado =
                    await respuesta.json();


                if(
                    resultado.estado ===
                    "ok"
                ){

                    mostrarMensaje(
                        resultado.mensaje,
                        "exito"
                    );


                    formulario.reset();


                    setTimeout(
                        () => {

                            window.location.href =
                                "/admin/profesionales";

                        },
                        1200
                    );


                    return;
                }


                mostrarMensaje(
                    resultado.mensaje ||
                    "No fue posible crear el profesional."
                );


            }catch(error){

                console.error(
                    "ERROR:",
                    error
                );


                mostrarMensaje(
                    "No se pudo conectar con el servidor."
                );


            }finally{

                boton.disabled = false;

                boton.textContent =
                    "Crear profesional";

            }

        }
    );

});