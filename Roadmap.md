# Roadmap de conversion a Qt/Python con PyQt6

Ultima actualizacion: 2026-05-02.

Este archivo debe servir como relevo para continuar la migracion en otra sesion.
Antes de tocar codigo, leer especialmente las secciones:

- `Estado actual al cierre`
- `Como verificar rapidamente`
- `Siguiente sesion: tareas concretas`
- `Limitaciones conocidas`

Este repositorio contiene dos proyectos C++/Qt que deben convivir durante la
conversion:

- `drumstick-2.11.0`: biblioteca MIDI para Qt. En Python queda como paquete
  `drumstick_py` dentro de la misma carpeta.
- `dmidiplayer`: reproductor que depende de Drumstick. En Python queda como
  paquete `dmidiplayer_py` dentro de la misma carpeta.

La conversion debe hacerse por capas. Primero se porta `drumstick_py`, luego se
conecta `dmidiplayer_py` contra esa API Python. El C++ original se conserva
como referencia hasta que cada modulo tenga paridad funcional y pruebas.

## Estado actual al cierre

Ya se creo una base Python ejecutable y se mantiene dentro de las carpetas de
cada proyecto, sin borrar ni sustituir el C++ original.

- `drumstick-2.11.0/drumstick_py/`
  - `file.py`: lector SMF inicial, sin dependencias externas, con mapa de
    tempo, duracion real y metadatos basicos.
  - `rt.py`: `BackendManager`, salida dummy, diagnostico con
    `python3-alsaaudio`, salida ALSA sequencer inicial mediante `libasound`,
    listado de destinos ALSA y conexion por puerto.
  - `widgets.py`: `PianoKeyboard` PyQt6 inicial.
- `dmidiplayer/dmidiplayer_py/`
  - `app.py`: ventana PyQt6 inicial con lista, controles, posicion, teclado y
    selector de destino MIDI ALSA.
  - `sequence.py`: modelo que carga SMF desde `drumstick_py`.
  - `player.py`: reproductor temporizado con `QTimer` y reloj real basado en
    mapa de tempo.
  - `__main__.py`: entrada `python3 -m dmidiplayer_py`.
- `dmidiplayer/dmidiplayer-py`: script lanzador local que configura
  `PYTHONPATH`.
- `tests/test_smf_parser.py`: prueba `unittest` minima que genera un SMF y
  valida note on/off, tempo y final de pista.
- `tests/test_alsa_event.py`: prueba minima para validar el armado de eventos
  SysEx ALSA con longitud variable.

Estado funcional:

- `./dmidiplayer/dmidiplayer-py --help` funciona.
- La ventana PyQt6 arranca.
- Se pueden cargar archivos `.mid`, `.midi` y `.kar` siempre que sean SMF
  legibles por el parser inicial.
- El parser calcula mapa de tempo, compas, armadura, textos y duracion real.
- El reproductor temporizado emite eventos a la salida configurada usando los
  tiempos reales derivados del mapa de tempo.
- La app intenta abrir ALSA sequencer primero.
- Si ALSA sequencer falla, la app cae a salida dummy y sigue abriendo la UI.
- `python3-alsaaudio` se usa solo como diagnostico de tarjetas/PCM. No sirve
  para ALSA sequencer MIDI porque el paquete no expone esa API.
- El envio MIDI ALSA real se implemento con `ctypes` sobre `libasound.so.2`.
- Los eventos SysEx ALSA se marcan como longitud variable; esto evita
  `Argumento invalido` al reproducir archivos como `examples/test.mid`.
- La UI lista destinos ALSA y puede conectar la salida directamente a QSynth,
  FluidSynth u otro puerto MIDI compatible. Si detecta QSynth/FluidSynth al
  arrancar, intenta autoconectarse.
- Se creo `README.md` en la raiz con notas de prueba en MX Linux 23, kernel RT,
  QjackCtl, QSynth y `FluidR3.sf2`.

Ejecucion actual:

```bash
./dmidiplayer/dmidiplayer-py archivo.mid
```

