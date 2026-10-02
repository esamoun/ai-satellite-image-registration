import dataclasses
import datetime as dt
from pathlib import Path

import numpy as np
import pytest
from test_ingest import CENTRE, CLOUD, VEGETATION, site_at
from test_real import CATALOGUE, CONFIG, acquisition_scene, catalogue_of
from test_trainchips import BENCHMARK, RULES, SITES_TOML

from satreg.benchmark import draw_pair, in_units_of
from satreg.cli import main
from satreg.degrade import load_presets
from satreg.displacement import Translation
from satreg.georef import NOMINAL
from satreg.methods import raft
from satreg.real import Acquisition
from satreg.simulate import SimulatedPair
from satreg.texture import fractal_texture
from satreg.trainchips import TRAIN, VALIDATION, TrainingChip, TrainingConfig
from satreg.trainpairs import (
    CROSS_DATE,
    SAME_DATE,
    DegradationRanges,
    PairGenerator,
    PairsConfig,
    load_pairs_config,
    load_ranges,
    load_training_series,
    loss_mask,
    pair_rng,
    timed_pairs,
    to_markdown,
)

CONFIGS = Path(__file__).parents[1] / "configs"
PRESETS = load_presets(CONFIGS / "degradations.toml")

# The smallest pairs the network takes, cut from chips just large enough.
SIZE, CHIP_PX = 128, 256
ROLES = ("anchor", "days", "season", "year")


def date(role, seed, hidden=None):
    """One date of a chip: a texture in digital-number units, clear by default."""
    scl = np.full((CHIP_PX, CHIP_PX), VEGETATION, np.uint8)
    if hidden is not None:
        scl[hidden] = CLOUD
    return Acquisition(
        role=role,
        image=1500 + 400 * fractal_texture(CHIP_PX, seed),
        scl=scl,
        georef=NOMINAL,
        item_id=f"item-{seed}",
        datetime=dt.datetime(2025, 7, 1 + seed, 10, 56, tzinfo=dt.UTC),
        platform="sentinel-2b",
    )


def chips(n_chips=2, **hidden):
    """Chips of four dates each; ``hidden`` gives a date's hidden pixels by role."""
    return {
        f"chip{c}": [
            date(role, 4 * c + i, hidden.get(role)) for i, role in enumerate(ROLES)
        ]
        for c in range(n_chips)
    }


def ranges(**changes):
    """Ranges that degrade nothing but for a faint noise, unless changed."""
    fields = {
        "gain": (1.0, 1.0),
        "offset": (0.0, 0.0),
        "gamma": (1.0, 1.0),
        "cover": (0.0, 0.0),
        "sigma": (0.0, 0.0),
        "snr_db": (60.0, 60.0),
        "cloudy_moving": 0.0,
        "cloudy_reference": 0.0,
    }
    return DegradationRanges(**{**fields, **changes})


def ranges_at(preset):
    """Ranges of one value each: the parameters of a benchmark preset."""
    r, c, b, n = preset.radiometry, preset.clouds, preset.blur, preset.noise
    return ranges(
        gain=(r.gain, r.gain),
        offset=(r.offset, r.offset),
        gamma=(r.gamma, r.gamma),
        cover=(c.cover, c.cover),
        sigma=(b.sigma, b.sigma),
        snr_db=(n.snr_db, n.snr_db),
        cloudy_moving=1.0,
    )


def pairs_config(**changes):
    return PairsConfig(**{"size": SIZE, "seed": 7, **changes})


REPO_RANGES = load_ranges(CONFIGS / "degradations.toml")


@pytest.mark.parametrize("preset", ["mild", "hard"])
@pytest.mark.parametrize("scenario", ["translation", "affine", "dense"])
def test_a_pair_with_a_preset_s_exact_parameters_is_the_benchmark_s_pair(
    preset, scenario
):
    config = pairs_config(scenarios=(scenario,))
    generator = PairGenerator(chips(1), config, ranges_at(PRESETS[preset]))

    pair = generator(3)

    by_role = {d.role: d for d in generator.chips["chip0"]}
    image = by_role[pair.draw.dates[0]].image
    clean = draw_pair(
        image, config.simulation, pair_rng(7, 3, "geometry"), scenario, NOMINAL
    )
    expected = PRESETS[preset](clean, pair_rng(7, 3, "pixels"))
    assert pair.draw.kind == SAME_DATE
    assert np.array_equal(pair.reference, expected.reference)
    assert np.array_equal(pair.moving, expected.moving)
    assert np.array_equal(pair.pair.cloud, expected.cloud)
    assert np.array_equal(pair.flow, expected.truth.field((SIZE, SIZE)))
    assert pair.reference_cloud is None


