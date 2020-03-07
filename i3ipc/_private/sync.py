from Xlib import display
from Xlib.protocol import event
from Xlib import X
import random


class Synchronizer:
    def __init__(self):
        self.display = display.Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        self.sync_atom = self.display.intern_atom('I3_SYNC')
        self.send_window = self.root.create_window(-10, -10, 10, 10, 0, self.screen.root_depth)

    def sync(self):
        rnd = random.randint(0, 2147483647)

        message = event.ClientMessage(window=self.root,
                                      data=([32, [self.send_window.id, rnd, 0, 0, 0]]),
                                      message_type=self.sync_atom,
                                      client_type=self.sync_atom,
                                      sequence_number=0)

        self.display.send_event(self.root, message, X.SubstructureRedirectMask)

        while True:
            e = self.display.next_event()
            if e.type == X.ClientMessage and e.client_type == self.sync_atom:
                fmt, data = e.data
                if data[0] == self.send_window.id and data[1] == rnd:
                    break
