# Sistema de evaluaciones — arquitectura MVC

| Capa | Dónde está | Responsabilidad |
|---|---|---|
| **Modelo** | `accounts/models.py`, `evaluaciones/models.py` | Datos y reglas de negocio |
| **Vista** | `templates/` y `static/` (HTML, CSS, JS vanilla) | Lo que ve el usuario |
| **Controlador** | `accounts/controllers.py`, `evaluaciones/controllers.py`, `urls.py` | Recibe la entrada, llama al modelo, elige la vista |

Flujo: Usuario → Vista (formulario) → Controlador → Modelo → Controlador → Vista.
(Django llama a este patrón MVT; sus "templates" son la V de MVC y sus "views" son la C.)

## Módulo: gestión de cuestionarios (CRUD)
- **Modelo:** `Cuestionario`, `Seccion`, `Pregunta`, `Opcion` + consultas en `CuestionarioManager`.
- **Vista:** `templates/cuestionarios/` y `templates/crud/`, estilos en `static/css/panel.css`.
- **Controlador:** `evaluaciones/controllers/cuestionarios.py` (solo Admin, ver `accounts/mixins.py`).
- Datos de ejemplo: `python manage.py cargar_ejemplo`

## Módulos completos
| Módulo | Modelo | Controlador | Vista |
|---|---|---|---|
| Usuarios (CRUD) | `accounts/models.py` | `accounts/controllers.py` | `templates/usuarios/` |
| Periodos (CRUD) | `evaluaciones/models.py` | `evaluaciones/controllers/periodos.py` | `templates/periodos/` |
| Evaluaciones (CRUD + resultados) | `Evaluacion` | `evaluaciones/controllers/evaluaciones.py` | `templates/evaluaciones/` |
| Responder evaluación | `Evaluacion.registrar_respuestas()` | `ResponderEvaluacion` | `templates/evaluaciones/responder.html` |

Base común de los controladores CRUD: `accounts/mixins.py`.
