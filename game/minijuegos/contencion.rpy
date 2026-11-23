## Minijuego 3 - Contencion de la crisis: "Central de Emergencias" (estrategia en tiempo real, minijuegos/central.rpy).
## Sustituye a Caza-Rumores en el mismo punto de la historia; la firma del label no cambia, asi que las llamadas
## de Historia, Feria, publicaciones de CivitasNet y Arena siguen igual. El arcade anterior (CazaRumores +
## jugar_arcade) queda en el codigo pero fuera de la experiencia jugable (docs/CENTRAL_EMERGENCIAS.md).
## Uso:  call minijuego_contencion                         (modo segun Historia o Feria; semilla aleatoria)
##       call minijuego_contencion(semilla=7)              (partida reproducible)
##       call minijuego_contencion(ajustes={"modo": "arena", "tutorial": False, "reinicio": False})
## Retorna (en _return) el dict de CentralEmergencias.Central.resultado() (clave "contencion").

label minijuego_contencion(focos=None, semilla=None, aplicar=True, ajustes=None):
    $ ajustes_central = dict(ajustes or {})
    $ modo_central = ajustes_central.get("modo") or ("feria" if modo_feria_activo else "historia")
    call minijuego_central(modo_central, semilla, aplicar, ajustes_central.get("tutorial", True),
                           ajustes_central.get("reinicio", True), ajustes_central.get("escenario"))
    return _return
