# GOAT in moum layout

Generated from `/home/ajou/yigyu/guitar_project/tablature/data/GOAT`.

This is a separate output tree; the existing `moum` data was not modified.
Audio files are symbolic links to the extracted GOAT release, so the source
directory must remain available.

## Layout

```text
/home/ajou/yigyu/3/data/moum_goat/
  audio/
    GOAT_DI/item_0.wav
    GOAT_amp_1/item_0.wav ... GOAT_amp_5/item_0.wav
  annotation/
    integrated_guitar_data.csv
    train_guitar_data.csv
    test_guitar_data.csv
    goat_notes_di.csv
    GOAT_metadata.csv
    GOAT_raw/               # GP5, GP, DadaGP text and MIDI symlinks
```

The canonical manifests contain the DI recording plus five amplifier
variants.  `*_di.csv` contains only the DI recording for a clean baseline.
The official GOAT train/test item split is preserved across all variants, so
amplifier renders from one item never cross the split boundary.

The CSV uses the current Conformer v1 schema:
`unique_id,directory_name,audio_name,string,start,end,pitch,source`.
GP strings are converted from GP's high-to-low numbering to moum's
low-to-high zero-based numbering.  Pitches use each GP5 score's actual string
tuning.  The current v1 loader's MIDI range is 40--88; rows outside that range
are retained in the CSV but are ignored by that loader until its range is
expanded.

See `conversion_report.json` for counts and per-item alignment details.
