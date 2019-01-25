#!/usr/bin/python
"""
Perhaps a little ambitious, this will be a Scratch style Sprite Actor sim

Sprite 1
   image = cat:
   costumes = [
       ("costume1" : ... ),
       ("costume2" : ... ),
       ...
       ("costumeN" : ... ),
   ]
   sounds = [
       ("sound1" : "meow.wav" ),
       ("sound2" : "purr.wav"),
       ...
       ("costumeN" : "chirrup.wav" ),
   ]

class Sprite(...)
    image = ...

    @when_start
    def ...
       "when start is clicked:"

    @when_clicked
    def ...
       "when sprite 1 is clicked:"

    @when_I_receive
    def <event name>
       "when I receive (event):"
       "   broadcast (event)"
       "   broadcast (event) and wait (for what?)"

    @when_key_pressed("key?")  (value vs __call__ed value)
    def ...

Booleans:
   - touching (pointer, edge, another sprite)
   - touching (colour)
   - color (colour) is touching (colour)
   - ask (text) and wait (answer in "answer"...)
   - Attrs
       - answer
       - mousex
       - mousey
       - mousedown?
       - timer (since start/reset)
       - loudness
   - key <key> pressed ?
   - distance to <mousepointer, other sprite>
   - reset timer
   - {attr} of {sprite}
      - attr : x pos, y pos, direction, costume #, size, volume
      - sprite: any sprite
   - loud?
   - {sensor} sensor value
       - sensor: slide, light, sound, resistance A,resistance B,resistance C,resistance D, tilt, distance
   - sensor {button pressed}
       - button pressed: button pressed, A connected, B connected, C connected, D connected

"""











