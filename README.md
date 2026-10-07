# rTMS ADAS-Cog Prediction

Analysis code and manuscript sources for:

**Predicting Long-Term ADAS-Cog Change From Early Response After Repetitive
Transcranial Magnetic Stimulation in Alzheimer Disease**

Authors: Mohammad Alamgir Chowdhury and Hina Shaheen.

## Files

- `project_rTMS_clean_analysis.py`: clean Python analysis supplied on October 5, 2026,
  with portable input/output paths.
- `requirements.txt`: Python dependencies derived from the imports and Excel input.
- `manuscript/rtms_standalone_manuscript.tex`: supplied main manuscript source.
- `manuscript/rtms_supplement.tex`: supplied supplementary manuscript source.
- `manuscript/references_rtms.bib`: supplied manuscript bibliography.
- `data/README.md`: description of the required workbook and its current availability.

The uploaded manuscript sources are the supplied October 5 versions. They have
not been independently checked against a newer journal submission.

## Data availability

The participant-level Excel workbook is **not included** in this public repository.
Public release authorization has not been confirmed. The analysis requires the
original workbook; this code upload does not establish public availability of the
clinical dataset. No data-access contact or access agreement is asserted here.

## Run the analysis

Use Python 3 with a scikit-learn version that supports
`OneHotEncoder(sparse_output=False)`. Exact original package versions are not
available; `requirements.txt` is an unpinned dependency list, not a locked environment.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Place the authorized workbook in `data/` under the filename
`rTMS participants pre-post info.xlsx`, then run from the repository root:

```bash
python project_rTMS_clean_analysis.py
```

Alternatively, on macOS/Linux point to a workbook stored elsewhere:

```bash
RTMS_DATA_FILE="/absolute/path/rTMS participants pre-post info.xlsx" python project_rTMS_clean_analysis.py
```

The required sheet is `weston_export-2`. The corrected total-score column used
by the script is `ADAS-Cog-Recog Total Score`. See `data/README.md` for the schema.

Optional environment variables:

- `RTMS_DATA_FILE`: path to the input workbook.
- `RTMS_OUTPUT_DIR`: output directory; defaults to `outputs/` beside the script.
- `RTMS_N_JOBS`: parallel job count; defaults to `-1`. Use `1` for lower memory use.

## Analysis and outputs

The supplied analysis includes participant flow and descriptive summaries,
Week-5 landmark prediction, nested predictor-set comparisons, ridge regression,
multi-task elastic net, restricted random forest, mixed-effects comparisons,
paired participant-level bootstrap comparisons, calibration, and coefficient summaries.
The code specifies repeated 5-fold cross-validation with five repetitions and
10,000 bootstrap resamples. Full execution can be computationally intensive.

Generated output folders are:

- `outputs/manuscript_figures/`: figures 1-8 and S1, in PNG and PDF formats.
- `outputs/rtms_ml_results/`: model metrics and prediction outputs.
- `outputs/rtms_clean_results/`: saved summary tables.

Generated outputs are excluded from Git by default. Some prediction arrays and
console previews contain participant-level information; inspect them before
choosing to publish additional results.

## Compile the manuscript

The original figure PDFs were not available as separate files at the time of
this upload. Run the analysis and copy its generated PDF figures into
`manuscript/figures/`. From `manuscript/`, run:

```bash
pdflatex rtms_standalone_manuscript.tex
bibtex rtms_standalone_manuscript
pdflatex rtms_standalone_manuscript.tex
pdflatex rtms_standalone_manuscript.tex
pdflatex rtms_supplement.tex
pdflatex rtms_supplement.tex
```

## Upload validation

The Python source passed a syntax check. Repository preparation changed only
input/output paths; statistical calculations were not changed. The complete
analysis was not rerun during this upload, so reproduced results and manuscript
compilation with the original figures have not been verified in this environment.
