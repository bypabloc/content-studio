# Estilos de música disponibles (126)

Catálogo de presets de `music/musica.py`, definido en [estilos.py](estilos.py). Se usan con `--estilo <nombre>`. Los 117 nuevos se generaron a 30 s con ACE-Step y pasaron `--evaluar` (sin voz, al menos 20 s, no mudos); cómo se probaron y qué se descartó está en [INVESTIGACION.md](INVESTIGACION.md). **Nadie escuchó las pistas**: las métricas no dicen si el estilo se reconoce ni si suena bien.

Todos van en compás 4/4. Tono y BPM se pueden pisar con `--tono` y `--bpm`.

Presets que pasaron por poco en voz (entre −25 y −32 dB): `demo-producto`, `heroico`, `suspenso-tech`, `ambient-oceano`, `tutorial-tech`, `ciencia-ficcion`, `pop-brillante`, `demo-saas`. Con ellos conviene `--evaluar --reintentos 2`.

Descartados por voz y no incluidos: `cinematico-epico` y `documental-historia`.

## Los 9 originales

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `lofi-chill` | Rhodes, vinilo, boom bap suave | C Major | 80 |
| `lofi-jazz` | Acordes de jazz, trompeta con sordina, escobillas | D Minor | 85 |
| `lofi-lluvia` | Piano melancólico, ambiente de lluvia | E Minor | 72 |
| `lofi-estudio` | Guitarra suave, groove relajado, minimal | G Major | 78 |
| `lofi-nocturno` | Pads de sintetizador, sub bajo, ciudad de noche | A Minor | 70 |
| `corporate` | Fondo tech optimista, piano eléctrico, plucks | C Major | 110 |
| `future-bass` | Supersaw suaves, sidechain leve, brillante | G Major | 100 |
| `deep-house` | Groove cálido, bajo redondo, elegante | A Minor | 120 |
| `ambient` | Pads que evolucionan, sin batería | D Major | 70 |

## Tutoriales y explicativos

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `tutorial-calmo` | Piano suave, pad cálido, pluck ligero | C Major | 90 |
| `tutorial-tech` | Plucks de sintetizador, piano eléctrico, beat minimal | G Major | 100 |
| `tutorial-guitarra` | Guitarra fingerstyle, shaker suave | G Major | 95 |
| `explainer-animado` | Marimba juguetona, pizzicato, palmas ligeras | C Major | 115 |
| `explainer-minimal` | Motivo de piano, sub bajo suave, pad aireado | D Major | 85 |
| `curso-online` | Kalimba, piano suave, pad cálido | C Major | 88 |
| `paso-a-paso` | Pulso suave y constante, pluck apagado | A Minor | 100 |
| `codigo` | Electrónica ambient, arpegio suave, pad profundo | D Minor | 92 |
| `documental-suave` | Piano y cuerdas suaves, reflexivo | D Major | 76 |

## Corporativo y publicidad

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `corporate-inspirador` | Guitarra acústica, piano, palmas suaves | C Major | 112 |
| `corporate-minimal` | Piano suave, cuerdas sutiles, limpio | G Major | 100 |
| `corporate-energico` | Guitarras brillantes, palmas con pegada | D Major | 124 |
| `corporate-startup` | Glockenspiel, sintetizador ligero, chasquidos | G Major | 118 |
| `corporate-confianza` | Cuerdas cálidas, piano, crecimiento lento | C Major | 84 |
| `corporate-innovacion` | Sintetizador pulsante, bajo limpio, futurista | A Minor | 108 |
| `corporate-motivacional` | Crescendo cinematográfico, piano, cuerdas, batería | D Major | 100 |
| `anuncio-alegre` | Ukulele, silbido, palmas | C Major | 120 |
| `anuncio-premium` | Bajo profundo, sintetizador brillante, elegante | A Minor | 95 |
| `anuncio-moda` | Groove deep house, pasarela, sofisticado | A Minor | 122 |
| `anuncio-deportivo` | Batería potente, guitarras rock, palmas de estadio | E Minor | 130 |
| `anuncio-comida` | Acústico cálido, guitarra jazzera, café | G Major | 108 |
| `anuncio-lanzamiento` | Sintetizadores en crescendo, impactos, riser | A Minor | 118 |
| `anuncio-fintech` | Pluck limpio, kick suave, seguro y pulido | C Major | 104 |
| `anuncio-inmobiliario` | Piano cálido, cuerdas suaves, aspiracional | D Major | 80 |
| `anuncio-salud` | Piano suave, cuerdas ligeras, calmado | G Major | 76 |
| `anuncio-viajes` | Guitarra acústica, percusión de mano, aventurero | D Major | 110 |
| `anuncio-auto` | Bajo sintético potente, beat constante, cinematográfico | E Minor | 112 |