def test_the_mask_leaves_out_what_a_known_shift_moves_out_of_frame():
    image = np.zeros((8, 8))
    pair = SimulatedPair(image, image, Translation(dx=2.5, dy=-1.0))

    mask = loss_mask(pair)

    # Row 0 would be read above the moving image, columns 5 to 7 right of it.
    expected = np.zeros((8, 8), bool)
    expected[1:, :5] = True
    assert np.array_equal(mask, expected)


def test_the_mask_leaves_out_opaque_cloud_on_either_image():
    image = np.zeros((8, 8))
    moving_cloud = np.zeros((8, 8))
    moving_cloud[2:4, 5:7] = 1.0
    moving_cloud[6, 6] = 0.5  # a thin cloud, which still shows the ground
    reference_cloud = np.zeros((8, 8))
    reference_cloud[7, 0] = 1.0
    hidden = np.zeros((8, 8), bool)
    hidden[5, 1] = True
    pair = SimulatedPair(image, image, Translation(dx=2.0, dy=0.0), moving_cloud)

    mask = loss_mask(pair, reference_cloud, hidden)

    expected = np.ones((8, 8), bool)
    expected[:, 6:] = False  # out of frame
    expected[2:4, 3:5] = False  # lands under the moving image's cloud
    expected[7, 0] = False  # under the reference image's cloud
    expected[5, 1] = False
    assert np.array_equal(mask, expected)
    # The benchmark keeps cloud pixels for a global truth; the loss does not.
    assert pair.valid[2:4, 3:5].all()


def test_clouds_fall_on_both_images_and_the_mask_follows_them():
    cloudy = ranges(cover=(0.3, 0.3), cloudy_moving=1.0, cloudy_reference=1.0)
    config = pairs_config(scenarios=("translation",), max_shift=0.0)

    pair = PairGenerator(chips(1), config, cloudy)(0)

    on_moving, on_reference = pair.pair.cloud, pair.reference_cloud
    assert not np.array_equal(on_moving, on_reference)
    assert np.mean(on_reference >= 0.5) == pytest.approx(0.3, abs=0.01)
    assert np.array_equal(pair.mask, (on_moving < 0.9) & (on_reference < 0.9))
    assert 0.3 < pair.mask.mean() < 0.9
    # A cloud is brighter than the ground it covers.
    opaque = on_reference >= 0.9
    assert pair.reference[opaque].mean() > pair.reference[~opaque].mean() + 400


@pytest.mark.parametrize("scenario", ["translation", "affine", "dense"])
def test_the_mask_follows_a_cloud_of_the_moving_image_through_the_motion(scenario):
    cloudy = ranges(cover=(0.3, 0.3), cloudy_moving=1.0)
    config = pairs_config(scenarios=(scenario,))

    pair = PairGenerator(chips(1), config, cloudy)(1)

    # Where each reference pixel truly is in the moving image, and the cloud there.
    rows, cols = np.indices((SIZE, SIZE)) + pair.flow
    inside = (rows >= 0) & (rows <= SIZE - 1) & (cols >= 0) & (cols <= SIZE - 1)
    r0 = np.clip(np.floor(rows).astype(int), 0, SIZE - 2)
    c0 = np.clip(np.floor(cols).astype(int), 0, SIZE - 2)
    fr, fc = np.clip(rows - r0, 0, 1), np.clip(cols - c0, 0, 1)
    cloud = pair.pair.cloud
    there = (
        cloud[r0, c0] * (1 - fr) * (1 - fc)
        + cloud[r0, c0 + 1] * (1 - fr) * fc
        + cloud[r0 + 1, c0] * fr * (1 - fc)
        + cloud[r0 + 1, c0 + 1] * fr * fc
    )
    # Pixels a rounding could tip either way are not compared.
    sure = (np.abs(there - 0.9) > 1e-6) & inside
    assert np.abs(pair.flow).max() > 0.5
    assert np.array_equal(pair.mask[sure], there[sure] < 0.9)
    assert not pair.mask[~inside].any()
    # The cloud read in place, without the motion, is another mask.
    assert not np.array_equal(pair.mask[sure], cloud[sure] < 0.9)