La salida MIDI real ALSA ya tiene una primera implementacion. Si ALSA sequencer
no esta disponible, la aplicacion cae automaticamente a salida dummy para validar
parser, UI y temporizacion.

Para que ALSA sequencer funcione debe existir `/dev/snd/seq`. En Debian suele
activarse con el modulo del kernel `snd-seq`; se puede comprobar con:

```bash
aconnect -lo
```

Si `aconnect -lo` falla con `open /dev/snd/seq failed`, cargar el modulo:

```bash
sudo modprobe snd-seq
```

Despues de lanzar `dmidiplayer-py`, se puede conectar el puerto ALSA desde la
propia UI con el selector `Destino MIDI`. `aconnect` sigue siendo util para
diagnostico manual.

## Como verificar rapidamente

Desde la raiz del repo:

```bash
./dmidiplayer/dmidiplayer-py --help
PYTHONPATH=drumstick-2.11.0:dmidiplayer python3 -m compileall drumstick-2.11.0/drumstick_py dmidiplayer/dmidiplayer_py
PYTHONPATH=drumstick-2.11.0:dmidiplayer python3 -m unittest tests.test_smf_parser tests.test_alsa_event
QT_QPA_PLATFORM=offscreen timeout 2s ./dmidiplayer/dmidiplayer-py
```

Notas sobre estas pruebas:

- El comando offscreen debe terminar por `timeout` porque la app queda abierta;
  eso es normal.
- Si en el entorno no existe `/dev/snd/seq`, aparecera un mensaje de ALSA y la
  app usara dummy. Eso no es fallo de importacion.
- Despues de `compileall`, se pueden borrar los `__pycache__` generados.

Prueba manual con ALSA real:

```bash
aconnect -lo
./dmidiplayer/dmidiplayer-py archivo.mid
aconnect -lo
```

En otra terminal, conectar el puerto de `dmidiplayer PyQt6` a FluidSynth,
hardware MIDI, QSynth u otro sintetizador ALSA.

## Limitaciones conocidas

- El parser SMF inicial ya calcula tempo y duracion real para SMF PPQ, pero aun
  necesita mas pruebas de borde y comparacion contra Drumstick C++.
- El scheduler de `dmidiplayer_py.player` ya usa tiempos reales, pero sigue
  dependiendo de `QTimer`; aun no implementa seek, loop ni compensacion avanzada
  de latencia.
- La salida ALSA envia eventos directos a suscriptores, pero todavia no lista ni
  conecta destinos por nombre desde la UI.
- La UI PyQt6 actual es una ventana minima, no una conversion completa de
  `guiplayer.ui`.
- No se han portado todavia canales, playlist completa, loop, letras, pianola
  completa, preferencias ni ayuda.
- RIFF MIDI y Cakewalk WRK aun no estan portados.
- `uchardet` aun no esta conectado al parser Python.
- Hay una prueba automatizada minima para SMF; falta ampliar cobertura.

## Siguiente sesion: tareas concretas

Prioridad recomendada para continuar:

1. Ampliar pruebas de `drumstick_py.file`:
   - formato 1 multipista;
   - running status;
   - sysex;
   - cambios de tempo multiples;
   - compas, armadura, lyrics y markers.
2. Mejorar `drumstick_py.rt`:
   - mostrar conexiones activas y desconectar/reconectar destinos;
   - conectar por busqueda de nombre mas flexible desde preferencias;
   - exponer errores ALSA sin escribir demasiado en stderr;
   - verificar tamano/layout de `snd_seq_event_t` con una prueba pequena.
3. Agregar seek basico en `SequencePlayer` y conectar el slider de posicion.
4. Empezar la conversion de UI real:
   - decidir si se usara `pyuic6` o `PyQt6.uic.loadUi`;
   - cargar `guiplayer.ui`;
   - conectar acciones basicas contra el `SequencePlayer` Python.

No repetir:

- No buscar bindings de `python3-alsaaudio` para MIDI sequencer: ya se reviso y
  solo expone PCM/mixer.
