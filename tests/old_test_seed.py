from datetime import datetime, timedelta

import pytest
from immutables import Map
from pytest import raises

from spat.seed import ChannelMap, Seed


@pytest.fixture
def small_seed() -> Seed:
    time_step = timedelta(microseconds=1)
    start_time = datetime.now()
    channels: ChannelMap = Map(chan0=b"1234")
    return Seed(time_step, start_time, channels)


def test_accessors(small_seed: Seed) -> None:
    assert small_seed["chan0"] == b"1234"
    with raises(KeyError):
        small_seed["chan1"]


def test_constructor() -> None:
    time_step = timedelta(microseconds=1)
    start_time = datetime.now()
    channels: ChannelMap = Map(chan0=b"1234", chan1=b"12345")
    with raises(ValueError):
        Seed(time_step, start_time, channels)
