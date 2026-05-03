# dmidiplayer PyQt6 port

Este repositorio contiene una conversion progresiva de Drumstick/dmidiplayer a
Qt/Python con PyQt6. El codigo C++ original se conserva como referencia y la
version Python vive en paquetes paralelos dentro del mismo arbol:

- `drumstick/drumstick_py`
- `dmidiplayer/dmidiplayer_py`

## Entorno de pruebas actual

Las pruebas manuales se estan haciendo en MX Linux 23.

En ese sistema se instalo el kernel RT disponible en los mismos repositorios de
MX Linux 23 y se configuro junto con los paquetes indicados para esta migracion,
incluyendo PyQt6, ALSA y utilidades MIDI.

Para escuchar la salida MIDI real se instalo tambien:

- QjackCtl
- QSynth
- `fluid-soundfont-gm`

La fuente de sonido usada para las pruebas es `FluidR3.sf2`, instalada por el
paquete `fluid-soundfont-gm`. Esta fuente se cargo en QSynth desde la
configuracion `Soundfonts`.

Con QjackCtl activo y QSynth abierto, dmidiplayer PyQt6 puede enviar eventos por
ALSA sequencer hacia QSynth. La aplicacion tambien incluye un selector de
destinos MIDI ALSA para conectar la salida directamente desde la interfaz.

## Dependencias

Dependencias necesarias hasta el momento en MX Linux 23/Debian 12:

```bash
sudo apt install python3-pyqt6 python3-alsaaudio alsa-utils
```

Para escuchar MIDI con buena calidad usando QSynth/FluidSynth:

```bash
sudo apt install qjackctl qsynth fluidsynth fluid-soundfont-gm
```

Paquetes usados o previstos durante la migracion:

```bash
sudo apt install uchardet pandoc
```

Para ejecutar las pruebas actuales no hace falta `pytest`; se usa `unittest`,
incluido con Python. Mas adelante pueden ser utiles:

```bash
sudo apt install python3-pytest python3-pytestqt
```

Notas:

- `alsa-utils` aporta `aconnect`, util para comprobar puertos MIDI ALSA.
- `python3-alsaaudio` se usa solo para diagnostico PCM/tarjetas; la salida MIDI
  ALSA sequencer se implementa con `ctypes` sobre `libasound.so.2`.
- Para que ALSA sequencer funcione debe existir `/dev/snd/seq`. Si `aconnect
  -lo` falla con `open /dev/snd/seq failed`, normalmente hay que cargar el
  modulo `snd-seq`.
- `fluid-soundfont-gm` instala `FluidR3.sf2`, que se puede cargar en QSynth
  desde `Soundfonts`.

## Como probar

Para probar, usar uno de los `.mid` de `dmidiplayer/examples`, por ejemplo:

```bash
./dmidiplayer/dmidiplayer-py dmidiplayer/examples/test.mid
```

y aparecerá la ventana y sonando el programa:

![](vx_images/01-dmidiplayer_port-qt_py.png)

Tambien puedes probar con otros:

```bash
./dmidiplayer/dmidiplayer-py dmidiplayer/examples/Schubert_Standchen.mid
./dmidiplayer/dmidiplayer-py dmidiplayer/examples/haendel_hallelujah.mid
./dmidiplayer/dmidiplayer-py dmidiplayer/examples/mozart_aveverum.mid
```

Ejecuta esos comandos desde la raiz del proyecto:

```bash
cd /home/wachin/Dev/dmidiplayer-port-qt_py
./dmidiplayer/dmidiplayer-py dmidiplayer/examples/test.mid
```

Si QSynth ya esta abierto, la app intentara conectarse automaticamente a un
destino que parezca QSynth/FluidSynth. Si no lo hace, usa el selector `Destino
MIDI`, pulsa `Refrescar` y luego `Conectar`.

La toolbar actual incluye tambien controles iniciales de `Tono` y `Tempo`.
`Tono` permite transponer entre -12 y +12 semitonos, sin alterar el canal de
percusion GM 10. `Tempo` permite reproducir entre 50% y 200% de la velocidad
original.

## Verificacion rapida

```bash
./dmidiplayer/dmidiplayer-py --help
PYTHONPATH=drumstick:dmidiplayer python3 -m compileall drumstick/drumstick_py dmidiplayer/dmidiplayer_py tests
PYTHONPATH=drumstick:dmidiplayer python3 -m unittest tests.test_smf_parser tests.test_alsa_event tests.test_sequence_player
```