- No borrar C++ original; sigue siendo referencia.
- No mover los paquetes Python fuera de sus carpetas actuales.
- No introducir dependencias de `pip` sin necesidad fuerte.

## Dependencias Debian 12

Ya instaladas por el usuario:

- `python3-pyqt6`
- `uchardet`
- `pandoc`
- `python3-alsaaudio`

Paquetes recomendados para pruebas reales de sonido:

- `alsa-utils`: trae `aconnect`. En el entorno revisado ya existe
  `/usr/bin/aconnect`.
- `fluidsynth`: sintetizador software para escuchar salida MIDI.
- `fluid-soundfont-gm`: soundfont General MIDI comun en Debian.

Paquetes que el usuario indico que estan disponibles para instalar si hicieran
falta:

- `python3-audioread`
- `python3-pydub`
- `python-soundfile-doc`
- `python3-pyao`
- `python3-pymad`
- `python-mutagen-doc`
- `python3-soundfile`
- `python3-mediafile`
- `python3-ecasound`
- `python3-jack-client`
- `python3-aubio`

Evaluacion de esos paquetes para este proyecto:

- `python3-jack-client` podria ser util mas adelante si se porta soporte JACK.
- `python3-soundfile`, `python3-pydub` y `python3-audioread` solo serian utiles
  si se agrega renderizado/exportacion de audio, no para MIDI realtime.
- `python3-aubio` sirve para analisis de audio, no es prioridad.
- `python3-pymad`, `python3-mediafile`, `python-mutagen-doc`, `python3-pyao` y
  `python3-ecasound` no son necesarios para la ruta actual de dmidiplayer.

Dependencias recomendadas para fases posteriores:

- `python3-pyqt6.qtmultimedia`, si se decide usar Qt Multimedia para audio.
- `python3-alsaaudio`, ya instalado, queda como diagnostico PCM/mixer.
- `fluidsynth` y, si esta disponible en repositorios, bindings Python para
  FluidSynth; si no, usar `ctypes` sobre `libfluidsynth`.
- `python3-pytest` para pruebas unitarias.
- `python3-pytestqt`, si se desea automatizar widgets PyQt6.

No introducir paquetes de `pip` salvo que sea inevitable. La prioridad es usar
paquetes de Debian 12.

## Fase 1: base Python y compatibilidad de estructura

Estado: iniciada y usable como esqueleto.

- Mantener el C++ original sin borrar archivos.
- Usar paquetes Python paralelos:
  - `drumstick-2.11.0/drumstick_py`
  - `dmidiplayer/dmidiplayer_py`
- Mantener nombres de clases cercanos a los originales cuando ayude:
  - `BackendManager`
  - `Sequence`
  - `SequencePlayer`
  - `PianoKeyboard`
- Crear scripts de ejecucion locales, sin instalacion global al principio.
- Confirmar que `python3 -m compileall` pasa en ambos paquetes.
- Confirmar que `./dmidiplayer/dmidiplayer-py --help` funciona.

## Fase 2: Drumstick File

Estado: iniciada. Hay lector SMF basico en `drumstick_py/file.py`.

Objetivo: reemplazar `library/file` en Python.

Tareas:

- Completar lector SMF:
  - tempo `0x51`
  - compas `0x58`
  - armadura `0x59`
  - textos, lyrics, markers y cue points
  - sysex completo
  - running status ya iniciado, ampliar pruebas de borde
  - duracion real en microsegundos considerando cambios de tempo
- Agregar escritor SMF si alguna utilidad lo requiere.
- Portar RIFF MIDI desde `rmid.cpp`.
- Portar Cakewalk WRK desde `qwrk.cpp`.
- Integrar deteccion de codificacion:
  - usar `uchardet` mediante comando externo o binding `ctypes`
  - mapear codificaciones a codecs Python
  - conservar comportamiento de letras karaoke
- Definir excepciones Python equivalentes a errores de carga C++.
- Crear fixtures MIDI pequenos para pruebas:
  - formato 0
  - formato 1 multipista
  - karaoke `.kar`
  - archivo con sysex
  - archivo con cambios de tempo

Criterios de salida:

