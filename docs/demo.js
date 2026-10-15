"use strict";

// The demo page reads what `satreg demo` wrote to demo/ and draws it. It
// computes no result: every figure on the page is one a file holds, and the
// only arithmetic here is where to draw it.

(() => {
  const DATA = "demo/";
  const SVG = "http://www.w3.org/2000/svg";

  // What the files name, in the page's words: the full name, the short one of
  // a choice, and what the method does in a sentence or two.
  const METHODS = {
    none: {
      name: "No registration",
      pick: "No registration",
      gloss: "Nothing is corrected. This is what you get if you compare the two images as they come.",
    },
    phase_correlation_hann: {
      name: "Phase correlation, Hann window",
      pick: "Phase correlation",
      gloss:
        "A classic method. It finds the one shift that best lines up the whole image, in steps of a " +
        "hundredth of a pixel. The Hann window fades the edges of both images first.",
    },
    sift_ransac: {
      name: "SIFT + RANSAC",
      pick: "SIFT + RANSAC",
      gloss:
        "A classic method. SIFT finds distinctive points and matches them between the two images, then " +
        "RANSAC keeps the affine transform most matches agree on. With too few of them it declines the " +
        "pair, which counts as a failure.",
    },
    raft: {
      name: "RAFT, pretrained",
      pick: "RAFT pretrained",
      gloss:
        "A neural network that estimates a displacement at every pixel. Pretrained: it runs with its " +
        "published weights, with no training on this project's data.",
    },
    raft_ft: {
      name: "RAFT, fine-tuned",
      pick: "RAFT fine-tuned",
      gloss:
        "The RAFT network again, trained further on this project's simulated pairs. Like the pretrained " +
        "one, it estimates a displacement at every pixel.",
    },
  };
  const NONE = "none";
  // The method the page opens on: the benchmark's own model. One click changes it.
  const FIRST_METHOD = "raft_ft";
  const SITES = {
    beauce: ["Beauce", "open fields"],
    toulouse: ["Toulouse", "a city"],
    vosges: ["Vosges", "forest"],
    marseille: ["Marseille", "a coast"],
  };
  const PRESETS = {
    clean: ["Clean", "the moving image is shifted and nothing else."],
    hard: [
      "Hard",
      "the moving image is also flatter and darker, blurred and partly under cloud, and both images are noisy.",
    ],
  };
  const CLASSIC = {
    phase_correlation: "Phase correlation",
    sift_ransac: "SIFT + RANSAC",
    arosics: "AROSICS",
  };
  // Arrows of the true field and of an estimate are drawn this many times their length.
  const FIELD_GAIN = 3;
  // What "Fit" picks from for the error: the largest that keeps the arrows apart.
  const ERROR_GAINS = [3, 10, 30, 100];
  // The ground a pixel covers, in metres: the 10 m of Sentinel-2's B04 band, as
  // the GeoTIFFs of examples/ hold it for these same windows. A unit, not a result.
  const PIXEL_M = 10;
  // The scale bar of the slider at each zoom: about a sixth of the picture.
  const SCALE_M = { 1: 500, 2: 200, 4: 100 };

  const state = {
    site: null,
    preset: null,
    method: null,
    // What the slider opens on: the changed pixels, before and after correction.
    view: "changed",
    zoom: 1,
    cx: 0.5,
    cy: 0.5,
    split: 50,
    gain: "auto",
    machine: "m1",
  };
  let manifest = null;
  let shown = null;
  let curve = [];
  const cells = new Map();

  const $ = (id) => document.getElementById(id);
  const clamp = (value, low, high) => Math.min(high, Math.max(low, value));

  const el = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const svgEl = (tag, attributes = {}, text) => {
    const node = document.createElementNS(SVG, tag);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  };

  // Figures as the page writes them: a real minus sign, and no "-0.00".
  const fixed = (value, digits) => {
    const text = value.toFixed(digits);
    return Number(text) === 0 ? text.replace("-", "") : text.replace("-", "−");
  };
  const px = (value, digits = 2) => `${fixed(value, digits)} px`;
  const percent = (share, digits = 2) => `${fixed(share * 100, digits)} %`;
  const milliseconds = (value) => `${fixed(value, value >= 100 ? 0 : 1)} ms`;
  const mebibytes = (value) => `${fixed(value, 1)} MiB`;
  // A distance in pixels said on the ground, for a reader who does not count in pixels.
  const metres = (value) => {
    const m = Math.abs(value) * PIXEL_M;
    if (m >= 10) return `${fixed(m, 0)} m`;
    if (m >= 1) return `${fixed(m, 1)} m`;
    return `${fixed(m * 100, m >= 0.1 ? 0 : 1)} cm`;
  };
  const onGround = (value) => el("span", `about ${metres(value)}`, "ground");

  const read = async (path, as) => {
    const response = await fetch(DATA + path);
    if (!response.ok) throw new Error(`${DATA}${path}: HTTP ${response.status}`);
    return response[as]();
  };
  const table = (text) => {
    const [head, ...lines] = text.trim().split(/\r?\n/);
    const keys = head.split(",");
    return lines.map((line) => {
      const values = line.split(",");
      return Object.fromEntries(keys.map((key, index) => [key, values[index]]));
    });
  };
  // A figure of a CSV file, or null where the file holds none.
  const figure = (text) => {
    const value = text === undefined || text === "" ? NaN : Number(text);
    return Number.isFinite(value) ? value : null;
  };

  const cell = (site, preset) => {
    const key = `${site}/${preset}`;
    if (!cells.has(key)) {
      const files = [manifest.files.slider, manifest.files.arrows];
      cells.set(
        key,
        Promise.all(files.map((file) => read(`${key}/${file}`, "json"))).then(
          ([pair, arrows]) => ({ directory: `${DATA}${key}/`, pair, arrows })
        )
      );
    }
    return cells.get(key);
  };

  // --- the choices ---------------------------------------------------------

  const fill = (host, name, values, label, chosen) => {
    host.replaceChildren(
      ...values.map((value) => {
        const input = el("input");
        input.type = "radio";
        input.name = name;
        input.value = value;
        input.checked = value === chosen;
        const wrapper = el("label");
        wrapper.append(input, el("span", label(value)));
        return wrapper;
      })
    );
  };
  const onPick = (id, apply) => {
    $(id).addEventListener("change", (event) => apply(event.target.value));
  };
  // One of the three choices of the bar: options on a wide screen, a list on a
  // narrow one, and both say the same.
  const choice = (name, values, label) => {
    const chips = $(`pick-${name}`);
    const list = $(`select-${name}`);
    fill(chips, name, values, label, state[name]);
    list.replaceChildren(
      ...values.map((value) => {
        const option = el("option", label(value));
        option.value = value;
        option.selected = value === state[name];
        return option;
      })
    );
    const pick = (event) => {
      state[name] = event.target.value;
      list.value = state[name];
      for (const input of chips.querySelectorAll("input")) input.checked = input.value === state[name];
      settle();
      draw();
    };
    chips.addEventListener("change", pick);
    list.addEventListener("change", pick);
  };
  const methodName = (name) => (METHODS[name] ? METHODS[name].name : name);
  const siteName = (name) => (SITES[name] ? SITES[name][0] : name);
  const presetName = (name) => (PRESETS[name] ? PRESETS[name][0] : name);
  const count = (value) => value.toLocaleString("en-US");

  // A row is a name, its figure, and under them a plain sentence, then the
  // detail for whoever wants it.
  const setFacts = (host, rows) => {
    host.replaceChildren(
      ...rows.map(([term, value, plain, detail]) => {
        const row = el("div");
        const figures = el("dd", undefined, "value");
        figures.append(...[].concat(value));
        const note = el("dd", plain, "note");
        if (detail) note.append(" ", el("span", detail, "detail"));
        row.append(el("dt", term), figures, note);
        return row;
      })
    );
  };
  // Two figures with an arrow between them, and the words a screen reader says instead.
  const fromTo = (before, after) => {
    const sign = el("span", " → ");
    sign.setAttribute("aria-hidden", "true");
    return [before, el("span", " before, ", "unseen"), sign, after, el("span", " after", "unseen")];
  };

  // A failure is said as one, with the reason the method gave.
  const setFailure = (host, outcome) => {
    host.hidden = !outcome.failure;
    if (!outcome.failure) return;
    const drawn = outcome.estimate
      ? " It did give an estimate, which is drawn as it is."
      : " It gave no estimate, so it has nothing of its own to draw.";
    host.replaceChildren(
      el("strong", "Failed. "),
      `${methodName(state.method)} on this pair: `,
      // The files name the exception before its message: the page keeps the message.
      el("q", outcome.reason.replace(/^\w+(?:Failure|Error): /, "")),
      `.${drawn} A method fails when it gives no estimate, or when it is more than ` +
        `${px(manifest.failure_threshold_px, 0)} (${metres(manifest.failure_threshold_px)}) off on average.`
    );
  };

  // --- the slider ----------------------------------------------------------

  const frame = $("frame");

  const place = () => {
    const half = 0.5 / state.zoom;
    state.cx = clamp(state.cx, half, 1 - half);
    state.cy = clamp(state.cy, half, 1 - half);
    frame.style.setProperty("--zoom", state.zoom);
    frame.style.setProperty("--tx", `${(0.5 - state.cx * state.zoom) * 100}%`);
    frame.style.setProperty("--ty", `${(0.5 - state.cy * state.zoom) * 100}%`);
    frame.style.setProperty("--split", `${state.split}%`);
    $("split").value = Math.round(state.split);
    const zoomed = state.zoom > 1;
    frame.classList.toggle("zoomed", zoomed);
    // Smoothed when enlarged a little; at 4× each pixel is drawn as the square it is.
    frame.classList.toggle("sharp", state.zoom >= 4);
    const bar = SCALE_M[state.zoom];
    const across = (manifest ? manifest.size_px : 256) * PIXEL_M;
    frame.style.setProperty("--bar", (bar * state.zoom) / across);
    $("scale-text").textContent = `${bar} m`;
    if (zoomed) frame.tabIndex = 0;
    else frame.removeAttribute("tabindex");
    frame.setAttribute(
      "aria-label",
      "The two images, one on each side of the divider." +
        (zoomed ? " Zoomed: the arrow keys move the view." : "")
    );
  };

  const side = (letter, image, veil, tag, alt) => {
    $(`image-${letter}`).hidden = !image;
    if (image) {
      $(`image-${letter}`).src = image;
      $(`image-${letter}`).alt = alt;
    }
    $(`veil-${letter}`).hidden = !veil;
    if (veil) $(`veil-${letter}`).src = veil;
    $(`tag-${letter}`).textContent = tag;
  };

  const estimateSaid = (estimate) => {
    if (estimate.model === "translation") {
      return `It estimated one shift for the whole image: dx ${px(estimate.dx)}, dy ${px(estimate.dy)}.`;
    }
    if (estimate.model === "dense") {
      return (
        "It estimated a displacement at every pixel: " +
        `dx ${px(estimate.mean_dx)}, dy ${px(estimate.mean_dy)} on average.`
      );
    }
    if (estimate.model === "affine") {
      return "It estimated an affine transform: a shift that can also stretch and turn the image a little.";
    }
    return "";
  };

  const drawSlider = ({ directory, pair }) => {
    const outcome = pair.methods[state.method];
    const before = pair.methods[NONE];
    const name = methodName(state.method);
    const none = state.method === NONE;
    const where = `the ${siteName(state.site)} window`;
    const reference = directory + pair.images.reference;
    const moving = directory + pair.images.moving;
    const corrected = outcome.corrected ? directory + outcome.corrected : null;
    const seen = "The moving image is shown at the reference's brightness, as the change detector reads it.";
    let caption;

    $("method-name").textContent = name;
    $("method-gloss").textContent = METHODS[state.method] ? METHODS[state.method].gloss : "";
    $("changed-legend").hidden = state.view !== "changed";
    $("missing-b").hidden = true;
    const nothing = () => {
      side("b", null, null, "No corrected image", "");
      $("missing-b").textContent = `${name} gave no estimate, so there is no corrected image.`;
      $("missing-b").hidden = false;
    };

    if (state.view === "changed") {
      const flagged = "Magenta: the pixels a change detector flags when it compares this image with the reference.";
      side(
        "a",
        moving,
        directory + before.changed,
        "Before correction",
        `Moving image of ${where} before correction, with the pixels flagged as changed`
      );
      if (none) {
        side("b", moving, directory + before.changed, "No correction", "The same image: no correction");
        caption = `${flagged} With no registration nothing is corrected, so both sides are the same.`;
      } else if (corrected && outcome.changed) {
        side(
          "b",
          corrected,
          directory + outcome.changed,
          "After correction",
          `Moving image of ${where} corrected by ${name}, with the pixels flagged as changed`
        );
        caption = `${flagged} Left of the divider, before correction. Right, after correction by ${name}.`;
      } else {
        nothing();
        caption = `${flagged} Left of the divider, before correction. Right, nothing: ${name} gave no estimate.`;
      }
    } else {
      side("a", reference, null, "Reference image", `Reference image of ${where}`);
      if (state.view === "before") {
        side("b", moving, null, "Moving image", `Moving image of ${where}`);
        caption =
          "Left of the divider, the reference image. Right, the moving image as it comes. " +
          `Drag the divider across an edge to see how far apart the two are. ${seen}`;
      } else if (none) {
        side("b", moving, null, "No correction", `Moving image of ${where}, not corrected`);
        caption =
          "Left of the divider, the reference image. With no registration nothing is corrected, " +
          `so the right side is the moving image as it comes. ${seen}`;
      } else if (corrected) {
        side("b", corrected, null, "Corrected image", `Moving image of ${where}, corrected by ${name}`);
        caption =
          `Left of the divider, the reference image. Right, the moving image corrected by ${name}. ` +
          `Where a correction reads from outside the image, the pixels are black. ${seen}`;
      } else {
        nothing();
        caption = `Left of the divider, the reference image. Right, nothing: ${name} gave no estimate.`;
      }
    }
    if (state.zoom >= 4) {
      caption += ` At 4×, each square is one pixel, ${PIXEL_M} m on the ground: the finest this band of Sentinel-2 sees.`;
    }
    if (state.zoom > 1) {
      caption +=
        " Zoomed in: drag the picture to look elsewhere, or use the arrow keys on it. " +
        "The divider still moves by its handle.";
    }
    $("slider-caption").textContent = caption;

    setFailure($("slider-failure"), outcome);

    const truth = pair.truth;
    const facts = [
      [
        "True shift",
        [px(truth.shift_px), onGround(truth.shift_px)],
        "How far the moving image was moved. Known exactly: it was made by shifting the reference.",
        `dx ${px(truth.dx)}, dy ${px(truth.dy)}, with x to the right and y down.`,
      ],
    ];
    if (none) {
      facts.push([
        "Error with no registration",
        [px(outcome.error_px), onGround(outcome.error_px)],
        "Nothing is corrected, so the whole shift is left.",
      ]);
    } else if (outcome.failure) {
      facts.push([
        "Error",
        outcome.error_px === null ? "Failed" : `Failed, ${px(outcome.error_px, 3)} off`,
        outcome.estimate ? estimateSaid(outcome.estimate) : "It gave no estimate, so it has no error to give.",
      ]);
    } else {
      facts.push([
        "Error",
        [px(outcome.error_px, 3), onGround(outcome.error_px)],
        "How far its estimate is from the true shift, on average. Lower is better.",
        estimateSaid(outcome.estimate),
      ]);
    }
    const ground = "Nothing changed on the ground, so every flagged pixel is a mistake.";
    const flaggedShare = "The share of the picture flagged as changed";
    if (none) {
      facts.push([
        "False changes",
        percent(before.changed_share),
        `${flaggedShare}. ${ground}`,
        `${count(before.changed_px)} of the ${count(before.counted_px)} pixels the detector counts.`,
      ]);
    } else if (outcome.changed_share === null) {
      facts.push([
        "False changes",
        `${percent(before.changed_share)} before`,
        `${flaggedShare} before correction. There is no corrected image to count after. ${ground}`,
        `${count(before.changed_px)} of the ${count(before.counted_px)} pixels the detector counts.`,
      ]);
    } else {
      facts.push([
        "False changes",
        fromTo(percent(before.changed_share), percent(outcome.changed_share)),
        `${flaggedShare}, before and after correction. ${ground}`,
        `${count(before.changed_px)} of the ${count(before.counted_px)} pixels the detector counts, then ` +
          `${count(outcome.changed_px)} of ${count(outcome.counted_px)}.`,
      ]);
    }
    setFacts($("slider-facts"), facts);
  };

  // On arrival the divider moves once, to show that it moves. Any touch stops it.
  let glide = 0;
  let landing = 50;
  const settle = () => {
    if (!glide) return;
    cancelAnimationFrame(glide);
    glide = 0;
    // Stopped on the way, the divider goes where it was heading.
    state.split = landing;
    place();
  };
  const arrive = () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const from = 88;
    const to = state.split;
    landing = to;
    const waits = 500;
    const lasts = 1200;
    let began = null;
    const step = (now) => {
      if (began === null) began = now;
      const done = clamp((now - began - waits) / lasts, 0, 1);
      state.split = from + (to - from) * (1 - (1 - done) ** 3);
      place();
      glide = done < 1 ? requestAnimationFrame(step) : 0;
    };
    state.split = from;
    place();
    glide = requestAnimationFrame(step);
  };

  const dragging = { on: false, pan: false, x: 0, y: 0, box: null };
  frame.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    settle();
    const box = frame.getBoundingClientRect();
    const divider = box.left + (box.width * state.split) / 100;
    // Zoomed, the picture moves under the pointer, and the divider by its handle.
    const pan = state.zoom > 1 && Math.abs(event.clientX - divider) > 22;
    Object.assign(dragging, { on: true, pan, x: event.clientX, y: event.clientY, box });
    frame.setPointerCapture(event.pointerId);
    frame.classList.toggle("moving", pan);
    if (!pan) {
      state.split = clamp(((event.clientX - box.left) / box.width) * 100, 0, 100);
      place();
    }
  });
  frame.addEventListener("pointermove", (event) => {
    if (!dragging.on) return;
    const { box } = dragging;
    if (dragging.pan) {
      state.cx -= (event.clientX - dragging.x) / (box.width * state.zoom);
      state.cy -= (event.clientY - dragging.y) / (box.height * state.zoom);
      dragging.x = event.clientX;
      dragging.y = event.clientY;
    } else {
      state.split = clamp(((event.clientX - box.left) / box.width) * 100, 0, 100);
    }
    place();
  });
  for (const type of ["pointerup", "pointercancel"]) {
    frame.addEventListener(type, () => {
      dragging.on = false;
      frame.classList.remove("moving");
    });
  }
  frame.addEventListener("keydown", (event) => {
    // The divider's own keys are the range's: the picture moves only from the frame.
    if (state.zoom === 1 || event.target !== frame) return;
    const step = 1 / (8 * state.zoom);
    const moves = {
      ArrowLeft: [-step, 0],
      ArrowRight: [step, 0],
      ArrowUp: [0, -step],
      ArrowDown: [0, step],
    };
    const move = moves[event.key];
    if (!move) return;
    event.preventDefault();
    state.cx += move[0];
    state.cy += move[1];
    place();
  });
  $("split").addEventListener("input", (event) => {
    // Read first: stopping the arrival writes the divider's place back.
    const asked = Number(event.target.value);
    settle();
    state.split = asked;
    place();
  });

  // --- the arrows ----------------------------------------------------------

  const round = (value) => Math.round(value * 100) / 100;

  // One arrow from a point to where it goes; a dot when it goes nowhere to speak of.
  const arrow = (x, y, u, v) => {
    const length = Math.hypot(u, v);
    if (length < 0.6) return `M${x} ${y}h0.01`;
    const tipX = round(x + u);
    const tipY = round(y + v);
    const barb = Math.min(3.2, length * 0.45);
    const angle = Math.atan2(v, u);
    const barbs = [angle + 2.6, angle - 2.6].map(
      (turned) => `${round(tipX + barb * Math.cos(turned))} ${round(tipY + barb * Math.sin(turned))}`
    );
    return `M${x} ${y}L${tipX} ${tipY}M${barbs[0]}L${tipX} ${tipY}L${barbs[1]}`;
  };

  // A field on the grid of the file. Where `observed` says the truth cannot be
  // seen, a ring stands for the arrow: there is no error to draw there.
  const drawField = (svg, grid, dx, dy, gain, observed) => {
    let path = "";
    const rings = [];
    grid.rows.forEach((row, i) => {
      grid.cols.forEach((col, j) => {
        const x = col + 0.5;
        const y = row + 0.5;
        if (observed && !observed[i][j]) {
          rings.push(svgEl("circle", { cx: x, cy: y, r: 1.7, class: "arrows-hidden" }));
        } else {
          path += arrow(x, y, dx[i][j] * gain, dy[i][j] * gain);
        }
      });
    });
    svg.replaceChildren(
      svgEl("path", { d: path, class: "arrows-under" }),
      svgEl("path", { d: path, class: "arrows-over" }),
      ...rings
    );
    return rings.length;
  };

  const fieldSaid = (estimate) => {
    if (estimate.model === "translation") {
      return "It estimates one shift for the whole image, so all its arrows are the same.";
    }
    if (estimate.model === "affine") {
      return "It estimates an affine transform, so its arrows change evenly across the image.";
    }
    if (estimate.model === "dense") return "It estimates a displacement at every pixel.";
    return "";
  };

  const drawArrows = ({ directory, arrows }) => {
    const outcome = arrows.methods[state.method];
    const name = methodName(state.method);
    const none = state.method === NONE;
    const { grid, truth, observed } = arrows;
    const step = grid.step_px;
    const size = manifest.size_px;
    $("arrow-step").textContent = `${step} px (${metres(step)})`;
    for (const part of ["truth", "estimate", "error"]) {
      $(`field-${part}`).setAttribute("viewBox", `0 0 ${size} ${size}`);
      $(`field-image-${part}`).src = directory + arrows.image;
    }

    drawField($("field-truth"), grid, truth.dx, truth.dy, FIELD_GAIN, null);
    $("field-truth-caption").textContent =
      `The true field, over the reference image: up to ${px(truth.max_px)}. ` +
      `Arrows are drawn at ${FIELD_GAIN} times their length.`;

    const drawn = outcome.dx !== null;
    $("missing-estimate").hidden = drawn;
    $("missing-error").hidden = drawn;
    $("pick-gain").closest("fieldset").disabled = !drawn;
    setFailure($("arrows-failure"), outcome);

    if (drawn) {
      drawField($("field-estimate"), grid, outcome.dx, outcome.dy, FIELD_GAIN, null);
      $("field-estimate-caption").textContent = none
        ? "With no registration, the estimate is no displacement at all: every arrow is a point."
        : `What ${name} estimates, at the same scale.`;

      let longest = 0;
      grid.rows.forEach((_, i) => {
        grid.cols.forEach((_, j) => {
          if (observed[i][j]) {
            longest = Math.max(longest, Math.hypot(outcome.error_dx[i][j], outcome.error_dy[i][j]));
          }
        });
      });
      const fitting = ERROR_GAINS.filter((gain) => longest * gain <= step);
      const gain = state.gain === "auto" ? fitting.pop() || ERROR_GAINS[0] : Number(state.gain);
      const rings = drawField($("field-error"), grid, outcome.error_dx, outcome.error_dy, gain, observed);
      $("field-error-caption").textContent =
        `The error, estimate minus truth, drawn at ${gain} times its length.` +
        (rings
          ? ` A ring marks one of the ${rings} points whose true position cannot be seen in the moving image, ` +
            "under cloud or out of the frame: no error is counted there."
          : "");
      $("gain-note").textContent =
        `At ${gain}×, an error arrow as long as the gap between two arrows is an error of ${px(step / gain, 2)}.` +
        (state.gain === "auto"
          ? " Fit takes the largest of the four that keeps the arrows apart, so it changes with the method."
          : "");
    } else {
      $("field-estimate").replaceChildren();
      $("field-error").replaceChildren();
      $("missing-estimate").textContent = `${name} gave no estimate on this pair.`;
      $("missing-error").textContent = "No estimate, so no error to draw.";
      $("field-estimate-caption").textContent = `What ${name} estimates: nothing here.`;
      $("field-error-caption").textContent = "The error, estimate minus truth: none without an estimate.";
      $("gain-note").textContent = "";
    }

    const facts = [
      [
        "True field",
        [`up to ${px(truth.max_px)}`, onGround(truth.max_px)],
        "The slider's pair again, same window and same shift at its centre, " +
          "with a small rotation, scale, shear and local field added.",
        `dx ${px(truth.mean_dx)}, dy ${px(truth.mean_dy)} on average.`,
      ],
    ];
    if (none) {
      facts.push([
        "Error with no registration",
        [px(outcome.error_px), onGround(outcome.error_px)],
        "Nothing is corrected, so the whole displacement is left, averaged over the image.",
      ]);
    } else if (outcome.failure) {
      facts.push([
        "Error",
        outcome.error_px === null ? "Failed" : `Failed, ${px(outcome.error_px, 3)} off`,
        outcome.estimate ? fieldSaid(outcome.estimate) : "It gave no estimate, so it has no error to give.",
      ]);
    } else {
      facts.push([
        "Error",
        [px(outcome.error_px, 3), onGround(outcome.error_px)],
        "How far its arrows are from the true ones, on average. Lower is better.",
        "Averaged over the pixels whose true position can be seen in the moving image. " +
          fieldSaid(outcome.estimate),
      ]);
    }
    setFacts($("arrows-facts"), facts);
  };

  const drawNotes = ({ pair }) => {
    const site = manifest.sites.find((entry) => entry.name === state.site);
    const day = new Date(site.acquired).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
      timeZone: "UTC",
    });
    const landscape = SITES[site.name] ? `, ${SITES[site.name][1]}` : "";
    $("pair-note").textContent =
      `${siteName(site.name)}${landscape}. Pair ${site.pair} of the benchmark for this site: ` +
      `a ${site.window.size} × ${site.window.size} px window, ${fixed((site.window.size * PIXEL_M) / 1000, 2)} km ` +
      `across at ${PIXEL_M} m a pixel, of the Sentinel-2 scene ${site.scene}, ` +
      `acquired on ${day}.`;
    const cloud = pair.cloud_fraction
      ? ` Cloud covers about ${percent(pair.cloud_fraction, 0)} of the moving image.`
      : "";
    $("preset-note").textContent = PRESETS[state.preset]
      ? `${presetName(state.preset)} preset: ${PRESETS[state.preset][1]}${cloud}`
      : "";
  };

  let turn = 0;
  const draw = async () => {
    const mine = ++turn;
    const loaded = await cell(state.site, state.preset);
    // A later pick may have come while the files were read.
    if (mine !== turn) return;
    shown = loaded;
    drawNotes(shown);
    drawSlider(shown);
    drawArrows(shown);
  };

  // --- the cost curve --------------------------------------------------------

  // One entry per row of the two curve files, with what each machine has for it.
  const curveItems = (points, references) => {
    const items = points.map((row) => ({
      key: row.method,
      kind: "raft",
      model: row.model,
      weights: row.weights,
      refinements: Number(row.refinements),
      name: `RAFT ${row.model}, ${row.weights}`,
      m1: {
        error: figure(row.mean_epe),
        failures: figure(row.failure_rate),
        time: figure(row.time_ms),
        memory: figure(row.memory_mib),
      },
      // The T4 has a time alone; the error beside it is PyTorch's, read on the M1.
      t4: {
        error: figure(row.torch_mean_epe),
        failures: figure(row.torch_failure_rate),
        time: figure(row.gpu_time_ms),
        memory: null,
      },
    }));
    for (const row of references) {
      // A method named with _r4 or _r8 runs fewer refinements than the 12 of training.
      const int8 = /^raft_ft(?:_r(\d+))?_onnx_int8$/.exec(row.method);
      items.push({
        key: row.method,
        kind: int8 ? "int8" : "classic",
        model: int8 ? "large" : null,
        weights: int8 ? "fine-tuned" : null,
        refinements: int8 ? Number(int8[1] || 12) : null,
        name: int8 ? "RAFT large, fine-tuned, int8 copy" : CLASSIC[row.method] || row.method,
        m1: {
          error: figure(row.mean_epe),
          failures: figure(row.failure_rate),
          time: figure(row.time_ms),
          memory: figure(row.memory_mib),
        },
        t4: null,
      });
    }
    return items;
  };

  const CHARTS = [
    {
      id: "chart-error",
      x: "time",
      y: "error",
      log: true,
      xTitle: "time of one call (ms)",
      yTitle: "error (px)",
    },
    {
      id: "chart-failures",
      x: "time",
      y: "failures",
      log: true,
      xTitle: "time of one call (ms)",
      yTitle: "failed pairs (%)",
    },
    {
      id: "chart-memory",
      x: "memory",
      y: "error",
      log: false,
      m1Only: true,
      xTitle: "memory added (MiB)",
      yTitle: "error (px)",
    },
  ];
  const scaled = (item, machine, axis) =>
    axis === "failures" ? item[machine].failures * 100 : item[machine][axis];

  const linearAxis = (largest) => {
    const rough = (largest || 1) / 4;
    const power = 10 ** Math.floor(Math.log10(rough));
    const step = [1, 2, 2.5, 5, 10].map((times) => times * power).find((value) => value >= rough);
    const top = Math.ceil((largest || 1) / step - 1e-9) * step;
    const ticks = [];
    for (let value = 0; value <= top + step / 2; value += step) ticks.push(Number(value.toPrecision(6)));
    return { ticks, at: (value) => value / top };
  };
  const logAxis = (smallest, largest) => {
    const low = Math.log10(smallest / 1.35);
    const high = Math.log10(largest * 1.35);
    const steps = high - low < 1 ? [1, 1.5, 2, 3, 5, 7] : [1, 2, 5];
    const ticks = [];
    for (let power = Math.floor(low); power <= Math.ceil(high); power += 1) {
      for (const times of steps) {
        const value = times * 10 ** power;
        if (Math.log10(value) >= low && Math.log10(value) <= high) ticks.push(Number(value.toPrecision(6)));
      }
    }
    return { ticks, at: (value) => (Math.log10(value) - low) / (high - low) };
  };

  const marker = (item, x, y) => {
    if (item.kind === "classic") {
      return svgEl("path", {
        class: "mark cross",
        d: `M${x - 4.2} ${y - 4.2}L${x + 4.2} ${y + 4.2}M${x + 4.2} ${y - 4.2}L${x - 4.2} ${y + 4.2}`,
      });
    }
    const filled = item.weights === "fine-tuned" ? "solid" : "hollow";
    if (item.kind === "int8") {
      return svgEl("path", {
        class: `mark ${filled}`,
        d: `M${x} ${y - 5.5}L${x + 5.5} ${y}L${x} ${y + 5.5}L${x - 5.5} ${y}Z`,
      });
    }
    if (item.model === "small") {
      return svgEl("rect", { class: `mark ${filled}`, x: x - 4.2, y: y - 4.2, width: 8.4, height: 8.4 });
    }
    return svgEl("circle", { class: `mark ${filled}`, cx: x, cy: y, r: 4.6 });
  };
  const colour = (item) => {
    if (item.kind !== "raft") return "c-ref";
    return item.model === "small" ? "c-small" : "c-large";
  };

  const overlaps = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];

  const drawChart = (chart) => {
    const svg = $(chart.id);
    const machine = chart.m1Only ? "m1" : state.machine;
    const items = curve.filter(
      (item) => item[machine] && item[machine][chart.x] !== null && item[machine][chart.y] !== null
    );
    // Drawn at the size the page gives it, one unit a pixel, so the text keeps its size.
    const box = svg.getBoundingClientRect();
    const width = Math.round(box.width);
    const height = Math.round(box.height);
    if (width < 120 || height < 120) return;
    const left = 38;
    const right = 16;
    const top = 30;
    const bottom = 44;
    const xs = items.map((item) => scaled(item, machine, chart.x));
    const ys = items.map((item) => scaled(item, machine, chart.y));
    const xAxis = chart.log ? logAxis(Math.min(...xs), Math.max(...xs)) : linearAxis(Math.max(...xs));
    const yAxis = linearAxis(Math.max(...ys));
    const X = (value) => round(left + xAxis.at(value) * (width - left - right));
    const Y = (value) => round(height - bottom - yAxis.at(value) * (height - top - bottom));
    const nodes = [];

    for (const tick of yAxis.ticks) {
      nodes.push(svgEl("line", { class: "grid", x1: left, x2: width - right, y1: Y(tick), y2: Y(tick) }));
      nodes.push(svgEl("text", { x: left - 6, y: Y(tick) + 4, "text-anchor": "end" }, String(tick)));
    }
    nodes.push(
      svgEl("line", { class: "axis", x1: left, x2: width - right, y1: height - bottom, y2: height - bottom })
    );
    for (const tick of xAxis.ticks) {
      const x = left + xAxis.at(tick) * (width - left - right);
      nodes.push(svgEl("line", { class: "axis", x1: x, x2: x, y1: height - bottom, y2: height - bottom + 4 }));
      nodes.push(svgEl("text", { x, y: height - bottom + 18, "text-anchor": "middle" }, String(tick)));
    }
    nodes.push(svgEl("text", { class: "axis-title", x: 0, y: 12 }, chart.yTitle));
    nodes.push(
      svgEl(
        "text",
        { class: "axis-title", x: left + (width - left - right) / 2, y: height - 4, "text-anchor": "middle" },
        chart.xTitle
      )
    );

    // One line per model and weights, through its 4, 8 and 12 refinements.
    const lines = new Map();
    for (const item of items) {
      if (item.refinements === null) continue;
      const key = `${item.kind} ${item.model} ${item.weights}`;
      if (!lines.has(key)) lines.set(key, []);
      lines.get(key).push(item);
    }
    for (const members of lines.values()) {
      members.sort((a, b) => a.refinements - b.refinements);
      const dashed = members[0].weights === "pretrained" ? " dashed" : "";
      nodes.push(
        svgEl("polyline", {
          class: `line ${colour(members[0])}${dashed}`,
          points: members
            .map((item) => `${X(scaled(item, machine, chart.x))},${Y(scaled(item, machine, chart.y))}`)
            .join(" "),
        })
      );
    }

    // A label goes where it hides no point and no other label, or is left out:
    // the hover and the table say the same.
    const at = new Map(
      items.map((item) => [item, [X(scaled(item, machine, chart.x)), Y(scaled(item, machine, chart.y))]])
    );
    const taken = [...at.values()].map(([x, y]) => [x - 6, y - 6, x + 6, y + 6]);
    const labelled = [...items].sort((a, b) => (b.kind === "classic") - (a.kind === "classic"));
    const labels = new Map();
    for (const item of labelled) {
      const [x, y] = at.get(item);
      const text = item.refinements === null ? item.name : String(item.refinements);
      const wide = text.length * 6.7;
      const places = {
        above: { x, y: y - 10, anchor: "middle", box: [x - wide / 2, y - 21, x + wide / 2, y - 9] },
        below: { x, y: y + 19, anchor: "middle", box: [x - wide / 2, y + 8, x + wide / 2, y + 20] },
        right: { x: x + 10, y: y + 4, anchor: "start", box: [x + 9, y - 7, x + 10 + wide, y + 7] },
        left: { x: x - 10, y: y + 4, anchor: "end", box: [x - 10 - wide, y - 7, x - 9, y + 7] },
        upRight: { x: x + 7, y: y - 9, anchor: "start", box: [x + 6, y - 20, x + 7 + wide, y - 8] },
        upLeft: { x: x - 7, y: y - 9, anchor: "end", box: [x - 7 - wide, y - 20, x - 6, y - 8] },
      };
      let order = ["above", "right", "below", "left", "upRight", "upLeft"];
      if (item.kind === "classic") order = ["right", "left", "above", "below", "upRight", "upLeft"];
      else if (item.kind === "raft" && item.weights === "fine-tuned") order = ["below", "above", "right", "left"];
      const own = taken[items.indexOf(item)];
      const free = order
        .map((name) => places[name])
        .find(
          ({ box }) =>
            box[0] >= 0 &&
            box[2] <= width &&
            box[1] >= top - 14 &&
            box[3] <= height - bottom - 1 &&
            !taken.some((other) => other !== own && overlaps(box, other))
        );
      if (free) {
        // Kept a few pixels apart, so that two numbers side by side do not read as one.
        taken.push([free.box[0] - 4, free.box[1], free.box[2] + 4, free.box[3]]);
        labels.set(item, svgEl("text", { x: round(free.x), y: round(free.y), "text-anchor": free.anchor }, text));
      }
    }

    for (const item of items) {
      const [x, y] = at.get(item);
      const point = svgEl("g", {
        class: `point ${colour(item)}`,
        "data-key": item.key,
        role: "img",
        "aria-label": `${title(item)}. ${said(item, machine).join(". ")}.`,
      });
      point.append(svgEl("circle", { class: "hit", cx: x, cy: y, r: 12 }), marker(item, x, y));
      if (labels.has(item)) point.append(labels.get(item));
      point.addEventListener("pointerenter", () => tell(item, machine, point));
      point.addEventListener("pointerleave", (event) => {
        // A finger leaves as soon as it lifts: what a tap showed stays until the next tap.
        if (event.pointerType !== "touch") hush();
      });
      nodes.push(point);
    }
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.replaceChildren(...nodes);
  };

  // What the files hold for a point on a machine, and nothing they do not.
  const said = (item, machine) => {
    const values = item[machine];
    const lines = [`Error: ${fixed(values.error, 4)} px`, `Failed pairs: ${percent(values.failures, 1)}`];
    if (machine === "m1") {
      lines.push(`Time on the M1: ${milliseconds(values.time)}`);
      lines.push(`Memory added on the M1: ${mebibytes(values.memory)}`);
    } else {
      lines.push(`Time on the T4: ${milliseconds(values.time)}`);
      lines.push("Memory: read on the M1 alone");
    }
    return lines;
  };
  const title = (item) =>
    item.refinements === null ? item.name : `${item.name}, ${item.refinements} refinements`;

  const tip = $("tip");
  const hush = () => {
    tip.hidden = true;
    for (const point of document.querySelectorAll(".point.on")) point.classList.remove("on");
  };
  const tell = (item, machine, point) => {
    hush();
    for (const twin of document.querySelectorAll(".point")) {
      if (twin.dataset.key === item.key) twin.classList.add("on");
    }
    tip.replaceChildren(el("strong", title(item)), ...said(item, machine).map((line) => el("span", line)));
    tip.hidden = false;
    const host = $("charts").getBoundingClientRect();
    const box = point.querySelector(".hit").getBoundingClientRect();
    const x = clamp(box.left + box.width / 2 - host.left - tip.offsetWidth / 2, 0, host.width - tip.offsetWidth);
    const above = box.top - tip.offsetHeight - 6;
    const y = above < 0 ? box.bottom + 6 : above;
    tip.style.left = `${x}px`;
    tip.style.top = `${y - host.top}px`;
  };
  document.addEventListener("pointerdown", (event) => {
    if (!event.target.closest || !event.target.closest(".point")) hush();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hush();
  });

  const drawCurve = () => {
    CHARTS.forEach(drawChart);
    const t4 = state.machine === "t4";
    const timed = curve.filter((item) => item.t4 && item.t4.time !== null).length;
    const left = curve.length - timed;
    $("machine-note").textContent = t4
      ? `A T4 GPU, under PyTorch. The files hold a T4 time for the ${timed} RAFT points only: ` +
        `the ${left} other rows, the int8 copies and the classic methods, have none and are not drawn against time. ` +
        "The error and the failed pairs beside a T4 time are the same models' under PyTorch, read on the M1's CPU. " +
        "Memory was read on the M1 only, so the memory chart does not change."
      : "An Apple M1 laptop, on its CPU: RAFT is run by ONNX Runtime, " +
        "the classic methods by their own libraries. Every row of the files is drawn.";
    $("chart-error-caption").textContent =
      `Error against the time of one call on the ${t4 ? "T4" : "M1"}: lower is more accurate, ` +
      "further left is faster. The time axis is logarithmic: equal steps are equal ratios.";
    $("chart-failures-caption").textContent =
      `Failed pairs against the time of one call on the ${t4 ? "T4" : "M1"}: lower fails less, ` +
      "further left is faster.";
    $("chart-memory-caption").textContent =
      "Error against the memory a method adds to a process, on the M1: further left needs less." +
      (t4 ? " The files hold no memory figure for the T4." : "");
  };

  const drawTable = () => {
    const cellOf = (text, className) => el("td", text, className);
    $("curve-table")
      .querySelector("tbody")
      .replaceChildren(
        ...curve.map((item) => {
          const row = el("tr");
          const head = el("th", item.name);
          head.scope = "row";
          row.append(
            head,
            cellOf(item.refinements === null ? "" : String(item.refinements), "num"),
            cellOf(fixed(item.m1.error, 4), "num"),
            cellOf(percent(item.m1.failures, 1), "num"),
            cellOf(fixed(item.m1.time, item.m1.time >= 100 ? 0 : 1), "num"),
            cellOf(fixed(item.m1.memory, 1), "num"),
            cellOf(item.t4 && item.t4.time !== null ? fixed(item.t4.time, 1) : "", "num")
          );
          return row;
        })
      );
  };

  // --- start -----------------------------------------------------------------

  const start = async () => {
    manifest = await read("manifest.json", "json");
    const named = (end) => manifest.curve.find((path) => path.endsWith(end));
    const [points, references] = await Promise.all(
      ["curve-points.csv", "curve-references.csv"].map((end) => read(named(end), "text").then(table))
    );
    curve = curveItems(points, references);

    state.site = manifest.sites[0].name;
    state.preset = manifest.presets[0];
    state.method = manifest.methods.includes(FIRST_METHOD) ? FIRST_METHOD : manifest.methods[0];

    // A browser may put back, on a reload, the choices the page was left with.
    for (const name of ["view", "zoom", "gain", "machine"]) {
      const chosen = document.querySelector(`input[name="${name}"]:checked`);
      if (chosen) state[name] = name === "zoom" ? Number(chosen.value) : chosen.value;
    }

    choice("site", manifest.sites.map((site) => site.name), siteName);
    choice("preset", manifest.presets, presetName);
    choice("method", manifest.methods, (name) => (METHODS[name] ? METHODS[name].pick : name));

    const pairs = Number(points[0].pairs).toLocaleString("en-US");
    for (const node of document.querySelectorAll("#curve-pairs, .curve-pairs")) node.textContent = pairs;
    for (const node of document.querySelectorAll(".threshold")) {
      node.textContent = manifest.failure_threshold_px;
    }
    $("rule-shift").textContent = manifest.rule.min_shift_px;
    $("notice").textContent = manifest.notice;

    onPick("pick-view", (value) => {
      state.view = value;
      settle();
      drawSlider(shown);
    });
    onPick("pick-zoom", (value) => {
      state.zoom = Number(value);
      place();
      drawSlider(shown);
    });
    onPick("pick-gain", (value) => {
      state.gain = value;
      drawArrows(shown);
    });
    onPick("pick-machine", (value) => {
      state.machine = value;
      hush();
      drawCurve();
    });

    place();
    await draw();
    $("main").hidden = false;
    arrive();
    // The curve is drawn once it is laid out, and again whenever its room changes.
    drawCurve();
    drawTable();
    let sized = 0;
    let last = $("charts").clientWidth;
    new ResizeObserver(() => {
      const now = $("charts").clientWidth;
      if (now === last) return;
      last = now;
      cancelAnimationFrame(sized);
      sized = requestAnimationFrame(() => {
        hush();
        CHARTS.forEach(drawChart);
      });
    }).observe($("charts"));
  };

  start().catch((error) => {
    const host = $("load-error");
    host.hidden = false;
    host.replaceChildren(
      el("strong", "The demo files could not be read. "),
      `${error.message}. If this page was opened as a file, serve the docs folder instead: `,
      el("code", "python -m http.server --directory docs"),
      " from the repository's folder, then open ",
      el("code", "localhost:8000"),
      "."
    );
  });
})();
