# AI Object Lab model library

Browser-ready 3D assets used by the AI Object Lab skill. The catalog supports
Russian, Kazakh and English aliases and records what each model can and cannot
be used to explain.

## First release

| Model | Format | Approx. size | Intended use |
| --- | --- | ---: | --- |
| Four-cylinder engine-block scan | GLB | 7.0 MB | Realistic block and cylinder-geometry inspection |
| ASUS ROG Strix B550-F motherboard | GLB | 8.1 MB | Detailed motherboard layout and connectors |
| Disc-brake educational model | GLB | 0.2 MB | Selectable parts and exploded-view explanation |

The engine scan and motherboard carry CC BY 4.0 attribution requirements. The
original disc-brake model is CC0. See `LICENSES.md` for full credit and changes.

## Stable URLs

The skill reads `catalog/catalog.json`. Model URLs are built from its
`base_url` plus each model's `file` field. Keep paths stable after publishing;
add a new catalog record rather than silently replacing a substantially
different model.

## Upload this package

Open the GitHub repository, choose **Add file → Upload files**, and drag all
contents of this folder into the upload area. Commit directly to `main` for the
initial release.

## Quality rules

- Include a model only when its licence and source are recorded.
- Prefer GLB below 15 MB for classroom networks and ordinary laptops.
- State whether parts, exploded view and animation genuinely work.
- Never describe a visual reconstruction as an exact CAD model.
- Do not use these files for repair, diagnosis, safety inspection or exact
  measurement.

## Regenerating the disc brake

The disc-brake file is deterministic and can be rebuilt with Python 3 plus
`numpy` and `trimesh`:

```bash
python scripts/generate_disc_brake.py
```

Run `python scripts/validate_catalog.py` before committing an update.