def test_clouding_the_reference_changes_nothing_else():
    config = pairs_config(scenarios=("dense",))
    base = ranges(cover=(0.2, 0.2), cloudy_moving=1.0, snr_db=(20.0, 20.0))
    cloudy = dataclasses.replace(base, cloudy_reference=1.0)

    plain = PairGenerator(chips(1), config, base)(5)
    clouded = PairGenerator(chips(1), config, cloudy)(5)

    assert np.array_equal(plain.moving, clouded.moving)
    assert np.array_equal(plain.flow, clouded.flow)
    clear = clouded.reference_cloud == 0
    assert 0 < clear.mean() < 1
    assert np.array_equal(plain.reference[clear], clouded.reference[clear])
    assert not np.array_equal(plain.reference, clouded.reference)


def test_the_same_seed_gives_the_same_pairs_in_any_order():
    config = pairs_config(cross_date=0.5)
    first = PairGenerator(chips(), config, REPO_RANGES)
    second = PairGenerator(chips(), config, REPO_RANGES)

    forward = [first(i) for i in (0, 1, 2)]
    backward = [second(i) for i in (2, 1, 0)][::-1]

    for a, b in zip(forward, backward, strict=True):
        assert a.draw == b.draw
        assert np.array_equal(a.reference, b.reference)
        assert np.array_equal(a.moving, b.moving)
        assert np.array_equal(a.flow, b.flow)
        assert np.array_equal(a.mask, b.mask)
    assert len({pair.draw for pair in forward}) == 3


def test_another_seed_gives_other_pairs():
    one = PairGenerator(chips(), pairs_config(seed=1), REPO_RANGES)
    two = PairGenerator(chips(), pairs_config(seed=2), REPO_RANGES)

    assert [one.draw(i) for i in range(5)] != [
        dataclasses.replace(two.draw(i)) for i in range(5)
    ]


def test_the_share_of_cross_date_pairs_is_the_config_s():
    def draws(share):
        generator = PairGenerator(chips(), pairs_config(cross_date=share), REPO_RANGES)
        return [generator.draw(i) for i in range(300)]

    none, half, every = draws(0.0), draws(0.5), draws(1.0)

    assert all(d.kind == SAME_DATE and d.dates[0] == d.dates[1] for d in none)
    assert all(d.kind == CROSS_DATE and d.dates[0] != d.dates[1] for d in every)
    assert 0.4 < np.mean([d.kind == CROSS_DATE for d in half]) < 0.6
    # Every second date of a chip is drawn, and every chip and scenario.
    assert {d.dates for d in every} >= {(a, b) for a in ROLES for b in ROLES if a != b}
    assert {d.chip for d in none} == {"chip0", "chip1"}
    assert {d.scenario for d in none} == {"translation", "affine", "dense"}


def test_two_shares_of_cross_date_pairs_differ_by_the_moving_date_only():
    same = PairGenerator(chips(), pairs_config(cross_date=0.0), REPO_RANGES)
    cross = PairGenerator(chips(), pairs_config(cross_date=1.0), REPO_RANGES)

    for i in range(20):
        a, b = same.draw(i), cross.draw(i)
        assert (a.chip, a.dates[0], a.scenario) == (b.chip, b.dates[0], b.scenario)
        assert a.degradation == b.degradation
    assert np.array_equal(same(0).flow, cross(0).flow)


def test_a_cross_date_pair_is_cut_like_the_benchmark_s_inter_band_pair():
    config = pairs_config(cross_date=1.0, scenarios=("affine",))
    generator = PairGenerator(chips(1), config, ranges_at(PRESETS["mild"]))

    pair = generator(2)

    by_role = {d.role: d for d in generator.chips["chip0"]}
    reference, moving = (by_role[role].image for role in pair.draw.dates)
    clean = draw_pair(
        in_units_of(moving, reference),
        config.simulation,
        pair_rng(7, 2, "geometry"),
        "affine",
        reference=reference,
    )
    expected = PRESETS["mild"](clean, pair_rng(7, 2, "pixels"))
    assert np.array_equal(pair.reference, expected.reference)
    assert np.array_equal(pair.moving, expected.moving)
    assert not pair.hidden.any()


