# Estilos de música disponibles (126)

Catálogo de presets de `python cli.py music`, definido en [styles.py](../../src/content_studio/music/styles.py). Se usan con `--style <nombre>`. Los 117 nuevos se generaron a 30 s con ACE-Step y pasaron `--evaluate` (sin voz, al menos 20 s, no mudos); cómo se probaron y qué se descartó está en [INVESTIGACION.md](INVESTIGACION.md). **Nadie escuchó las pistas**: las métricas no dicen si el estilo se reconoce ni si suena bien.

Todos van en compás 4/4. Tono y BPM se pueden pisar con `--key` y `--bpm`.

Presets que pasaron por poco en voz (entre −25 y −32 dB): `demo-product`, `heroic`, `suspense-tech`, `ambient-ocean`, `tutorial-tech`, `sci-fi`, `pop-bright`, `demo-saas`. Con ellos conviene `--evaluate --retries 2`.

Descartados por voz y no incluidos: `cinematico-epico` y `documental-historia`.

## Los 9 originales

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `lofi-chill` | Rhodes, vinilo, boom bap suave | C Major | 80 |
| `lofi-jazz` | Acordes de jazz, trompeta con sordina, escobillas | D Minor | 85 |
| `lofi-rain` | Piano melancólico, ambiente de lluvia | E Minor | 72 |
| `lofi-study` | Guitarra suave, groove relajado, minimal | G Major | 78 |
| `lofi-night` | Pads de sintetizador, sub bajo, ciudad de noche | A Minor | 70 |
| `corporate` | Fondo tech optimista, piano eléctrico, plucks | C Major | 110 |
| `future-bass` | Supersaw suaves, sidechain leve, brillante | G Major | 100 |
| `deep-house` | Groove cálido, bajo redondo, elegante | A Minor | 120 |
| `ambient` | Pads que evolucionan, sin batería | D Major | 70 |

## Tutoriales y explicativos

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `tutorial-calm` | Piano suave, pad cálido, pluck ligero | C Major | 90 |
| `tutorial-tech` | Plucks de sintetizador, piano eléctrico, beat minimal | G Major | 100 |
| `tutorial-guitar` | Guitarra fingerstyle, shaker suave | G Major | 95 |
| `explainer-animated` | Marimba juguetona, pizzicato, palmas ligeras | C Major | 115 |
| `explainer-minimal` | Motivo de piano, sub bajo suave, pad aireado | D Major | 85 |
| `course-online` | Kalimba, piano suave, pad cálido | C Major | 88 |
| `step-by-step` | Pulso suave y constante, pluck apagado | A Minor | 100 |
| `codigo` | Electrónica ambient, arpegio suave, pad profundo | D Minor | 92 |
| `documentary-soft` | Piano y cuerdas suaves, reflexivo | D Major | 76 |

## Corporativo y publicidad

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `corporate-inspiring` | Guitarra acústica, piano, palmas suaves | C Major | 112 |
| `corporate-minimal` | Piano suave, cuerdas sutiles, limpio | G Major | 100 |
| `corporate-energetic` | Guitarras brillantes, palmas con pegada | D Major | 124 |
| `corporate-startup` | Glockenspiel, sintetizador ligero, chasquidos | G Major | 118 |
| `corporate-trust` | Cuerdas cálidas, piano, crecimiento lento | C Major | 84 |
| `corporate-innovation` | Sintetizador pulsante, bajo limpio, futurista | A Minor | 108 |
| `corporate-motivational` | Crescendo cinematográfico, piano, cuerdas, batería | D Major | 100 |
| `ad-happy` | Ukulele, silbido, palmas | C Major | 120 |
| `ad-premium` | Bajo profundo, sintetizador brillante, elegante | A Minor | 95 |
| `ad-fashion` | Groove deep house, pasarela, sofisticado | A Minor | 122 |
| `ad-sports` | Batería potente, guitarras rock, palmas de estadio | E Minor | 130 |
| `ad-food` | Acústico cálido, guitarra jazzera, café | G Major | 108 |
| `ad-launch` | Sintetizadores en crescendo, impactos, riser | A Minor | 118 |
| `ad-fintech` | Pluck limpio, kick suave, seguro y pulido | C Major | 104 |
| `ad-realestate` | Piano cálido, cuerdas suaves, aspiracional | D Major | 80 |
| `ad-health` | Piano suave, cuerdas ligeras, calmado | G Major | 76 |
| `ad-travel` | Guitarra acústica, percusión de mano, aventurero | D Major | 110 |
| `ad-car` | Bajo sintético potente, beat constante, cinematográfico | E Minor | 112 |

