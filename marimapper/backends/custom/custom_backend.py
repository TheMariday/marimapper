import argparse
import importlib.util
from functools import partial
from inspect import signature
from pathlib import Path
import os


def custom_backend_factory(args: argparse.Namespace):
    return partial(load_custom_backend, args.file)


def custom_backend_set_args(parser):
    parser.add_argument('file', type=Path, default=Path("my_backend.py"), help="The backend file ")


def load_custom_backend(backend_file: Path):

    if not os.path.isfile(backend_file):
        raise RuntimeError(f"path {backend_file} does not exist")

    custom_backend_specs = importlib.util.spec_from_file_location(
        "custom_backend", backend_file
    )

    custom_backend = importlib.util.module_from_spec(custom_backend_specs)

    custom_backend_specs.loader.exec_module(custom_backend)

    backend = custom_backend.Backend()

    check_backend(backend)

    return backend


def check_backend(backend):

    missing_funcs = {"get_led_count", "set_led"}.difference(set(dir(backend)))

    if missing_funcs:
        raise RuntimeError(
            f"Your backend does not have the following functions: {missing_funcs}"
        )

    if len(signature(backend.get_led_count).parameters) != 0:  # pragma: no coverage
        raise RuntimeError(
            "Your backend get_led_count function should not take any arguments"
        )

    if len(signature(backend.set_led).parameters) != 2:
        raise RuntimeError(
            "Your backend set_led function should only take two arguments"
        )
