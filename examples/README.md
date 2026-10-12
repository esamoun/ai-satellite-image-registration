# Demo pairs

Contains modified Copernicus Sentinel data 2025.

These are the demo pairs of the project's page: for each site, one pair of the
benchmark, picked by a rule on its ground truth (the first pair of the site
whose true shift is over 2 px), under the `clean` and `hard` presets.
`satreg demo` wrote them; `manifest.json` gives each pair's site, scene, window
in the site image and true displacement.

Each `<site>/<preset>/` holds `reference.tif` and two moving images of it:
`moving_translation.tif`, shifted as a whole, and `moving_dense.tif`, moved by
a field that varies from pixel to pixel, given in `<site>/truth_dense.tif`
(`dy` then `dx`, in pixels).

```bash
satreg register examples/beauce/clean/reference.tif \
    examples/beauce/clean/moving_translation.tif \
    --method phase_correlation --out out/
```

moving(p + d) = reference(p): the content at pixel p of the reference is found at p + d in the moving image; d = (dy, dx) in pixels, rows down
