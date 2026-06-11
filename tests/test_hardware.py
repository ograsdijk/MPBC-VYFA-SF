import os

import pytest

from mpbc_vyfa_sf import MPBAmplifier

MPB_PORT = os.environ.get("MPB_PORT")


@pytest.mark.hardware
@pytest.mark.skipif(not MPB_PORT, reason="set MPB_PORT to run the hardware test")
def test_read_model_from_hardware():
    instrument = MPBAmplifier(port=MPB_PORT)
    try:
        model = instrument.model
        assert isinstance(model, str)
        assert model != ""
    finally:
        instrument.close()
