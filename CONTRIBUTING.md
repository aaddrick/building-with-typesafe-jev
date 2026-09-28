# Contributing

Corrections and new prior art are welcome.

## Fix a fact

Jev changes fast. If a fact in the skill is wrong, open an issue or a pull request with a link to the source: a page on docs.typesafe.ai, an SDK changelog, or a live API response. Do not paste an API key into an issue.

## Add prior art

Add the project to the shape file that matches how it works, not what domain it serves. `skills/building-with-typesafe-jev/prior-art/INDEX.md` lists the shapes. Each entry needs:

- one line on how the project uses Jev (which primitives, which loop),
- a link to the code or write-up,
- any number the author reports, marked as reported.

A project that tried Jev and found it a bad fit is just as useful. Add it to "Known bad fits" in `INDEX.md`.

## Before you open a pull request

```bash
python3 scripts/check_configs.py
python3 -m unittest discover -s tests -v
```

If you change an install command in `README.md`, change it in every file under `.github/readme/` too. The tests check that the commands match.

If you change the hero text, regenerate the card with `python3 scripts/make_card.py` (needs Pillow and NumPy) and commit the PNG.

## Screenshots

The README walkthroughs use images from `scripts/annotate_screens.py`, which blurs account details and draws the step highlights. The raw captures show account details, and the API key ones a live key, so they never go in the repo. Keep them outside the repo and check every output image for anything unmasked before you commit.

- **API key flow** (`.github/assets/api-key/`): capture the four console screens at 1512x807, run `python3 scripts/annotate_screens.py api-key /path/to/raw-dir`, then revoke the key you created for the capture.
- **Plugin marketplace flow** (`.github/assets/plugin-marketplace/`): capture the five claude.ai screens at 1510x812 in the dark theme, starting with no marketplace added (remove it under **Customize > Plugins > Add > Manage marketplaces**), then run `python3 scripts/annotate_screens.py plugin-marketplace /path/to/raw-dir`.

The script's docstring lists the file names each flow expects.
