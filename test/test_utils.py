from marimapper import utils
import argparse


def test_add_common_args():
    parser = argparse.ArgumentParser()
    utils.add_common_args(parser)
    args = parser.parse_args([])

    assert args.device == 0
    assert args.exposure == -10
    assert args.threshold == 128
    assert not args.version
    assert not args.verbose


def test_add_backend_args():

    parser = argparse.ArgumentParser()
    utils.add_backend_args(parser)
    args = parser.parse_args([])

    assert args.backend == "dummy"
    assert args.start == 0
    assert args.end == 10000
    assert args.server is None
