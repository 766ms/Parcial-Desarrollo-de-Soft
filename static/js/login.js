(() => {
  const boton = document.getElementById("verClave");
  const clave = document.getElementById("id_password");
  if (!boton || !clave) return;
  boton.addEventListener("click", () => {
    const oculto = clave.type === "password";
    clave.type = oculto ? "text" : "password";
    boton.textContent = oculto ? "Ocultar" : "Ver";
    boton.setAttribute("aria-label", oculto ? "Ocultar contraseña" : "Mostrar contraseña");
  });
})();
