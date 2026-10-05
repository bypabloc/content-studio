"""Catálogo de estilos para musica.py: música de fondo para tutoriales, publicidad, demos y videos.

Cada entrada: nombre -> (caption en inglés, tonalidad, BPM[, compás]). Lo que ACE-Step recomienda:
instrumentos concretos en vez de adjetivos, género + ánimo + uso, sin tempo ni tonalidad en el caption
(van aparte) y "no vocals" al final. Las tonalidades son las que su guía considera estables.
Los candidatos que fallan al probarlos se quitan de aquí y quedan anotados en INVESTIGACION.md.
"""

# Los 9 originales, con sus tags propios para HeartMuLa.
BASE = {
    'lofi-chill': dict(
        caption='lo-fi hip hop, chill, mellow Rhodes piano, dusty vinyl crackle, soft boom bap drums, warm bass, relaxing',
        tags='lofi,hip hop,chill,piano,relaxing', tono='C Major', bpm=80, compas='4',
    ),
    'lofi-jazz': dict(
        caption='jazzy lo-fi, smooth jazz chords, muted trumpet, upright bass, brushed drums, tape saturation, cozy',
        tags='lofi,jazz,chill,trumpet,cozy', tono='D Minor', bpm=85, compas='4',
    ),
    'lofi-lluvia': dict(
        caption='rainy lo-fi, melancholic piano, rain ambience, vinyl noise, slow lazy drums, nostalgic, calm',
        tags='lofi,rain,melancholic,piano,calm', tono='E Minor', bpm=72, compas='4',
    ),
    'lofi-estudio': dict(
        caption='lo-fi study beats, soft guitar, gentle keys, steady laid-back groove, focused, minimal, background music',
        tags='lofi,study,guitar,focus,minimal', tono='G Major', bpm=78, compas='4',
    ),
    'lofi-nocturno': dict(
        caption='late night lo-fi, dreamy synth pads, deep sub bass, slow swing drums, city night atmosphere, ambient',
        tags='lofi,night,dreamy,synth,ambient', tono='A Minor', bpm=70, compas='4',
    ),
    'corporate': dict(
        caption='corporate background music, uplifting, clean electric piano, light plucks, soft claps, optimistic, modern tech',
        tags='corporate,uplifting,piano,positive,background', tono='C Major', bpm=110, compas='4',
    ),
    'future-bass': dict(
        caption='soft future bass, bright supersaw chords, gentle sidechain, airy plucks, positive, polished, background',
        tags='future bass,electronic,bright,positive,soft', tono='G Major', bpm=100, compas='4',
    ),
    'deep-house': dict(
        caption='deep house, warm groove, smooth chords, round bass, crisp hi-hats, elegant, minimal, background',
        tags='deep house,groove,warm,minimal,elegant', tono='A Minor', bpm=120, compas='4',
    ),
    'ambient': dict(
        caption='ambient, evolving soft pads, gentle piano notes, airy textures, calm, spacious, no drums',
        tags='ambient,calm,pads,piano,spacious', tono='D Major', bpm=70, compas='4',
    ),
}

