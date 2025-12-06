# So you want to contribute a new backend?

Here are a few things you'll need:

# Step 1:
Create a new folder with the name of your backend in the backends directory and stick an empty `__init__.py` in that bad boy.

Next, add a file like `my_backend.py`

Let's look at what we need in said file:

# Step 2: Creating the basic backend file

Firstly, we need the meat of the backend, you can find details on how to do that [here](docs/backends/custom.md)

For this example let's call it `MyBackend`
```python
class MyBackend:

    def __init__(self, fruit1, fruit2):
        pass

    def get_led_count(self) -> int:
        pass

    def set_led(self, led_index: int, on: bool) -> None:
        pass

    def set_leds(self, buffer: list[list[int]]) -> None:
        raise AttributeError("Not yet implemented")
```

The only thing you'll need to do extra is add the dependencies to the `pyproject.toml` file

# Step 3: Add the helper methods

Next we need to add the helper methods so we can launch our backend from the command line 
with lots of lovely arguments

Firstly we need to add a method that adds all the arguments we'll need for our backend

```python
def my_backend_set_args(parser):
    parser.add_argument('--fruit_1', default="bananas")
    parser.add_argument('--fruit_2', default="oranges")
```

In this case, we're gonna feed it fruit 1 and fruit 2 from the argparser.

Next we need the backend factory.
This seems a bit tricky, but we are just packaging our backend constructor with all the arguments it needs to be created later.

```python
def my_backend_factory(args: argparse.Namespace):
    return partial(MyBackend, args.fruit_1, args.fruit_2)
```


# Step 4: Adding it to the list of known backends

In `marimapper/backends/backend_utils.py` there are two dictionaries, 
one with the factories, and the other with the arg setters.

Add your 

```python
from marimapper.backends.my_backend import my_backend

backend_factories = {
    ...
    "my_backend": my_backend.my_backend_factory,
}

backend_arg_setters = {
    ...
    "my_backend": my_backend.my_backend_set_args
}
```

# Step 5: Add the docs!

Add a new readme to the docs/backends folder and link it in the main README.md

# Step 6: Have a cuppa, you've earned it!

Congrats! you've now added a custom backend, now get that PR raised and let's get it supported!