- `drumstick_py.file.read_smf()` devuelve eventos ordenables por tick.
- La duracion y metadatos coinciden con dmidiplayer C++ en archivos de prueba.
- Los errores de archivo se reportan sin cerrar la aplicacion.

## Fase 3: Drumstick RT

Estado: iniciada. Hay salida dummy y primera salida ALSA sequencer en
`drumstick_py/rt.py`.

Objetivo: reemplazar `library/rt` y backends necesarios para Debian 12.

Prioridad Linux/Debian:

- ALSA sequencer output.
- ALSA sequencer input, si se necesita para utilidades como vpiano.
- FluidSynth output.
- Dummy output para pruebas.

Tareas:

- Disenar interfaz Python estable:
  - `MIDIOutput.open()`
  - `MIDIOutput.close()`
  - `MIDIOutput.send_event()`
  - `MIDIOutput.all_notes_off()`
  - `BackendManager.output_drivers()`
  - `BackendManager.connections()`
- Investigar si Debian 12 ofrece bindings ALSA suficientes.
- `python3-alsaaudio` cubre PCM/mixer, pero no ALSA sequencer MIDI. Usarlo para
  diagnostico y mantener la capa MIDI con `ctypes` sobre `libasound.so`.
- Portar conversion de eventos MIDI a mensajes raw.
- Implementar listado de puertos y conexion por nombre.
- Implementar reset GM/GS/XG si dmidiplayer lo requiere.
- Mantener backend dummy para pruebas automatizadas.

Criterios de salida:

- dmidiplayer Python puede enviar notas a un puerto ALSA visible.
- dmidiplayer Python puede usar FluidSynth si esta disponible.
- `all_notes_off` funciona al detener, pausar, cerrar y cambiar de archivo.

## Fase 4: Drumstick Widgets

Estado: iniciada solo con `PianoKeyboard` minimo.

Objetivo: reemplazar `library/widgets`.

Tareas:

- Completar `PianoKeyboard`:
  - teclas negras
  - rango configurable
  - colores por canal/estado
  - eventos de mouse/teclado si vpiano lo necesita
- Portar dialogos de configuracion:
  - FluidSynth
  - Network
  - Sonivox solo si se mantiene soporte
  - MacSynth no es prioridad en Debian
- Portar `SettingsFactory`.
- Reusar `.ui` existentes con `pyuic6` o cargar con `PyQt6.uic`, segun sea mas
  mantenible.

Criterios de salida:

- Los widgets se pueden importar sin depender de dmidiplayer.
- Los dialogos guardan/restauran configuracion con `QSettings`.

## Fase 5: dmidiplayer Core

Estado: iniciada con `Sequence` y `SequencePlayer` minimos.

Objetivo: portar la logica C++ de dmidiplayer.

Tareas por archivo C++ original:

- `events.*`
  - crear jerarquia/dataclasses Python para eventos MIDI, tempo, beat y texto.
- `sequence.*`
  - usar `drumstick_py.file`
  - calcular tiempos reales con mapa de tempo
  - conservar textos, lyrics, marcadores, compases y armadura
  - portar busqueda de codec y metadatos
- `seqplayer.*`
  - reemplazar temporizador simple por scheduler preciso
  - respetar tempo, pitch shift, volumen, mute, lock y programas
  - implementar loop por compases/ticks
  - emitir senales PyQt equivalentes a las C++
- `settings.*`
  - portar constantes de aplicacion
  - usar `QSettings`
  - modo portable `--portable` y `--file`
- `instrumentset.*`
  - cargar nombres de instrumentos y bancos
- `recentfileshelper.*`
  - guardar y poblar menu recientes

Criterios de salida:

- Abrir, reproducir, pausar, detener y cambiar posicion funcionan con MIDI real.
- Los canales respetan mute, volumen, programa y bloqueo.
- El comportamiento de loop coincide con C++.

## Fase 6: dmidiplayer UI PyQt6

Estado: iniciada con ventana minima escrita a mano. La UI completa original aun
no esta portada.

Objetivo: portar todas las ventanas y dialogos.

