from utils.constants import BEFORE_CREATE


def note_hook(lifecycle, context, note, adapter, request):
    if lifecycle == BEFORE_CREATE:
        ...