def test_what_either_date_hides_is_left_out_of_a_cross_date_pair_only():
    everywhere = (slice(None), slice(None))
    config = pairs_config(cross_date=1.0, scenarios=("translation",), max_shift=0.0)
    series = {"chip0": [date("anchor", 0), date("days", 1, hidden=everywhere)]}

    cross = PairGenerator(series, config, ranges())
    same = PairGenerator(series, dataclasses.replace(config, cross_date=0.0), ranges())

    # Whichever of the two dates is the reference, the other one hides it all.
    assert not any(cross(i).mask.any() for i in range(4))
    # On one date, a real cloud is ground like any other: it moves with it.
    assert all(same(i).mask.all() for i in range(4))


def test_the_hidden_pixels_are_those_of_the_pair_s_window():
    band = (slice(120, 136), slice(None))
    config = pairs_config(cross_date=1.0, scenarios=("translation",), max_shift=0.0)
    series = {"chip0": [date("anchor", 0), date("days", 1, hidden=band)]}

    pair = PairGenerator(series, config, ranges())(0)

    top = round(-pair.pair.georef.transform.f + NOMINAL.transform.f) // 10
    rows = np.flatnonzero(pair.hidden.all(axis=1))
    assert pair.hidden.any(axis=1).sum() == len(rows)
    assert list(rows + top) == [r for r in range(120, 136) if top <= r < top + SIZE]
    assert np.array_equal(pair.mask, ~pair.hidden)


def test_the_network_s_inputs_are_those_of_the_raft_method():
    pair = PairGenerator(chips(1), pairs_config(), REPO_RANGES)(0)

    reference, moving = pair.network_inputs()

    assert np.array_equal(reference, raft.network_input(pair.reference))
    assert np.array_equal(moving, raft.network_input(pair.moving))
    assert reference.shape == (3, SIZE, SIZE) == moving.shape
    assert reference.dtype == np.float32
    assert reference.min() == -1 and reference.max() == 1
    # Flow and mask are on the grid of the inputs: nothing was padded.
    assert pair.flow.shape == (2, SIZE, SIZE) and pair.mask.shape == (SIZE, SIZE)


def training_config():
    plain = TrainingChip(site_at(*CENTRE, chip_px=200, name="plain"), TRAIN, "forest")
    town = TrainingChip(
        site_at(*CENTRE, chip_px=200, name="town", lon=3.0), VALIDATION, "urban"
    )
    return TrainingConfig({"plain": plain, "town": town}, RULES, BENCHMARK)


@pytest.fixture
def scenes(tmp_path):
    """A search over an anchor and the two dates the fixture series takes."""
    d = dt.date
    return catalogue_of(
        acquisition_scene(tmp_path, d(2025, 7, 1), cloud_cover=0.1),
        acquisition_scene(tmp_path, d(2025, 6, 26)),
        acquisition_scene(tmp_path, d(2025, 9, 28), cloud_cover=30.0),
    )


def test_training_series_are_those_of_the_training_chips_only(tmp_path, scenes):
    series = load_training_series(training_config(), CONFIG, tmp_path, None, scenes)

    assert list(series) == ["plain"]
    assert [a.role for a in series["plain"]] == ["days", "anchor", "season"]
    assert series["plain"][0].image.shape == (200, 200)


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("town", "town is a validation chip: no train pair"),
        ("beauce", "beauce is a benchmark chip"),
        ("alps", "alps is a held-out site"),
    ],
)
def test_no_pair_is_cut_from_a_chip_that_is_not_a_training_chip(
    tmp_path, scenes, name, message
):
    with pytest.raises(ValueError, match=message):
        load_training_series(training_config(), CONFIG, tmp_path, [name], scenes)

    assert scenes.calls == []


def test_the_repository_ranges_reach_past_hard_on_every_parameter():
    hard, mild = PRESETS["hard"], PRESETS["mild"]
    r = REPO_RANGES

    for preset in (mild, hard):
        assert r.gain[0] < preset.radiometry.gain < r.gain[1]
        assert r.offset[0] < preset.radiometry.offset < r.offset[1]
        assert r.gamma[0] < preset.radiometry.gamma < r.gamma[1]
        assert r.cover[0] <= preset.clouds.cover < r.cover[1]
        assert r.sigma[0] <= preset.blur.sigma < r.sigma[1]
        assert r.snr_db[0] < preset.noise.snr_db < r.snr_db[1]
    # Clean is the other end: no blur, no cloud, and pairs with no cloud at all.
    assert r.sigma[0] == 0 and r.cover[0] == 0
    assert r.cloudy_moving < 1 and 0 < r.cloudy_reference < 1