Archivos `.ui` a convertir o cargar:

- `guiplayer.ui`
- `connections.ui`
- `loopdialog.ui`
- `playerabout.ui`
- `playlist.ui`
- `prefsdialog.ui`
- `toolbareditdialog.ui`

Widgets/vistas C++ a portar:

- `channels.*`
- `connections.*`
- `framelesswindow.*`
- `helpwindow.*`
- `lyrics.*`
- `pianola.*`
- `playlist.*`
- `prefsdialog.*`
- `rhythmview.*`
- `toolbareditdialog.*`
- `vumeter.*`

Tareas:

- Convertir `.qrc` a recursos Python o resolver iconos desde rutas locales.
- Reusar iconos existentes en `dmidiplayer/icons`.
- Portar menus, toolbars y acciones.
- Implementar drag and drop de archivos.
- Implementar dialogo de conexiones usando `BackendManager`.
- Implementar preferencias completas.
- Implementar playlist con repeticion y aleatorio.
- Implementar lyrics y karaoke sincronizado.
- Implementar pianola y vista ritmica.
- Implementar ayuda usando los markdown convertidos con `pandoc` cuando aplique.

Criterios de salida:

- La UI Python permite los mismos flujos principales que la C++.
- No quedan botones principales conectados a placeholders.
- La aplicacion cierra sin dejar notas sonando.

## Fase 7: traducciones y documentacion

Tareas:

- Revisar `.ts` existentes.
- Decidir si se conservan traducciones Qt Linguist (`.qm`) con PyQt6.
- Portar carga de idioma dinamica.
- Regenerar ayuda/manpages con `pandoc`.
- Documentar ejecucion Python en `README.md`.
- Mantener notas de diferencias respecto al C++ mientras dure la migracion.

Criterios de salida:

- Espanol e ingles funcionan en la UI Python.
- La ayuda abre desde la aplicacion.

## Fase 8: utilidades de Drumstick

Prioridad despues de dmidiplayer:

- `utils/playsmf`
- `utils/dumpsmf`
- `utils/dumpmid`
- `utils/dumprmi`
- `utils/dumpwrk`
- `utils/sysinfo`
- `utils/metronome`
- `utils/vpiano`
- `utils/drumgrid`
- `utils/guiplayer`

Cada utilidad debe tener su propio paquete o modulo dentro de
`drumstick_py/utils`.

## Fase 9: pruebas

Estado: pendiente. Solo se han hecho verificaciones manuales de importacion,
compilacion y arranque offscreen.

Pruebas minimas:

- Parser SMF:
  - cabecera invalida
  - evento meta
  - running status
  - sysex
  - tempo
  - formato 0 y 1
- Scheduler:
  - orden de eventos
  - tempo variable
  - loop
  - stop/all notes off
- UI:
  - abre ventana principal
  - carga archivo
  - cambia estado play/pause/stop
  - dialogo conexiones lista backends

Comandos esperados:

```bash
PYTHONPATH=drumstick-2.11.0:dmidiplayer python3 -m compileall drumstick-2.11.0/drumstick_py dmidiplayer/dmidiplayer_py
PYTHONPATH=drumstick-2.11.0:dmidiplayer python3 -m dmidiplayer_py --help
```

## Fase 10: empaquetado local

Tareas:

- Crear `pyproject.toml` si se decide instalar como paquete.
- Crear scripts:
  - `dmidiplayer-py`
  - utilidades `drumstick-*`
- Evaluar instalacion en `/usr/local` solo al final.
- Crear archivo `.desktop` para version Python.
- Asegurar que recursos, iconos y traducciones se encuentren desde instalacion
  y desde arbol fuente.

## Orden recomendado de trabajo

1. Ampliar pruebas automatizadas para parser y scheduler.
2. Completar `drumstick_py.rt` con listado/conexion de puertos ALSA.
3. Agregar seek basico en `SequencePlayer`.
4. Portar `settings`, `sequence` y `events` con paridad C++.
5. Convertir/cargar `.ui` y conectar acciones reales.
6. Portar canales, lyrics, playlist, loop, pianola y ritmo.
7. Portar preferencias, conexiones, ayuda y traducciones.
8. Portar utilidades Drumstick restantes.
9. Preparar empaquetado e instalacion.