## Demos y tecnología

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `demo-producto` | Electrónica limpia, bajo saltarín, palmas ligeras | G Major | 108 |
| `demo-saas` | Plucks burbujeantes, beat suave, ordenado | C Major | 110 |
| `demo-app-movil` | Plucks juguetones, percusión ligera, fresco | D Major | 114 |
| `demo-futurista` | Campanas cristalinas, pulsos graves, sci-fi | A Minor | 100 |
| `demo-ia` | Electrónica ambient, arpegios que evolucionan | E Minor | 96 |
| `demo-gadget` | Beat nítido, bajo funky, con estilo | A Minor | 105 |
| `demo-ecommerce` | Pop instrumental, palmas, brillante | C Major | 118 |
| `demo-dashboard` | Techno minimal constante, pad suave, analítico | A Minor | 112 |
| `demo-videojuego` | Lead chiptune, bajo marcado, juguetón | C Major | 125 |

## Lofi (nuevos)

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `lofi-cafe` | Lofi jazz hop, piano cálido, escobillas, cafetería | C Major | 82 |
| `lofi-guitarra` | Guitarra eléctrica suave, batería polvorienta | A Minor | 76 |
| `lofi-atardecer` | Chillhop, pads cálidos, kick suave | G Major | 84 |
| `lofi-nostalgico` | Piano nostálgico, campanas suaves, hiss de cinta | E Minor | 76 |
| `lofi-bossa` | Bossa nova lofi, guitarra de nylon, shaker | D Minor | 88 |
| `chillhop-foco` | Teclas jazzeras, boom bap, contrabajo | D Minor | 90 |
| `lofi-piano` | Piano solo lofi, hiss de cinta, íntimo | C Major | 68 |
| `vaporwave` | Ralentizado, sintetizador onírico, retro | G Major | 80 |

## Ambient, foco y bienestar

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `ambient-espacial` | Drone espacial, pads brillantes, sin batería | D Major | 60 |
| `ambient-piano` | Piano ambient, reverb suave, contemplativo | C Major | 64 |
| `ambient-cinematico` | Pads amplios, drone grave, swells sutiles | A Minor | 60 |
| `ambient-bosque` | Pads suaves, campanas, atmósfera de bosque | G Major | 62 |
| `ambient-oceano` | Pads lentos, textura de olas, vasto | D Major | 58 |
| `meditacion` | Cuencos tibetanos, pads suaves, lento | C Major | 60 |
| `yoga` | New age, flauta, arpa, fluido | D Major | 66 |
| `spa` | Arpa suave, piano, pad cálido | G Major | 64 |
| `dormir` | Pads muy suaves, lento, onírico | C Major | 52 |
| `foco-profundo` | Drone minimal, pulso sutil, concentración | A Minor | 70 |
| `new-age` | Pads de sintetizador, campanas de cristal, sereno | G Major | 68 |
| `ambient-oscuro` | Drones graves, tensión lenta, minimal | D Minor | 60 |

## Cinematográfico

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `cinematico-emotivo` | Piano, cuerdas, crecimiento sentido | D Minor | 72 |
| `cinematico-esperanza` | Cuerdas, piano, inspirador | D Major | 90 |
| `trailer-tension` | Sintetizadores pulsantes, metales graves, risers | A Minor | 110 |
| `cinematico-minimal` | Ostinato de piano, cuerdas suaves | A Minor | 84 |
| `documental-naturaleza` | Orquestal majestuoso, cuerdas amplias, trompa | G Major | 76 |
| `heroico` | Trompas, redoble de caja, triunfal | C Major | 108 |
| `misterio` | Cuerdas pulsadas, piano suave, suspenso | E Minor | 84 |
| `suspenso-tech` | Pulso de sintetizador oscuro, bajo profundo | E Minor | 100 |
| `ciencia-ficcion` | Sintetizadores analógicos, espacial, asombro | A Minor | 90 |
| `fantasia` | Arpa, flauta, cuerdas, mágico | D Major | 88 |
| `orquesta-calida` | Orquesta de cámara, cuerdas, maderas | G Major | 80 |
| `piano-emotivo` | Piano solo, íntimo, expresivo | A Minor | 66 |
| `cuerdas-minimal` | Cuarteto de cuerdas, minimalista, patrón repetido | D Major | 84 |
| `neoclasico` | Piano, violonchelo, ambient, reflexivo | D Minor | 68 |