def test_drawn_degradations_stay_in_their_ranges_and_fill_them():
    rng = np.random.default_rng(0)

    drawn = [REPO_RANGES.draw(rng) for _ in range(2000)]

    for name in ("gain", "offset", "gamma", "sigma", "snr_db"):
        values = np.array([getattr(d, name) for d in drawn])
        low, high = getattr(REPO_RANGES, name)
        assert low <= values.min() < low + 0.05 * (high - low)
        assert high - 0.05 * (high - low) < values.max() <= high
    # Log-uniform: as many gains under 1 as over it, for a range that mirrors.
    assert np.mean([d.gain < 1 for d in drawn]) == pytest.approx(0.5, abs=0.05)
    assert np.mean([d.cover > 0 for d in drawn]) == pytest.approx(0.5, abs=0.05)
    assert np.mean([d.reference_cover > 0 for d in drawn]) == pytest.approx(
        0.3, abs=0.05
    )
    assert max(d.cover for d in drawn) <= 0.4


def test_the_repository_pairs_config_is_the_benchmark_s_motion():
    config = load_pairs_config(CONFIGS / "train-pairs.toml")

    assert config == PairsConfig(cross_date=0.5)
    assert (config.size, config.max_shift) == (256, 4.0)
    assert config.scenarios == ("translation", "affine", "dense")


TRAINING = (
    "[training.radiometry]\ngain = [0.6, 1.67]\noffset = [-0.7, 0.7]\n"
    "gamma = [0.6, 1.7]\n[training.clouds]\ncover = [0.0, 0.4]\nmoving = 0.5\n"
    "reference = 0.3\n[training.blur]\nsigma = [0.0, 1.3]\n"
    "[training.noise]\nsnr_db = [12.0, 40.0]\n"
)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[presets.clean]\n", r"needs a \[training\] table"),
        (TRAINING + "[training.haze]\nlevel = [0, 1]\n", "unknown degradation 'haze'"),
        (TRAINING.replace("moving = 0.5\n", ""), r"\[training.clouds\] needs moving"),
        (TRAINING + "width = [0, 1]\n", r"\[training.noise\]: unknown key 'width'"),
        (TRAINING.replace("[0.6, 1.67]", "[1.67, 0.6]"), "gain needs low <= high"),
        (TRAINING.replace("[0.6, 1.67]", "[0.0, 1.67]"), "must be positive"),
        (TRAINING.replace("[0.6, 1.67]", "0.6"), r"gain must be \[low, high\]"),
        (TRAINING.replace("[0.0, 0.4]", "[0.0, 1.4]"), "cover must stay in"),
        (TRAINING.replace("[0.0, 1.3]", "[-1.0, 1.3]"), "sigma needs low <= high"),
        (TRAINING.replace("moving = 0.5", "moving = 1.5"), "cloudy_moving must be in"),
    ],
)
def test_bad_training_ranges_are_rejected(tmp_path, text, message):
    path = tmp_path / "degradations.toml"
    path.write_text(text)

    with pytest.raises(ValueError, match=message):
        load_ranges(path)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[benchmark]\n", r"needs a \[pairs\] table"),
        ("[pairs]\nshare = 0.5\n", "unknown key 'share'"),
        ("[pairs]\ncross_date = 1.5\n", "cross_date must be in"),
        ("[pairs]\nsize = 100\n", "size must be a multiple of 8 and at least 128"),
        ('[pairs]\nscenarios = ["projective"]\n', "scenarios must be among"),
        ("[pairs]\nmax_shift = -1.0\n", "ranges must be non-negative"),
    ],
)
def test_bad_pairs_config_is_rejected(tmp_path, text, message):
    path = tmp_path / "train-pairs.toml"
    path.write_text(text)

    with pytest.raises(ValueError, match=message):
        load_pairs_config(path)


def test_cross_date_pairs_need_two_dates_and_pairs_need_a_chip():
    single = {"chip0": [date("anchor", 0)]}

    PairGenerator(single, pairs_config(), ranges())
    with pytest.raises(ValueError, match=r"chip0 has 1 date\(s\)"):
        PairGenerator(single, pairs_config(cross_date=0.5), ranges())
    with pytest.raises(ValueError, match="at least one chip"):
        PairGenerator({}, pairs_config(), ranges())