## Archivos Python creados hasta ahora

- `drumstick-2.11.0/drumstick_py/__init__.py`
- `drumstick-2.11.0/drumstick_py/file.py`
- `drumstick-2.11.0/drumstick_py/rt.py`
- `drumstick-2.11.0/drumstick_py/widgets.py`
- `dmidiplayer/dmidiplayer_py/__init__.py`
- `dmidiplayer/dmidiplayer_py/__main__.py`
- `dmidiplayer/dmidiplayer_py/app.py`
- `dmidiplayer/dmidiplayer_py/player.py`
- `dmidiplayer/dmidiplayer_py/sequence.py`
- `dmidiplayer/dmidiplayer-py`
- `tests/test_smf_parser.py`
- `tests/test_alsa_event.py`

## Detalle tecnico del estado actual

`drumstick_py.file`:

- Lee cabecera `MThd`.
- Lee tracks `MTrk`.
- Soporta variable-length quantities.
- Soporta running status basico.
- Clasifica eventos de canal:
  - `note_off`
  - `note_on`
  - `key_pressure`
  - `control_change`
  - `program_change`
  - `channel_pressure`
  - `pitch_bend`
- Guarda meta eventos como `kind="meta"` con `meta_type`.
- Guarda sysex como `kind="sysex"`.
- Expone mapa de tempo con `TempoChange`.
- Expone metadatos basicos con `TimeSignature`, `KeySignature` y `TextEvent`.
- Calcula `length_microseconds`, `tick_to_microseconds()` y
  `microseconds_to_tick()`.
- Aun falta ampliar pruebas de borde y comparar duraciones/metadatos contra C++.

`drumstick_py.rt`:

- `DummyMidiOutput` guarda eventos en memoria.
- `AlsaSequencerOutput` abre `snd_seq_open("default", SND_SEQ_OPEN_OUTPUT)`.
- Crea un puerto `MIDI out` con capacidades de lectura/subscripcion para que
  otros clientes ALSA puedan suscribirse.
- Envia eventos directos con `snd_seq_event_output_direct`.
- Usa destino `SND_SEQ_ADDRESS_SUBSCRIBERS`.
- Marca SysEx con `SND_SEQ_EVENT_LENGTH_VARIABLE`.
- Lista puertos ALSA con `snd_seq_query_next_client` y
  `snd_seq_query_next_port`, filtrando destinos con `WRITE|SUBS_WRITE`.
- Conecta el puerto propio a destinos con `snd_seq_connect_to`.
- `all_notes_off()` envia controladores 123 y 120 en los 16 canales.
- Si falla ALSA, levanta `MidiOutputError`.

`dmidiplayer_py.player`:

- Carga `Sequence`.
- Avanza con `QTimer` preciso cada 2 ms y `QElapsedTimer`.
- Programa eventos segun los microsegundos calculados desde el mapa de tempo.
- Emite `positionChanged`, `eventPlayed`, `started`, `stopped`, `finished`.
- Aun falta seek, loop y compensacion avanzada de latencia.

`dmidiplayer_py.app`:

- Crea `BackendManager`.
- Intenta `create_output("alsa")`.
- Si falla, muestra mensaje en status bar y usa dummy.
- Tiene toolbar minima: abrir, reproducir, pausa, detener.
- Tiene lista de archivos, etiqueta de informacion, slider de posicion,
  teclado y etiqueta del ultimo evento.

## Notas tecnicas

- Evitar dependencias externas no disponibles en Debian 12.
- Preferir PyQt6 nativo sobre wrappers propios cuando Qt ya resuelve algo.
- Mantener el backend dummy siempre disponible para pruebas.
- No mezclar codigo C++ y Python en el mismo modulo; usar el C++ solo como
  referencia mientras se porta.
- Cualquier funcionalidad que todavia sea placeholder debe quedar marcada en
  este roadmap o con una excepcion clara en la UI.
