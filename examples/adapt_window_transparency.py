import i3ipc

ipc = i3ipc.Connection()

w_to_opac = {w.id: 1 for w in ipc.get_tree()}


def update_call(ipc, __):
    global w_to_opac
    w_to_opac = {w.id: 1 for w in ipc.get_tree()}
    for w in ipc.get_tree():
        if w.id not in w_to_opac:
            w_to_opac[w.id] = 1


def on_binding_call(ipc, binding_event):

    sequence = '+'.join(binding_event.binding.mods +
                        binding_event.binding.symbols)

    def minus_func(x):
        if w_to_opac[x.id] > 0:
            w_to_opac[x.id] -= .1
        return str(w_to_opac[x.id])

    def plus_func(x):
        if w_to_opac[x.id] < 1:
            w_to_opac[x.id] += .1
        return str(w_to_opac[x.id])

    def equal_func(x):
        w_to_opac[x.id] = 1
        return str(w_to_opac[x.id])

    lamb = None
    if sequence == 'Mod4+minus':
        lamb = minus_func
    if sequence == 'Mod4+plus':
        lamb = plus_func
    if sequence == 'Mod4+equal':
        lamb = equal_func

    for window in ipc.get_tree():
        if window.focused and lamb:
            window.command('opacity '+lamb(window))


ipc.on("binding::run", on_binding_call)
ipc.on("window::new", update_call)
ipc.main()