## Demos y tecnología

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `demo-product` | Electrónica limpia, bajo saltarín, palmas ligeras | G Major | 108 |
| `demo-saas` | Plucks burbujeantes, beat suave, ordenado | C Major | 110 |
| `demo-mobile-app` | Plucks juguetones, percusión ligera, fresco | D Major | 114 |
| `demo-futuristic` | Campanas cristalinas, pulsos graves, sci-fi | A Minor | 100 |
| `demo-ai` | Electrónica ambient, arpegios que evolucionan | E Minor | 96 |
| `demo-gadget` | Beat nítido, bajo funky, con estilo | A Minor | 105 |
| `demo-shop` | Pop instrumental, palmas, brillante | C Major | 118 |
| `demo-dashboard` | Techno minimal constante, pad suave, analítico | A Minor | 112 |
| `demo-game` | Lead chiptune, bajo marcado, juguetón | C Major | 125 |

## Lofi (nuevos)

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `lofi-cafe` | Lofi jazz hop, piano cálido, escobillas, cafetería | C Major | 82 |
| `lofi-guitar` | Guitarra eléctrica suave, batería polvorienta | A Minor | 76 |
| `lofi-sunset` | Chillhop, pads cálidos, kick suave | G Major | 84 |
| `lofi-nostalgic` | Piano nostálgico, campanas suaves, hiss de cinta | E Minor | 76 |
| `lofi-bossa` | Bossa nova lofi, guitarra de nylon, shaker | D Minor | 88 |
| `chillhop-focus` | Teclas jazzeras, boom bap, contrabajo | D Minor | 90 |
| `lofi-piano` | Piano solo lofi, hiss de cinta, íntimo | C Major | 68 |
| `vaporwave` | Ralentizado, sintetizador onírico, retro | G Major | 80 |

## Ambient, foco y bienestar

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `ambient-space` | Drone espacial, pads brillantes, sin batería | D Major | 60 |
| `ambient-piano` | Piano ambient, reverb suave, contemplativo | C Major | 64 |
| `ambient-cinematic` | Pads amplios, drone grave, swells sutiles | A Minor | 60 |
| `ambient-forest` | Pads suaves, campanas, atmósfera de bosque | G Major | 62 |
| `ambient-ocean` | Pads lentos, textura de olas, vasto | D Major | 58 |
| `meditation` | Cuencos tibetanos, pads suaves, lento | C Major | 60 |
| `yoga` | New age, flauta, arpa, fluido | D Major | 66 |
| `spa` | Arpa suave, piano, pad cálido | G Major | 64 |
| `sleep` | Pads muy suaves, lento, onírico | C Major | 52 |
| `deep-focus` | Drone minimal, pulso sutil, concentración | A Minor | 70 |
| `new-age` | Pads de sintetizador, campanas de cristal, sereno | G Major | 68 |
| `ambient-dark` | Drones graves, tensión lenta, minimal | D Minor | 60 |

## Cinematográfico

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `cinematic-emotional` | Piano, cuerdas, crecimiento sentido | D Minor | 72 |
| `cinematic-hope` | Cuerdas, piano, inspirador | D Major | 90 |
| `trailer-tension` | Sintetizadores pulsantes, metales graves, risers | A Minor | 110 |
| `cinematic-minimal` | Ostinato de piano, cuerdas suaves | A Minor | 84 |
| `documentary-nature` | Orquestal majestuoso, cuerdas amplias, trompa | G Major | 76 |
| `heroic` | Trompas, redoble de caja, triunfal | C Major | 108 |
| `mystery` | Cuerdas pulsadas, piano suave, suspenso | E Minor | 84 |
| `suspense-tech` | Pulso de sintetizador oscuro, bajo profundo | E Minor | 100 |
| `sci-fi` | Sintetizadores analógicos, espacial, asombro | A Minor | 90 |
| `fantasy` | Arpa, flauta, cuerdas, mágico | D Major | 88 |
| `orchestra-warm` | Orquesta de cámara, cuerdas, maderas | G Major | 80 |
| `piano-emotional` | Piano solo, íntimo, expresivo | A Minor | 66 |
| `strings-minimal` | Cuarteto de cuerdas, minimalista, patrón repetido | D Major | 84 |
| `neoclassical` | Piano, violonchelo, ambient, reflexivo | D Minor | 68 |