## Acústico y folk

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `acustico-alegre` | Ukulele, palmas, silbido, soleado | C Major | 118 |
| `acustico-calido` | Guitarra acústica cálida, percusión suave | G Major | 92 |
| `folk-suave` | Indie folk, guitarra con púa de dedos, mandolina | D Major | 100 |
| `country-suave` | Country ligero, slide guitar, escobillas | G Major | 96 |
| `piano-pop` | Piano pop instrumental, batería suave, esperanzador | C Major | 100 |
| `ukulele-playa` | Ukulele, playa, percusión ligera, tropical | C Major | 108 |
| `guitarra-clasica` | Guitarra de nylon solista, elegante | A Minor | 90 |
| `arpa-celestial` | Arpa, cuerdas suaves, etéreo | D Major | 72 |
| `celta` | Tin whistle, violín, bodhrán, folk | D Major | 96 |

## Jazz, latino y del mundo

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `jazz-cafe` | Trío de piano, escobillas, contrabajo, swing relajado | G Major | 100 |
| `jazz-suave` | Smooth jazz, saxofón, piano eléctrico | D Minor | 90 |
| `bossa-nova` | Guitarra de nylon, percusión suave, soleado | D Minor | 100 |
| `lounge` | Vibráfono, contrabajo, escobillas, nocturno | A Minor | 80 |
| `swing-alegre` | Swing animado, clarinete, bajo caminante, vintage | C Major | 140 |
| `latin-suave` | Latin pop instrumental, guitarra de nylon, congas | A Minor | 100 |
| `cumbia-suave` | Cumbia suave, güiro, bajo, tropical | A Minor | 92 |
| `reggae-chill` | Reggae, guitarra a contratiempo, órgano, relajado | G Major | 80 |
| `afrobeat-ligero` | Guitarras percusivas, groove cálido | G Major | 108 |
| `tropical-house` | Marimba, plucks, groove veraniego | A Minor | 110 |

## Electrónica y pop

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `pop-brillante` | Pop instrumental, palmas, plucks de sintetizador | C Major | 120 |
| `synthwave` | Retro 80s, arpegios analógicos, batería gated | E Minor | 105 |
| `retrowave-suave` | Sintetizadores retro suaves, caja de ritmos, neón | A Minor | 95 |
| `trap-suave` | Trap suave, 808, pads aireados | A Minor | 140 |
| `drum-and-bass-ligero` | Liquid drum and bass, breaks, pads cálidos | A Minor | 170 |
| `techno-minimal` | Techno minimal, hipnótico, kick marcado | A Minor | 124 |
| `house-alegre` | Piano house, palmas, acordes brillantes | C Major | 124 |
| `tech-house` | Bajo rodante, percusión nítida, minimal | A Minor | 125 |
| `edm-energico` | EDM, build grande, lead brillante, energía de festival | A Minor | 128 |
| `electropop` | Electropop instrumental, bajo sintético, arpegios | G Major | 112 |
| `downtempo` | Trip hop, vinilo, bajo cálido, ahumado | A Minor | 90 |
| `chillwave` | Sintetizadores brumosos, onírico, cálido | G Major | 90 |
| `future-garage` | Beats con shuffle, pads atmosféricos, sub bajo | A Minor | 130 |
| `chiptune-alegre` | 8-bit, saltarín, juego retro | C Major | 130 |
| `funk-suave` | Guitarra limpia, bajo slap, palmas | E Minor | 104 |
| `disco` | Nu disco, bajo groovy, cuerdas | A Minor | 118 |
| `boom-bap` | Batería polvorienta, piano sampleado, clásico | A Minor | 90 |
| `rnb-suave` | R&B suave, Rhodes, batería suave, nocturno | D Minor | 82 |
| `rock-motivacional` | Guitarras que empujan, batería potente, himno | E Minor | 120 |
| `indie-pop` | Guitarras jangly, palmas, brillante | G Major | 118 |
| `post-rock-suave` | Guitarras con delay, crecimiento lento, atmosférico | D Major | 96 |

## Usos concretos

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `navidad-suave` | Cascabeles, glockenspiel, piano suave | C Major | 90 |
| `infantil` | Xilófono, ukulele, alegre | C Major | 110 |
| `juego-casual` | Juego móvil casual, marimba, saltarín | G Major | 112 |
| `entrenamiento` | Electrónica enérgica, beat constante, intenso | A Minor | 135 |
| `noticias` | Cama de noticiero, sintetizador pulsante, neutral | A Minor | 112 |
| `cocina` | Guitarra jazzera ligera, cálido, animado | G Major | 100 |
| `vlog-viaje` | Indie acústico animado, silbido, palmas | G Major | 110 |
