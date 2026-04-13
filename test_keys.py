import questionary
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings

bindings = KeyBindings()

@bindings.add(Keys.Escape)
def _(event):
    # This will exit the prompt and return None
    event.app.exit(result=None)

try:
    # Does questionary accept keybindings kwarg?
    # Some wrappers do, but questionary often uses custom kwargs passed to prompt() 
    # Actually, questionary 1.0+ accepts `key_bindings` kwarg? Let's check? No, questionary 2.1.1 might accept it.
    pass
except Exception as e:
    pass
