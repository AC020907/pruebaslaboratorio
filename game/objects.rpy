init python:
    from clases.Publicacion import SesionPublicacion, BancoPublicaciones, armar_publicacion
    from clases.Ciudad import Ciudad
    from clases.Jugador import Jugador

    def aplicar_consecuencia(consecuencia):
        if not consecuencia:
            return
        for clave, valor in consecuencia.items():
            if clave == 'puntos':
                if valor > 0:
                    store.jugador.ganar_puntos(valor)
                else:
                    store.jugador.perder_puntos(-valor)
            elif clave == 'reputacion':
                store.jugador.reputacion = max(0, min(100, store.jugador.reputacion + valor))
            elif hasattr(store.ciudad, clave):
                nuevo = max(0, min(100, getattr(store.ciudad, clave) + valor))
                setattr(store.ciudad, clave, nuevo)
        mostrar_cambios(consecuencia)

label nueva_publicacion:
    if not banco.hay_mas():
        return

    $ sesion = SesionPublicacion(banco.siguiente())
    $ publicaciones_vistas += 1
    play sound "assets/audio/sfx/notificacion.wav"
    window hide

    while not sesion.terminada():
        $ eleccion = renpy.call_screen("telefono_civitas", sesion=sesion)
        $ sesion.elegir(eleccion)

    window auto
    civitas "[sesion.actual.texto]"

    $ aplicar_consecuencia(sesion.actual.consecuencia)
    $ ultima_accion = accion_elegida(sesion)
    $ ultima_publicacion_falsa = sesion.publicacion.es_falsa
    $ registrar_decision_publicacion(sesion.publicacion, ultima_accion)

    call reaccion_red_civitas(sesion)

    $ razon_derrota = ciudad.derrota_inmediata() or ""
    if razon_derrota:
        jump final_caos

    return

default publicaciones_vistas = 0
default ultima_accion = None
default ultima_publicacion_falsa = False

# Estado de la ciudad y del jugador

default ciudad = Ciudad()
default jugador = Jugador("Alcalde")
default razon_derrota = ""

# Banco de publicaciones — insertadas en AVL por nivel_riesgo, entregadas de menor a mayor
# Cada publicacion tiene 4 acciones segun el diagrama del PDF (pag. 4):
#   Compartir | Verificar (Si/No) | Ignorar

