(() => {
  const boton = document.getElementById("verClave");
  const clave = document.getElementById("id_password");
  const texto = boton?.querySelector(".sr-only");
  if (!boton || !clave) return;

  boton.addEventListener("click", () => {
    const oculto = clave.type === "password";
    clave.type = oculto ? "text" : "password";
    const etiqueta = oculto ? "Ocultar contraseña" : "Mostrar contraseña";
    boton.setAttribute("aria-label", etiqueta);
    boton.setAttribute("aria-pressed", String(oculto));
    if (texto) texto.textContent = etiqueta;
  });
})();
