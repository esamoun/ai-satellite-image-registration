# The benchmark chip of the container image

Contains modified Copernicus Sentinel data 2025.

`chips/beauce/B04_84ca7aa954b2.tif` is the Beauce benchmark chip: 1,024 px a
side, band B04, uint16, on its UTM 31N grid, cut from the scene
`S2B_T31UCP_20250701T110241_L2A`, which its tags name. It is the file
`satreg fetch` wrote to `data/chips/` on the M1, byte for byte, and the chip
the published figures of Beauce were made on.

The `Dockerfile` copies this directory to `data/` in the container image, where
`satreg benchmark` looks for a site's chip before it asks the catalogue. The
small benchmark of the container image (`configs/container-image.toml`) then
runs with no network, on the scene of the published tables.

The file name ends with a hash of Beauce's entry in `configs/sites.toml` and of
the catalogue's parameters. Editing either changes the name `satreg` looks for, and a
test fails until this file follows.

`data/` at the root of the repository is still what `satreg fetch` downloads
to, and is not committed. Why this one chip is: `docs/decisions.md`, entry of
2026-10-13.