# nombre: (caption, tonalidad, bpm) o (caption, tonalidad, bpm, compás)
NUEVOS = {
    # Tutoriales y explicativos: bajo, sin melodía que compita con la voz
    'tutorial-calmo': ('soft piano, warm pad, light pluck, gentle, minimal, focused, tutorial background', 'C Major', 90),
    'tutorial-tech': ('clean synth plucks, soft electric piano, minimal electronic beat, friendly, modern, explainer background', 'G Major', 100),
    'tutorial-guitarra': ('fingerstyle acoustic guitar, soft shaker, warm, friendly, light, unobtrusive background', 'G Major', 95),
    'explainer-animado': ('playful marimba, pizzicato strings, light claps, bright, curious, animated explainer', 'C Major', 115),
    'explainer-minimal': ('minimal piano motif, soft sub bass, airy pad, clear, uncluttered, background', 'D Major', 85),
    'curso-online': ('gentle kalimba, soft piano, warm pad, relaxed, educational, background', 'C Major', 88),
    'paso-a-paso': ('steady soft pulse, muted pluck, light percussion, neutral, step by step tutorial background', 'A Minor', 100),
    'codigo': ('ambient electronic, soft arpeggio, deep pad, focused, coding background', 'D Minor', 92),
    'documental-suave': ('gentle piano and strings, reflective, documentary underscore', 'D Major', 76),
    # Corporativo y publicidad
    'corporate-inspirador': ('uplifting corporate, acoustic guitar, piano, soft claps, inspiring, motivational', 'C Major', 112),
    'corporate-minimal': ('minimal corporate, soft piano, subtle strings, clean, trustworthy, background', 'G Major', 100),
    'corporate-energico': ('driving corporate, bright guitars, punchy claps, energetic, ambitious', 'D Major', 124),
    'corporate-startup': ('upbeat startup, glockenspiel, light synth, finger snaps, optimistic', 'G Major', 118),
    'corporate-confianza': ('warm strings, piano, slow build, trust, reassuring, finance', 'C Major', 84),
    'corporate-innovacion': ('futuristic, pulsing synth, clean bass, airy, innovation, technology', 'A Minor', 108),
    'corporate-motivacional': ('motivational cinematic build, piano, strings, drums crescendo, inspiring', 'D Major', 100),
    'anuncio-alegre': ('cheerful commercial, ukulele, whistle, claps, happy, bright', 'C Major', 120),
    'anuncio-premium': ('luxury brand, deep bass, glossy synth, sparse, elegant, premium', 'A Minor', 95),
    'anuncio-moda': ('fashion runway, deep house groove, sleek, sophisticated', 'A Minor', 122),
    'anuncio-deportivo': ('sports advert, powerful drums, rock guitars, stadium claps, intense', 'E Minor', 130),
    'anuncio-comida': ('warm acoustic, light jazzy guitar, cheerful, appetizing, cafe commercial', 'G Major', 108),
    'anuncio-lanzamiento': ('product launch, building synths, impact hits, riser, excitement', 'A Minor', 118),
    'anuncio-fintech': ('modern fintech, clean pluck, soft kick, secure, smooth, polished', 'C Major', 104),
    'anuncio-inmobiliario': ('real estate, warm piano, gentle strings, aspirational, spacious', 'D Major', 80),
    'anuncio-salud': ('healthcare, soft piano, light strings, caring, calm, clean', 'G Major', 76),
    'anuncio-viajes': ('travel advert, acoustic guitar, hand percussion, adventurous, sunny', 'D Major', 110),
    'anuncio-auto': ('automotive, powerful synth bass, driving beat, sleek, cinematic', 'E Minor', 112),
    # Demos de producto y tecnología
    'demo-producto': ('product demo, clean electronic, bouncy bass, light claps, modern', 'G Major', 108),
    'demo-saas': ('SaaS demo, bubbly synth plucks, soft beat, tidy, positive', 'C Major', 110),
    'demo-app-movil': ('mobile app showcase, playful plucks, light percussion, fresh', 'D Major', 114),
    'demo-futurista': ('futuristic interface, glassy bells, sub pulses, sci-fi, clean', 'A Minor', 100),
    'demo-ia': ('artificial intelligence, ambient electronic, evolving arpeggios, minimal percussion, curious', 'E Minor', 96),
    'demo-gadget': ('tech gadget unboxing, crisp beat, funky bass, stylish', 'A Minor', 105),
    'demo-ecommerce': ('e-commerce promo, upbeat pop instrumental, claps, bright, shiny', 'C Major', 118),
    'demo-dashboard': ('data dashboard, steady minimal techno, soft pad, analytical', 'A Minor', 112),
    'demo-videojuego': ('video game showcase, chiptune lead, driving bass, playful', 'C Major', 125),
    # Familia lofi
    'lofi-cafe': ('lofi jazz hop, warm piano, soft brushes, coffee shop, cozy', 'C Major', 82),
    'lofi-guitarra': ('lofi, mellow electric guitar, dusty drums, warm bass, relaxed', 'A Minor', 76),
    'lofi-atardecer': ('lofi chillhop, warm pads, soft kick, sunset, mellow', 'G Major', 84),
    'lofi-nostalgico': ('lofi, nostalgic piano, soft bells, gentle, tape hiss, dreamy', 'E Minor', 76),
    'lofi-bossa': ('lofi bossa nova, nylon guitar, soft shaker, warm, relaxed', 'D Minor', 88),
    'chillhop-foco': ('chillhop, jazzy keys, boom bap drums, upright bass, focus', 'D Minor', 90),
    'lofi-piano': ('solo piano lofi, tape hiss, mellow, intimate, slow', 'C Major', 68),
    'vaporwave': ('vaporwave, slowed, dreamy synth, nostalgic, hazy, retro', 'G Major', 80),
    # Ambient, foco y bienestar
    'ambient-espacial': ('spacious ambient drone, shimmering pads, slow evolving, no drums', 'D Major', 60),
    'ambient-piano': ('ambient piano, soft reverb, slow, contemplative, no drums', 'C Major', 64),
    'ambient-cinematico': ('cinematic ambient, wide pads, low drone, subtle swells, no drums', 'A Minor', 60),
    'ambient-bosque': ('nature ambient, soft pads, gentle bells, forest atmosphere, peaceful', 'G Major', 62),
    'ambient-oceano': ('ocean ambient, slow pads, wave texture, calm, vast', 'D Major', 58),
    'meditacion': ('meditation, singing bowls, soft pads, peaceful, slow', 'C Major', 60),
    'yoga': ('new age, flute, soft pads, harp, calm, flowing', 'D Major', 66),
    'spa': ('spa, gentle harp, soft piano, warm pad, relaxing', 'G Major', 64),
    'dormir': ('sleep music, very soft pads, slow, dreamy, minimal, no drums', 'C Major', 52),
    'foco-profundo': ('deep focus, minimal drone, subtle pulse, concentration', 'A Minor', 70),
    'new-age': ('new age, synth pads, crystal bells, floating, serene', 'G Major', 68),
    'ambient-oscuro': ('dark ambient, low drones, slow tension, minimal, no drums', 'D Minor', 60),
    # Cinematográfico y documental
    'cinematico-emotivo': ('emotional cinematic, piano, strings, heartfelt, slow build', 'D Minor', 72),
    'cinematico-esperanza': ('hopeful cinematic, strings, piano, building, inspiring', 'D Major', 90),
    'trailer-tension': ('trailer music, tense, pulsing synths, low brass, risers, impact hits', 'A Minor', 110),
    'cinematico-minimal': ('minimalist cinematic, piano ostinato, soft strings, subtle', 'A Minor', 84),
    'documental-naturaleza': ('nature documentary, orchestral, majestic, sweeping strings, french horn', 'G Major', 76),
    'heroico': ('heroic orchestral, french horns, snare roll, triumphant', 'C Major', 108),
    'misterio': ('mystery, plucked strings, soft piano, suspense, subtle', 'E Minor', 84),
    'suspenso-tech': ('tech thriller, dark synth pulse, deep bass, tense', 'E Minor', 100),
    'ciencia-ficcion': ('sci-fi, analog synths, spacey, wonder, evolving', 'A Minor', 90),
    'fantasia': ('fantasy, harp, flute, strings, magical, light', 'D Major', 88),
    'orquesta-calida': ('warm chamber orchestra, strings, woodwinds, gentle', 'G Major', 80),
    'piano-emotivo': ('solo piano, emotional, intimate, expressive', 'A Minor', 66),
    'cuerdas-minimal': ('string quartet, minimalist, gentle, repeating pattern', 'D Major', 84),
    'neoclasico': ('neoclassical, piano, cello, ambient, reflective', 'D Minor', 68),
    # Acústico y folk
    'acustico-alegre': ('happy acoustic, ukulele, hand claps, whistle, sunny', 'C Major', 118),
    'acustico-calido': ('warm acoustic guitar, soft percussion, cozy, gentle', 'G Major', 92),
    'folk-suave': ('indie folk, fingerpicked guitar, mandolin, gentle, airy', 'D Major', 100),
    'country-suave': ('light country, slide guitar, brushed drums, easygoing', 'G Major', 96),
    'piano-pop': ('pop piano instrumental, soft drums, warm, hopeful', 'C Major', 100),
    'ukulele-playa': ('ukulele, beach, sunny, light percussion, tropical, carefree', 'C Major', 108),
    'guitarra-clasica': ('classical nylon guitar, solo, elegant, intimate', 'A Minor', 90),
    'arpa-celestial': ('harp, soft strings, ethereal, gentle, floating', 'D Major', 72),
    'celta': ('celtic, tin whistle, fiddle, bodhran, gentle, folk', 'D Major', 96),
    # Jazz, latino y del mundo
    'jazz-cafe': ('cafe jazz, piano trio, brushed drums, upright bass, relaxed swing', 'G Major', 100),
    'jazz-suave': ('smooth jazz, saxophone, electric piano, warm, mellow', 'D Minor', 90),
    'bossa-nova': ('bossa nova, nylon guitar, soft percussion, relaxed, sunny', 'D Minor', 100),
    'lounge': ('lounge, vibraphone, upright bass, brushes, late night, smooth', 'A Minor', 80),
    'swing-alegre': ('upbeat swing, clarinet, piano, walking bass, vintage, cheerful', 'C Major', 140),
    'latin-suave': ('latin pop instrumental, nylon guitar, congas, warm, groovy', 'A Minor', 100),
    'cumbia-suave': ('soft cumbia, guiro, bass, light percussion, mellow, tropical', 'A Minor', 92),
    'reggae-chill': ('reggae, offbeat guitar, organ bubble, relaxed, sunny', 'G Major', 80),
    'afrobeat-ligero': ('light afrobeat, percussive guitars, groove, warm, upbeat', 'G Major', 108),
    'tropical-house': ('tropical house, marimba, plucks, sunny, groovy, summer', 'A Minor', 110),
    # Electrónica y pop de energía
    'pop-brillante': ('bright pop instrumental, claps, synth plucks, upbeat, shiny', 'C Major', 120),
    'synthwave': ('synthwave, retro 80s, analog arpeggios, gated reverb drums, driving', 'E Minor', 105),
    'retrowave-suave': ('mellow retro synths, soft drum machine, nostalgic, neon', 'A Minor', 95),
    'trap-suave': ('soft trap instrumental, 808 bass, airy pads, light hi-hats, moody', 'A Minor', 140),
    'drum-and-bass-ligero': ('liquid drum and bass, rolling breaks, warm pads, uplifting', 'A Minor', 170),
    'techno-minimal': ('minimal techno, hypnotic, driving kick, subtle synth, dark', 'A Minor', 124),
    'house-alegre': ('piano house, uplifting, claps, bright chords, feel-good', 'C Major', 124),
    'tech-house': ('tech house, rolling bass, crisp percussion, groovy, minimal', 'A Minor', 125),
    'edm-energico': ('EDM, big build, bright synth lead, driving kick, festival energy', 'A Minor', 128),
    'electropop': ('electropop instrumental, synth bass, bright arps, upbeat', 'G Major', 112),
    'downtempo': ('downtempo, trip hop beats, vinyl, smoky, warm bass', 'A Minor', 90),
    'chillwave': ('chillwave, hazy synths, washed out, dreamy, warm', 'G Major', 90),
    'future-garage': ('future garage, shuffled beats, atmospheric pads, sub bass', 'A Minor', 130),
    'chiptune-alegre': ('chiptune, 8-bit, bouncy, playful, retro game', 'C Major', 130),
    'funk-suave': ('light funk, clean guitar, slap bass, claps, groovy', 'E Minor', 104),
    'disco': ('nu disco, groovy bass, strings, shimmering guitar, feel-good', 'A Minor', 118),
    'boom-bap': ('boom bap instrumental, dusty drums, sampled piano, warm, classic', 'A Minor', 90),
    'rnb-suave': ('smooth R&B instrumental, Rhodes, soft drums, warm bass, late night', 'D Minor', 82),
    'rock-motivacional': ('motivational rock instrumental, driving guitars, powerful drums, anthemic', 'E Minor', 120),
    'indie-pop': ('indie pop instrumental, jangly guitars, claps, bright, breezy', 'G Major', 118),
    'post-rock-suave': ('post-rock, delayed guitars, slow build, atmospheric', 'D Major', 96),
    # Usos concretos
    'navidad-suave': ('gentle Christmas, sleigh bells, glockenspiel, soft piano, cozy', 'C Major', 90),
    'infantil': ('playful children, xylophone, ukulele, cheerful, light', 'C Major', 110),
    'juego-casual': ('casual mobile game, bouncy, marimba, bright, playful', 'G Major', 112),
    'entrenamiento': ('workout, energetic electronic, driving beat, intense, motivating', 'A Minor', 135),
    'noticias': ('news broadcast bed, pulsing synth, neutral, steady, professional', 'A Minor', 112),
    'cocina': ('cooking show, light jazzy guitar, cheerful, warm, upbeat', 'G Major', 100),
    'vlog-viaje': ('travel vlog, upbeat indie acoustic, whistle, claps, sunny', 'G Major', 110),
}


def _entrada(caption: str, tono: str, bpm: int, compas: str = '4') -> dict:
    """caption con "no vocals" al final; tags de HeartMuLa = las primeras etiquetas del caption.

    >>> e = _entrada('lofi, soft piano, warm, calm, cozy, extra', 'C Major', 80)
    >>> e['caption'], e['tags'], e['compas']
    ('lofi, soft piano, warm, calm, cozy, extra, no vocals', 'lofi,soft piano,warm,calm,cozy', '4')
    """
    return dict(caption=f'{caption}, no vocals', tags=','.join(caption.split(', ')[:5]), tono=tono, bpm=bpm, compas=compas)


ESTILOS = {**BASE, **{nombre: _entrada(*datos) for nombre, datos in NUEVOS.items()}}
