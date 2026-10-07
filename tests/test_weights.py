import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import numpy as np
import pytest
from test_raft import needs_raft

from satreg import weights
from satreg.cli import _checkpoints, main
from satreg.compute import file_sha256
from satreg.methods import deep, load_methods
from satreg.methods import raft as raft_method
from satreg.methods.raft import Raft
from satreg.simulate import simulate_translation
from satreg.texture import fractal_texture
from satreg.train import BEST, METHOD_NAMES
from satreg.weights import (
    RELEASED,
    REPOSITORY,
    TOKEN_VARIABLE,
    ReleasedWeights,
    WeightsRefused,
    WeightsUnavailable,
    fetch,
)

REPO = Path(__file__).parents[1]
CONFIGS = REPO / "configs"

needs_torch = pytest.mark.skipif(
    bool(deep.missing_modules()), reason="needs the dl extra: make install-dl"
)

CONTENT = b"the published weights"
TOKEN = "a-token-kept-out-of-every-message"


def publish(monkeypatch, content=CONTENT, model="small"):
    """Declare toy weights whose published file is ``content``."""
    toy = ReleasedWeights(
        name="toy",
        model=model,
        run="toy-run",
        tag="toy-tag",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    monkeypatch.setattr(weights, "RELEASED", {"toy": toy})
    return toy


@pytest.fixture
def toy(monkeypatch):
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    return publish(monkeypatch)


class GitHub:
    """Stands for GitHub: answers each address asked, and keeps the requests."""

    def __init__(self, monkeypatch, answers):
        self.answers = answers
        self.requests = []
        monkeypatch.setattr(weights, "urlopen", self)

    def __call__(self, request, timeout):
        self.requests.append(request)
        answer = self.answers[request.full_url]
        if isinstance(answer, Exception):
            raise answer
        return io.BytesIO(answer)


def public_url(toy):
    return f"https://github.com/{REPOSITORY}/releases/download/toy-tag/{toy.asset}"


API = f"https://api.github.com/repos/{REPOSITORY}/releases"


def listing(*names):
    assets = [{"id": 40 + i, "name": name} for i, name in enumerate(names)]
    return json.dumps({"tag_name": "toy-tag", "assets": assets}).encode()


def refusal(code):
    return HTTPError("https://github.com", code, "refused", None, None)


def test_a_released_file_is_named_after_its_weights_and_its_hash():
    for name, released in RELEASED.items():
        assert released.name == name
        assert released.asset == f"{name}-{released.sha256[:8]}.pth"
        assert released.card == f"{name}-{released.sha256[:8]}.json"
        assert len(released.sha256) == 64


def test_the_fine_tuned_methods_run_the_released_weights_of_their_model():
    methods = load_methods(CONFIGS / "methods.toml")

    for model, name in METHOD_NAMES.items():
        assert methods[name].model == model
        assert methods[name].checkpoint == ""
        assert RELEASED[methods[name].release].model == model
    assert {methods[name].release for name in METHOD_NAMES.values()} == set(RELEASED)


@pytest.mark.parametrize("name", RELEASED)
def test_the_pinned_hash_is_the_one_of_the_kept_weights_of_the_training(name):
    kept = REPO / "outputs" / "train" / RELEASED[name].run / BEST
    if not kept.is_file():
        pytest.skip(f"needs the kept weights of the training at {kept}")

    assert file_sha256(kept) == RELEASED[name].sha256


@pytest.mark.parametrize("name", RELEASED)
def test_the_pinned_hash_is_the_one_the_published_tables_were_scored_with(name):
    results = REPO / "docs" / "results" / "n3"
    recorded = {
        weights["sha256"]
        for context in results.glob("context-*.json")
        for weights in json.loads(context.read_text()).get("checkpoints", {}).values()
    }

    assert RELEASED[name].sha256 in recorded


def test_a_method_takes_released_weights_that_exist_and_fit_its_model():
    with pytest.raises(ValueError, match="no released weights named 'nothing'"):
        Raft(release="nothing")
    with pytest.raises(ValueError, match="are for a large model, the method asks for"):
        Raft(model="small", release="raft_large_ft")
    with pytest.raises(ValueError, match="a checkpoint or from a release, not both"):
        Raft(checkpoint="best.pt", release="raft_large_ft")


def test_weights_in_the_cache_are_returned_without_asking_github(
    tmp_path, toy, monkeypatch
):
    github = GitHub(monkeypatch, {})
    (tmp_path / toy.asset).write_bytes(CONTENT)

    assert fetch("toy", directory=tmp_path) == tmp_path / toy.asset
    assert github.requests == []


def test_weights_not_in_the_cache_are_downloaded_from_the_release(
    tmp_path, toy, monkeypatch
):
    github = GitHub(monkeypatch, {public_url(toy): CONTENT})
    cache = tmp_path / "hub" / "checkpoints"

    path = fetch("toy", directory=cache)

    assert path.read_bytes() == CONTENT
    assert [p.name for p in cache.iterdir()] == [toy.asset]
    # Without a token, the address anyone reads once the repository is public.
    (request,) = github.requests
    assert request.full_url == public_url(toy)
    assert not request.has_header("Authorization")


def test_a_download_with_a_wrong_hash_is_refused_and_not_cached(
    tmp_path, toy, monkeypatch
):
    GitHub(monkeypatch, {public_url(toy): b"something else"})

    with pytest.raises(
        WeightsRefused, match=f"not the published toy.*{toy.sha256[:16]}"
    ):
        fetch("toy", directory=tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_a_cached_file_with_a_wrong_hash_is_fetched_again(tmp_path, toy, monkeypatch):
    GitHub(monkeypatch, {public_url(toy): CONTENT})
    (tmp_path / toy.asset).write_bytes(b"cut short")

    assert fetch("toy", directory=tmp_path).read_bytes() == CONTENT


def test_with_a_token_the_asset_is_asked_through_the_api(tmp_path, toy, monkeypatch):
    monkeypatch.setenv(TOKEN_VARIABLE, TOKEN)
    github = GitHub(
        monkeypatch,
        {
            f"{API}/tags/toy-tag": listing("other.pth", toy.asset),
            f"{API}/assets/41": CONTENT,
        },
    )

    assert fetch("toy", directory=tmp_path).read_bytes() == CONTENT

    described, asset = github.requests
    assert asset.get_header("Accept") == "application/octet-stream"
    for request in (described, asset):
        assert request.host == "api.github.com"
        # Sent to GitHub's API, and not on to where the asset is served from.
        assert request.unredirected_hdrs == {"Authorization": f"Bearer {TOKEN}"}
        assert TOKEN not in str(request.headers)


def test_a_private_release_without_a_token_says_to_set_one(tmp_path, toy, monkeypatch):
    GitHub(monkeypatch, {public_url(toy): refusal(404)})

    with pytest.raises(WeightsUnavailable, match=f"not public: set {TOKEN_VARIABLE}"):
        fetch("toy", directory=tmp_path)

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("answers", "message"),
    [
        ({f"{API}/tags/toy-tag": refusal(401)}, "GitHub refused the token"),
        ({f"{API}/tags/toy-tag": refusal(404)}, "has no such file for the token"),
        ({f"{API}/tags/toy-tag": listing("other.pth")}, "has no asset toy-"),
        ({f"{API}/tags/toy-tag": URLError("no route")}, "could not be reached"),
    ],
)
def test_a_failed_download_says_why_without_the_token(
    tmp_path, toy, monkeypatch, answers, message
):
    monkeypatch.setenv(TOKEN_VARIABLE, TOKEN)
    GitHub(monkeypatch, answers)

    with pytest.raises(WeightsUnavailable, match=message) as raised:
        fetch("toy", directory=tmp_path)

    assert TOKEN not in str(raised.value)
    assert list(tmp_path.iterdir()) == []


def test_weights_are_taken_from_a_directory_with_the_same_check(
    tmp_path, toy, monkeypatch
):
    github = GitHub(monkeypatch, {})
    source, cache = tmp_path / "source", tmp_path / "cache"
    source.mkdir()

    with pytest.raises(WeightsUnavailable, match=f"no {toy.asset} in"):
        fetch("toy", source, cache)
    (source / toy.asset).write_bytes(b"something else")
    with pytest.raises(WeightsRefused):
        fetch("toy", source, cache)
    assert list(cache.iterdir()) == []

    (source / toy.asset).write_bytes(CONTENT)
    assert fetch("toy", source, cache).read_bytes() == CONTENT
    assert github.requests == []


def test_a_run_names_the_released_weights_of_its_methods(tmp_path, toy, monkeypatch):
    monkeypatch.setattr(weights, "cache_directory", lambda: tmp_path)
    (tmp_path / toy.asset).write_bytes(CONTENT)
    methods = {
        "raft": SimpleNamespace(checkpoint="", release=""),
        "raft_ft": SimpleNamespace(checkpoint="", release="toy"),
    }

    # The release and the asset, not where the cache is on this machine.
    assert _checkpoints(methods) == {
        "raft_ft": {"release": "toy-tag", "asset": toy.asset, "sha256": toy.sha256}
    }


@needs_torch
def test_a_benchmark_of_a_method_without_its_released_weights_is_refused(
    tmp_path, monkeypatch
):
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    monkeypatch.setattr(weights, "cache_directory", lambda: tmp_path / "cache")
    large = RELEASED["raft_large_ft"]
    address = f"https://github.com/{REPOSITORY}/releases/download"
    GitHub(monkeypatch, {f"{address}/{large.tag}/{large.asset}": refusal(404)})
    monkeypatch.chdir(tmp_path)
    args = ["benchmark", "--pairs", "1", "--methods", "raft_ft", "--out", "out"]
    for option, name in (("--methods", "methods"), ("--degradations", "degradations")):
        args += [f"{option}-config", str(CONFIGS / f"{name}.toml")]

    with pytest.raises(SystemExit, match=f"method raft_ft: .*set {TOKEN_VARIABLE}"):
        main(args)

    assert not (tmp_path / "out").exists()


@needs_torch
def test_the_command_fetches_the_weights_it_is_asked_for(
    tmp_path, toy, monkeypatch, capsys
):
    monkeypatch.setattr(weights, "cache_directory", lambda: tmp_path / "cache")
    GitHub(monkeypatch, {public_url(toy): refusal(404)})
    (tmp_path / toy.asset).write_bytes(CONTENT)

    with pytest.raises(SystemExit, match=f"satreg: .*set {TOKEN_VARIABLE}"):
        main(["fetch-weights"])
    with pytest.raises(SystemExit, match="satreg: no released weights named 'other'"):
        main(["fetch-weights", "other"])
    main(["fetch-weights", "--from", str(tmp_path)])

    assert capsys.readouterr().out == f"{tmp_path / 'cache' / toy.asset}\n"


def kept_weights(path, **extra):
    """Write the kept weights of a toy training of RAFT small, and return them."""
    import torch

    network = raft_method.builder("small")(weights=None)
    state = {
        "model": network.state_dict(),
        "step": 3,
        "validation": {"score": 0.25},
        "train": {"model": "small", "steps": 4},
        "pairs": {"seed": 0},
        "ranges": {"gain": [0.6, 1.67]},
        "chips": ["a_chip"],
        "commit": "abcdef0123",
        "dirty": False,
        **extra,
    }
    path.parent.mkdir(parents=True)
    torch.save(state, path)
    return path.read_bytes()


@needs_raft
def test_the_released_file_is_the_kept_weights_of_the_training_unchanged(
    tmp_path, monkeypatch, capsys
):
    runs, out = tmp_path / "train", tmp_path / "release"
    content = kept_weights(runs / "toy-run" / BEST)
    toy = publish(monkeypatch, content)

    main(["export-weights", "--runs", str(runs), "--out", str(out)])

    assert {p.name for p in out.iterdir()} == {toy.asset, toy.card, "notes.md"}
    assert (out / toy.asset).read_bytes() == content
    card = json.loads((out / toy.card).read_text())
    assert (card["sha256"], card["asset"], card["bytes"]) == (
        toy.sha256,
        toy.asset,
        len(content),
    )
    assert (card["commit"], card["step"], card["train"]["model"]) == (
        "abcdef0123",
        3,
        "small",
    )
    assert card["chips"] == ["a_chip"]
    # The command says how to publish, and publishes nothing itself.
    printed = capsys.readouterr().out
    assert printed.startswith((out / "notes.md").read_text())
    assert f"gh release create toy-tag {out / toy.asset} {out / toy.card}" in printed
    assert toy.sha256 in printed


@needs_raft
def test_a_file_that_is_not_the_pinned_kept_weights_is_not_exported(
    tmp_path, monkeypatch
):
    runs, out = tmp_path / "train", tmp_path / "release"
    args = ["export-weights", "--runs", str(runs), "--out", str(out)]
    publish(monkeypatch)
    with pytest.raises(SystemExit, match=r"satreg: no checkpoint at .*toy-run"):
        main(args)

    content = kept_weights(runs / "toy-run" / BEST, optimizer={"lr": 1e-4})
    with pytest.raises(SystemExit, match="satreg: best.pt is not the published toy"):
        main(args)
    publish(monkeypatch, content)
    with pytest.raises(SystemExit, match="holds optimizer: it is a checkpoint to"):
        main(args)
    content = kept_weights(tmp_path / "other" / "toy-run" / BEST)
    publish(monkeypatch, content, model="large")
    args[args.index(str(runs))] = str(tmp_path / "other")
    with pytest.raises(SystemExit, match="holds a small model, toy is large"):
        main(args)

    assert not out.exists()


@needs_raft
def test_a_method_loads_its_released_weights_from_the_cache(tmp_path, monkeypatch):
    import torch

    content = kept_weights(tmp_path / "train" / "toy-run" / BEST)
    toy = publish(monkeypatch, content)
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    monkeypatch.setattr(weights, "cache_directory", lambda: tmp_path / "cache")
    github = GitHub(monkeypatch, {public_url(toy): content})
    raft_method._released_file.cache_clear()

    try:
        network = Raft(model="small", release="toy").network()
        again = Raft(model="small", release="toy", iterations=4).network()
    finally:
        raft_method._released_file.cache_clear()

    # Downloaded once, then the same network for every variant of the method.
    assert len(github.requests) == 1
    assert again is network
    kept = torch.load(tmp_path / "cache" / toy.asset, weights_only=True)["model"]
    for name, tensor in network.state_dict().items():
        assert torch.equal(tensor, kept[name])


@pytest.mark.parametrize("name", METHOD_NAMES.values())
def test_a_released_method_gives_a_dense_displacement(name):
    # The conftest refuses network access: the weights must be in the cache.
    if deep.missing_modules():
        pytest.skip("needs the dl extra: make install-dl")
    method = load_methods(CONFIGS / "methods.toml")[name]
    cached = weights.cache_directory() / RELEASED[method.release].asset
    if not cached.is_file():
        pytest.skip(f"needs {cached.name} in PyTorch's cache: satreg fetch-weights")
    pair = simulate_translation(fractal_texture(160, seed=3), dx=0.4, dy=-0.3)

    field = method(pair.reference, pair.moving).field(pair.reference.shape)

    assert field.shape == (2, *pair.reference.shape)
    assert np.isfinite(field).all()