default banco = BancoPublicaciones([

    armar_publicacion(
        "@verde.ciudad",
        "El colegio San Marcos lanzó una campaña de reciclaje.",
        False, 10,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La difundes de inmediato. La comunidad se suma y el bienestar mejora.",
            "efecto": {"bienestar": 3, "confianza": 1, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La oportunidad pasa desapercibida. Nada cambia.",
            "efecto": {"bienestar": -1}},
        verificar_si={
            "etiqueta": "Sí, es verdadera — Compartir",
            "texto": "Verificas y confirmas. La difundes con credibilidad. Excelente gestión.",
            "efecto": {"bienestar": 5, "confianza": 3, "info_verificada": 3, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es falsa — Reportar",
            "texto": "Detectas que es falsa y la reportas. Ciudad Nova te lo agradece.",
            "efecto": {"desinformacion": -3, "confianza": 2, "puntos": 6}},
    ),

    armar_publicacion(
        "@salud.nova",
        "La alcaldía inauguró el nuevo hospital del sur esta mañana.",
        False, 15,
        compartir={
            "etiqueta": "Compartir",
            "texto": "Los ciudadanos reciben la buena noticia. La confianza en instituciones crece.",
            "efecto": {"bienestar": 4, "confianza": 2, "puntos": 5}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La noticia no llega a tiempo. Oportunidad perdida.",
            "efecto": {"bienestar": -1}},
        verificar_si={
            "etiqueta": "Sí, es verdadera — Compartir",
            "texto": "Confirmas con la alcaldía y difundes con datos. Gestión ejemplar.",
            "efecto": {"bienestar": 6, "confianza": 4, "info_verificada": 3, "puntos": 10}},
        verificar_no={
            "etiqueta": "No, es falsa — Reportar",
            "texto": "Era un rumor. Lo reportas y evitas confusión ciudadana.",
            "efecto": {"desinformacion": -3, "confianza": 3, "puntos": 7}},
    ),

    armar_publicacion(
        "@candidata.luna",
        "Propongo convertir el lote abandonado del barrio norte en zona verde.",
        False, 20,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La propuesta gana respaldo ciudadano. La ciudad florece.",
            "efecto": {"bienestar": 2, "confianza": 2, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "Los ciudadanos sienten que nadie escucha las propuestas.",
            "efecto": {"convivencia": -1}},
        verificar_si={
            "etiqueta": "Sí, es seria — Compartir con contexto",
            "texto": "Verificas la propuesta y la apoyas con datos. Gran impacto.",
            "efecto": {"bienestar": 4, "confianza": 3, "convivencia": 2, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es propaganda — Reportar",
            "texto": "Detectas que es solo propaganda electoral. La reportas.",
            "efecto": {"desinformacion": -2, "confianza": 1, "puntos": 5}},
    ),

    armar_publicacion(
        "@barrio.central",
        "Vecinos del barrio central llevan tres semanas sin alumbrado público.",
        False, 30,
        compartir={
            "etiqueta": "Compartir",
            "texto": "Visibilizas el problema. La gente siente que su voz importa.",
            "efecto": {"convivencia": 2, "confianza": 1, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "Los vecinos pierden la fe en las instituciones.",
            "efecto": {"convivencia": -2, "confianza": -2}},
        verificar_si={
            "etiqueta": "Sí, es real — Gestionar y comunicar acciones",
            "texto": "Verificas y canalizas la queja oficial. La convivencia mejora.",
            "efecto": {"convivencia": 4, "confianza": 3, "bienestar": 2, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es exagerado — Reportar",
            "texto": "Era una exageración. La reportas para no generar alarma falsa.",
            "efecto": {"desinformacion": -2, "convivencia": 1, "puntos": 4}},
    ),

    armar_publicacion(
        "@salud.publica",
        "Se registraron 40 casos de gripe en escuelas del centro. Las autoridades investigan.",
        False, 40,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La ciudadanía actúa con prevención. Buen manejo de la información.",
            "efecto": {"info_verificada": 2, "bienestar": 1, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "Los ciudadanos no saben de la alerta. Se siguen contagiando.",
            "efecto": {"bienestar": -3, "desinformacion": 2}},
        verificar_si={
            "etiqueta": "Sí, es verdadera — Informar con datos médicos",
            "texto": "Confirmas con autoridades de salud y difundes con calma. Excelente.",
            "efecto": {"info_verificada": 5, "confianza": 3, "bienestar": 3, "puntos": 10}},
        verificar_no={
            "etiqueta": "No, es exagerado — Reportar para evitar pánico",
            "texto": "Evitas el pánico colectivo. Ciudad Nova respira tranquila.",
            "efecto": {"desinformacion": -4, "conflictos": -2, "puntos": 7}},
    ),

    armar_publicacion(
        "@preocupado99",
        "Dicen que el gobierno va a privatizar el acueducto. Ya no tendremos agua gratis.",
        True, 55,
        compartir={
            "etiqueta": "Compartir",
            "texto": "El rumor se propaga rápidamente. Los ciudadanos entran en conflicto.",
            "efecto": {"conflictos": 5, "desinformacion": 4, "confianza": -3}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "El rumor sigue circulando sin respuesta. La tensión aumenta.",
            "efecto": {"conflictos": 2, "desinformacion": 2}},
        verificar_si={
            "etiqueta": "Sí, es verdad — Compartir con evidencia oficial",
            "texto": "Verificas y resulta verdadero. Lo informas con fuentes. Ciudad confía.",
            "efecto": {"info_verificada": 4, "confianza": 3, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es falso — Reportar y desmentir",
            "texto": "La verdad prevalece. La confianza en las instituciones se fortalece.",
            "efecto": {"reputacion": 6, "confianza": 4, "desinformacion": -5, "puntos": 12}},
    ),

    armar_publicacion(
        "@noticias.nova",
        "Fuentes anónimas afirman que el alcalde ordenará el cierre de todos los parques.",
        True, 60,
        compartir={
            "etiqueta": "Compartir",
            "texto": "El rumor llega a miles. Los conflictos aumentan por la incertidumbre.",
            "efecto": {"conflictos": 5, "desinformacion": 4, "convivencia": -3}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "El rumor circula sin freno. La tensión sigue creciendo.",
            "efecto": {"conflictos": 2, "desinformacion": 3}},
        verificar_si={
            "etiqueta": "Sí, es verdad — Informar con datos oficiales",
            "texto": "Confirmas la noticia con el alcalde y la comunicas claramente.",
            "efecto": {"info_verificada": 4, "confianza": 2, "puntos": 7}},
        verificar_no={
            "etiqueta": "No, es falso — Reportar y comunicar la verdad",
            "texto": "Confirmas que es falso y lo comunicas. La ciudad respira tranquila.",
            "efecto": {"info_verificada": 5, "confianza": 3, "desinformacion": -4, "puntos": 10}},
    ),

    armar_publicacion(
        "@sol.y.limon",
        "Escuché que el alcalde robó fondos públicos para comprar su casa. Lo vi en un video.",
        True, 75,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La acusación se viraliza. Si era falsa, destruiste a un inocente.",
            "efecto": {"reputacion": -8, "desinformacion": 5, "conflictos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "El rumor crece y la gente duda de las instituciones.",
            "efecto": {"reputacion": -4, "desinformacion": 3}},
        verificar_si={
            "etiqueta": "Sí, hay evidencia — Compartir con pruebas",
            "texto": "Verificas y hay evidencia real. Lo comunicas con responsabilidad.",
            "efecto": {"info_verificada": 5, "confianza": 2, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es falso — Reportar y desmentir",
            "texto": "La gente te cree. Tu reputación se consolida. La verdad gana.",
            "efecto": {"reputacion": 10, "confianza": 5, "desinformacion": -5, "puntos": 14}},
    ),

    armar_publicacion(
        "@investigador.nova",
        "Tengo pruebas de que el candidato Tomás tiene vínculos con grupos criminales.",
        True, 85,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La ciudad entra en caos. Una acusación sin verificar destruye reputaciones.",
            "efecto": {"desinformacion": 6, "conflictos": 5, "confianza": -5}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La grave acusación queda sin respuesta. La incertidumbre crece.",
            "efecto": {"conflictos": 3, "desinformacion": 2}},
        verificar_si={
            "etiqueta": "Sí, hay evidencia — Reportar a autoridades",
            "texto": "Actúas con responsabilidad. Las autoridades investigan. Los conflictos bajan.",
            "efecto": {"reputacion": 8, "conflictos": -4, "desinformacion": -3, "puntos": 12}},
        verificar_no={
            "etiqueta": "No, es fabricado — Reportar la manipulación",
            "texto": "Expones la manipulación. Ciudad Nova se protege de la desinformación.",
            "efecto": {"info_verificada": 5, "confianza": 3, "desinformacion": -4, "puntos": 10}},
    ),

    armar_publicacion(
        "@ciudadano",
        "El candidato a alcalde ha sido acusado de corrupción por 3 millones de pesos.",
        True, 90,
        compartir={
            "etiqueta": "Compartir",
            "texto": "El rumor se propaga. Si era falso, destruiste a un inocente y pierdes credibilidad.",
            "efecto": {"reputacion": -15, "desinformacion": 8, "conflictos": 6}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La acusación sigue circulando sin respuesta. La desconfianza aumenta.",
            "efecto": {"conflictos": 4, "confianza": -3, "desinformacion": 3}},
        verificar_si={
            "etiqueta": "Sí, hay evidencia — Investigar y publicar pruebas",
            "texto": "La gente te respalda. La verdad fortalece la democracia.",
            "efecto": {"reputacion": 15, "confianza": 5, "desinformacion": -6, "puntos": 15}},
        verificar_no={
            "etiqueta": "No, es falsa — Reportar y exigir rectificación",
            "texto": "Proteges al acusado inocente. La transparencia gana. Ciudad Nova prospera.",
            "efecto": {"reputacion": 12, "info_verificada": 6, "confianza": 4, "puntos": 12}},
    ),

])
