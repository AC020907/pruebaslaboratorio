## Prologo: el juego empieza en el primer segundo (apertura para la Feria Gamer, ver story/apertura.rpy).
## A) la ciudad despierta  B) decision inmediata  C) el rumor corre por el grafo  D) Claudia
## E) microprueba de Moderacion Express  F) titulo  -> estilo del alcalde -> Acto I / Lunes.

label prologo(corto=False):
    $ avanzar_momento(inv.PROLOGO)
    $ apertura_marca("inicio")
    scene negro
    stop music
    $ quick_menu = False
    $ musica("tension", fadein=1.5)

    # A. La ciudad despierta
    call screen apertura_montaje
    $ apertura_marca("crisis_entendida")

    # B. Decision inmediata (menu real con pantalla propia: guardado, rollback y QA la respetan)
    $ apertura_marca("primera_interaccion")
    menu (screen="apertura_decision"):
        "Publicar un desmentido ahora mismo.":
            $ eleccion_ap = "desmentir"
        "Pedir los análisis del agua antes de responder.":
            $ eleccion_ap = "analisis"
        "No intervenir todavía: es solo un rumor más.":
            $ eleccion_ap = "ignorar"
    $ apertura_decidir(eleccion_ap)
    $ renpy.block_rollback()
    $ apertura_marca("decision")

    # C. La ciudad reacciona: BFS real desde @verdad.oculta sobre la red de Civitas
    $ niveles_ap, padres_ap, bloqueados_ap = apertura_propagacion(apertura_decision)
    $ sfx("alarma" if apertura_decision == "ignorar" else "notificacion")
    $ apertura_marca("consecuencia")
    call screen apertura_reaccion(apertura_decision, niveles_ap, padres_ap, bloqueados_ap)

    # D. Entra Claudia: reacciona a lo que ya elegiste y trae una pista nueva
    $ quick_menu = True
    scene bg despacho at paneo with rapido
    show screen tarjeta_lugar("LUNES  -  6:47 A.M.", "Despacho del alcalde")
    if apertura_decision == "desmentir":
        show claudia seria at escena("claudia") with suave
        $ reaccionar("claudia", "temblor")
        c seria "Alcalde, ya vi su desmentido. Rápido: eso calma a la gente hoy."
        c "{cps=28}Ojalá no tengamos que tragarnos esas palabras si los análisis dicen otra cosa.{/cps}"
    elif apertura_decision == "analisis":
        show claudia feliz at escena("claudia") with suave
        $ reaccionar("claudia", "salto")
        c feliz "Alcalde. Me dijeron que pidió los análisis. Alguien en este edificio que pregunta antes de hablar."
        c seria "Pero el rumor no nos va a esperar: cada hora sin respuesta suma reposts."
    else:
        show claudia enojada at escena("claudia") with suave
        $ reaccionar("claudia", "temblor")
        c enojada "¿Un rumor más? Alcalde, hay señoras haciendo fila con tres botellones cada una."
        c "Los rumores no se cansan. Nosotros sí."
    if not corto:
        c seria "Claudia Reyes, de Noticias Nova. Me asignaron a su equipo esta semana, y acepté por una razón: quiero saber quién está detrás de esto."
    else:
        c seria "Claudia Reyes, de Noticias Nova. Esta semana trabajo con usted."
    c seria "Rastreé la primera publicación. Salió de @verdad.oculta: sin foto, sin historial."
    c "{cps=22}Y ayer... esa cuenta no existía.{/cps}"
    $ dar_pista("hip_nova_creo")
    $ sfx("pista")
    $ interferencia()
    if not corto:
        tu "¿Alguien la creó solo para esto?"
        c "O alguien tiene muchas como esa, esperando su turno."
    c "Mire los comentarios: bots y vecinos asustados, todo mezclado. Borre los bots, pero a la gente real no se la calla."
    hide claudia
    hide screen tarjeta_lugar

    # E. Microprueba: el motor real de Moderacion Express, 4 comentarios
    call apertura_microprueba
    $ micro_ap = _return
    scene bg despacho with rapido
    if micro_ap == "limpio":
        show claudia feliz at escena("claudia") with suave
        c feliz "Limpio. Y nadie podrá decir que la alcaldía borra a quien la critica."
    elif micro_ap == "censuro":
        show claudia seria at escena("claudia") with suave
        c seria "Borró a una persona real. Ya hay una captura que dice que la alcaldía censura."
    elif micro_ap == "bots":
        show claudia seria at escena("claudia") with suave
        c seria "Se le colaron bots. Van a repetir lo del veneno toda la mañana."
    else:
        show claudia seria at escena("claudia") with suave
    c seria "Faltan seis días para las elecciones. Alguien quiere que Ciudad Nova llegue a ese domingo con miedo."
    hide claudia with suave

    # F. Titulo
    stop music fadeout 1.0
    call screen apertura_titulo
    $ apertura_marca("titulo")

    scene bg alcaldia at paneo with lento
    $ musica("conversacion", fadein=2.0)
    show claudia at escena("claudia") with suave
    c "Una última cosa. Esta semana la gente va a mirar cómo reacciona. ¿Qué clase de alcalde va a ser?"

    menu:
        "Cercano: hablo con la gente, no solo con los medios.":
            $ jugador.set_rol("Ciudadano")
            $ estilo_alcalde = "Cercano"
            c feliz "En los barrios lo van a notar. Allá nadie lee comunicados."
        "Analítico: primero los datos, luego la opinión.":
            $ jugador.set_rol("Periodista")
            $ estilo_alcalde = "Analítico"
            c feliz "Ese idioma lo hablo yo. Vamos a llevarnos bien."
        "Mediático: si no estoy en Civitas, no existo.":
            $ jugador.set_rol("Influencer")
            $ estilo_alcalde = "Mediático"
            c seria "Sus palabras van a llegar lejos. Las buenas... y las malas también."
        "Político: cada gesto cuenta para el domingo.":
            $ jugador.set_rol("Candidato")
            $ estilo_alcalde = "Político"
            c seria "Entonces no se equivoque en público. Allá afuera todo queda en captura."

    hide claudia with suave
    show screen hud_ciudad with rapido
    $ apertura_marca("fin_prologo")
    return