def test_the_summary_counts_the_pairs_and_gives_their_throughput():
    generator = PairGenerator(chips(), pairs_config(cross_date=0.5), REPO_RANGES)

    pairs, rows = timed_pairs(generator, range(6))
    table = to_markdown(rows)

    assert [pair.draw.index for pair in pairs] == list(range(6))
    assert [row.usable for row in rows] == [pair.mask.mean() for pair in pairs]
    counts = [int(line.split("|")[3]) for line in table.splitlines()[2:] if "|" in line]
    assert sum(counts) == 6
    assert "pairs per second" in table


def cached(tmp_path, scenes):
    """Configure a training and a validation chip, the first one in the cache.

    Returns:
        The arguments of ``train-pairs`` that read it without any fetch.
    """
    site = site_at(*CENTRE)
    (tmp_path / "sites.toml").write_text(SITES_TOML)
    train = tmp_path / "train-sites.toml"
    train.write_text(
        "[defaults]\nchip_px = 200\nstart = 2025-04-01\nend = 2025-09-30\n"
        "max_cloud = 5.0\n"
        f'[chips.place]\nlandscape = "forest"\nrole = "train"\n'
        f"lon = {site.lon}\nlat = {site.lat}\n"
        '[chips.town]\nlandscape = "urban"\nrole = "validation"\n'
        "lon = 3.0\nlat = 45.0\n"
    )
    series = tmp_path / "real.toml"
    series.write_text(
        '[series]\nsites = ["beauce"]\nmax_scene_cloud = 50.0\n[series.dates]\n'
        "days = { offset_days = 0, within_days = 15 }\n"
        "season = { offset_days = 91, within_days = 30 }\n"
    )
    pairs = tmp_path / "train-pairs.toml"
    pairs.write_text(f"[pairs]\nsize = {SIZE}\ncross_date = 0.5\nseed = 3\n")
    place = TrainingChip(
        site_at(*CENTRE, chip_px=200, name="place", max_chip_cloud=site.max_chip_cloud),
        TRAIN,
        "forest",
    )
    config = TrainingConfig({"place": place}, RULES, BENCHMARK)
    load_training_series(config, CONFIG, tmp_path / "data", None, scenes)
    return [
        "train-pairs",
        "--sites-config",
        str(tmp_path / "sites.toml"),
        "--train-config",
        str(train),
        "--series-config",
        str(series),
        "--pairs-config",
        str(pairs),
        "--degradations-config",
        str(CONFIGS / "degradations.toml"),
        "--data-dir",
        str(tmp_path / "data"),
        "--out",
        str(tmp_path / "out"),
    ]


def test_train_pairs_writes_the_table_the_rows_and_the_contact_sheet(
    tmp_path, capsys, scenes
):
    args = cached(tmp_path, scenes)

    main(args + ["--n-pairs", "6", "--sheet-pairs", "4"])

    printed = capsys.readouterr().out
    out = tmp_path / "out"
    assert printed == (out / "summary.md").read_text()
    assert "6 training pairs of 128 px from 1 chips (place), seed 3" in printed
    assert "cross-date share 0.5" in printed
    assert len((out / "pairs.csv").read_text().splitlines()) == 7
    assert (out / "contact-sheet.png").stat().st_size > 10_000
    assert (out / "context.json").is_file()


def test_train_pairs_takes_its_share_of_cross_date_pairs_from_the_command_line(
    tmp_path, capsys, scenes
):
    args = cached(tmp_path, scenes)

    main(args + ["--n-pairs", "4", "--sheet-pairs", "0", "--cross-date", "0"])

    assert "cross-date share 0." in capsys.readouterr().out
    rows = (tmp_path / "out" / "pairs.csv").read_text().splitlines()[1:]
    assert all(f",{SAME_DATE}," in row for row in rows)
    assert not (tmp_path / "out" / "contact-sheet.png").exists()


def test_train_pairs_refuses_a_validation_chip(tmp_path, scenes):
    args = cached(tmp_path, scenes)

    with pytest.raises(SystemExit, match="town is a validation chip: no train pair"):
        main(args + ["--chip", "town"])


def test_catalogue_is_the_fixture_s():
    # The fixture series of this file are fetched from the catalogue of the
    # benchmark configuration the training configuration is built on.
    assert BENCHMARK.catalogue == CATALOGUE
