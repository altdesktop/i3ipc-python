from Xlib import X, Xutil
from Xlib.display import Display
from threading import Thread


class Window(object):
    def __init__(self, display=None):
        if display is None:
            display = Display()

        self.d = display
        self.screen = self.d.screen()
        bgsize = 20
        bgpm = self.screen.root.create_pixmap(bgsize, bgsize, self.screen.root_depth)
        bggc = self.screen.root.create_gc(foreground=self.screen.black_pixel,
                                          background=self.screen.black_pixel)
        bgpm.fill_rectangle(bggc, 0, 0, bgsize, bgsize)
        bggc.change(foreground=self.screen.white_pixel)
        bgpm.arc(bggc, -bgsize // 2, 0, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, bgsize // 2, 0, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, 0, -bgsize // 2, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, 0, bgsize // 2, bgsize, bgsize, 0, 360 * 64)

        self.window = self.screen.root.create_window(100,
                                                     100,
                                                     400,
                                                     300,
                                                     0,
                                                     self.screen.root_depth,
                                                     X.InputOutput,
                                                     X.CopyFromParent,
                                                     background_pixmap=bgpm,
                                                     event_mask=(X.StructureNotifyMask
                                                                 | X.ButtonReleaseMask),
                                                     colormap=X.CopyFromParent)

        self.WM_DELETE_WINDOW = self.d.intern_atom('WM_DELETE_WINDOW')
        self.WM_PROTOCOLS = self.d.intern_atom('WM_PROTOCOLS')

        self.window.set_wm_name('i3 test window')
        self.window.set_wm_class('i3win', 'i3win')

        self.window.set_wm_protocols([self.WM_DELETE_WINDOW])
        self.window.set_wm_hints(flags=Xutil.StateHint, initial_state=Xutil.NormalState)

        self.window.set_wm_normal_hints(flags=(Xutil.PPosition | Xutil.PSize | Xutil.PMinSize),
                                        min_width=50,
                                        min_height=50)

        self.window.map()
        display.flush()

    def run(self):
        def loop():
            while True:
                e = self.d.next_event()

                if e.type == X.DestroyNotify:
                    break

                elif e.type == X.ClientMessage:
                    if e.client_type == self.WM_PROTOCOLS:
                        fmt, data = e.data
                        if fmt == 32 and data[0] == self.WM_DELETE_WINDOW:
                            self.window.destroy()
                            self.d.flush()
                            break

        Thread(target=loop).start()