## Acústico y folk

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `acoustic-happy` | Ukulele, palmas, silbido, soleado | C Major | 118 |
| `acoustic-warm` | Guitarra acústica cálida, percusión suave | G Major | 92 |
| `folk-soft` | Indie folk, guitarra con púa de dedos, mandolina | D Major | 100 |
| `country-soft` | Country ligero, slide guitar, escobillas | G Major | 96 |
| `piano-pop` | Piano pop instrumental, batería suave, esperanzador | C Major | 100 |
| `ukulele-beach` | Ukulele, playa, percusión ligera, tropical | C Major | 108 |
| `guitar-classical` | Guitarra de nylon solista, elegante | A Minor | 90 |
| `harp-celestial` | Arpa, cuerdas suaves, etéreo | D Major | 72 |
| `celtic` | Tin whistle, violín, bodhrán, folk | D Major | 96 |

## Jazz, latino y del mundo

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `jazz-cafe` | Trío de piano, escobillas, contrabajo, swing relajado | G Major | 100 |
| `jazz-soft` | Smooth jazz, saxofón, piano eléctrico | D Minor | 90 |
| `bossa-nova` | Guitarra de nylon, percusión suave, soleado | D Minor | 100 |
| `lounge` | Vibráfono, contrabajo, escobillas, nocturno | A Minor | 80 |
| `swing-happy` | Swing animado, clarinete, bajo caminante, vintage | C Major | 140 |
| `latin-soft` | Latin pop instrumental, guitarra de nylon, congas | A Minor | 100 |
| `cumbia-soft` | Cumbia suave, güiro, bajo, tropical | A Minor | 92 |
| `reggae-chill` | Reggae, guitarra a contratiempo, órgano, relajado | G Major | 80 |
| `afrobeat-light` | Guitarras percusivas, groove cálido | G Major | 108 |
| `tropical-house` | Marimba, plucks, groove veraniego | A Minor | 110 |

## Electrónica y pop

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `pop-bright` | Pop instrumental, palmas, plucks de sintetizador | C Major | 120 |
| `synthwave` | Retro 80s, arpegios analógicos, batería gated | E Minor | 105 |
| `retrowave-soft` | Sintetizadores retro suaves, caja de ritmos, neón | A Minor | 95 |
| `trap-soft` | Trap suave, 808, pads aireados | A Minor | 140 |
| `drum-and-bass-light` | Liquid drum and bass, breaks, pads cálidos | A Minor | 170 |
| `techno-minimal` | Techno minimal, hipnótico, kick marcado | A Minor | 124 |
| `house-happy` | Piano house, palmas, acordes brillantes | C Major | 124 |
| `tech-house` | Bajo rodante, percusión nítida, minimal | A Minor | 125 |
| `edm-energetic` | EDM, build grande, lead brillante, energía de festival | A Minor | 128 |
| `electropop` | Electropop instrumental, bajo sintético, arpegios | G Major | 112 |
| `downtempo` | Trip hop, vinilo, bajo cálido, ahumado | A Minor | 90 |
| `chillwave` | Sintetizadores brumosos, onírico, cálido | G Major | 90 |
| `future-garage` | Beats con shuffle, pads atmosféricos, sub bajo | A Minor | 130 |
| `chiptune-happy` | 8-bit, saltarín, juego retro | C Major | 130 |
| `funk-soft` | Guitarra limpia, bajo slap, palmas | E Minor | 104 |
| `disco` | Nu disco, bajo groovy, cuerdas | A Minor | 118 |
| `boom-bap` | Batería polvorienta, piano sampleado, clásico | A Minor | 90 |
| `rnb-soft` | R&B suave, Rhodes, batería suave, nocturno | D Minor | 82 |
| `rock-motivational` | Guitarras que empujan, batería potente, himno | E Minor | 120 |
| `indie-pop` | Guitarras jangly, palmas, brillante | G Major | 118 |
| `post-rock-soft` | Guitarras con delay, crecimiento lento, atmosférico | D Major | 96 |

## Usos concretos

| Preset | Descripción | Tono | BPM |
|:--|:--|:--|:--|
| `christmas-soft` | Cascabeles, glockenspiel, piano suave | C Major | 90 |
| `kids` | Xilófono, ukulele, alegre | C Major | 110 |
| `casual-game` | Juego móvil casual, marimba, saltarín | G Major | 112 |
| `workout` | Electrónica enérgica, beat constante, intenso | A Minor | 135 |
| `news` | Cama de noticiero, sintetizador pulsante, neutral | A Minor | 112 |
| `cooking` | Guitarra jazzera ligera, cálido, animado | G Major | 100 |
| `vlog-travel` | Indie acústico animado, silbido, palmas | G Major | 110 |
