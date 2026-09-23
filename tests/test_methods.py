from pathlib import Path

import pytest

from satreg.methods import METHODS, load_methods, missing_dependencies
from satreg.methods.arosics import Arosics
from satreg.methods.phase_correlation import PhaseCorrelation
from satreg.methods.sift_ransac import SiftRansac

REPO_CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"


def test_a_variant_is_a_new_method_next_to_the_built_in_one(tmp_path):
    config = tmp_path / "methods.toml"
    config.write_text('[methods.strict_sift]\nmethod = "sift_ransac"\nratio = 0.6\n')

    methods = load_methods(config)

    assert methods["strict_sift"] == SiftRansac(ratio=0.6)
    assert methods["sift_ransac"] is METHODS["sift_ransac"]
    assert list(methods)[: len(METHODS)] == list(METHODS)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('[methods.fast]\nmethod = "orb"\n', "no configurable method orb"),
        (
            '[methods.sift_ransac]\nmethod = "arosics"\n',
            "variant sift_ransac would replace a built-in method",
        ),
        ('[methods.pc]\nmethod = "phase_correlation"\nsigma = 1\n', "method pc:"),
    ],
)
def test_bad_variants_are_rejected(tmp_path, text, message):
    config = tmp_path / "methods.toml"
    config.write_text(text)

    with pytest.raises(ValueError, match=message):
        load_methods(config)


def test_repository_configuration_declares_the_n1_variants():
    methods = load_methods(REPO_CONFIG)

    assert methods["phase_correlation_hann"] == PhaseCorrelation(window="hann")
    assert methods["arosics"].min_reliability == 40.0
    assert methods["arosics_floor60"].min_reliability == 60.0


def test_variants_need_what_their_method_needs():
    variant = Arosics(min_reliability=60.0)

    assert missing_dependencies(variant) == missing_dependencies(METHODS["arosics"])
    assert missing_dependencies(PhaseCorrelation(window="hann")) == []
