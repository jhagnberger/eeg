<p align="center"><img src="neuronauts_logo.svg" alt="CALM-PDE Logo" width="25%" /></p>

# EEG Project

## Download Data
1. Install git-annex (e.g., `brew install git-annex` on macOS)
2. Clone repository `git clone https://github.com/OpenNeuroDatasets/ds003846.git`
3. Get data files `git annex get .`

## First Analysis
Run Jupyter Notebook `visualize_eeg.ipynb`

## Milestone 3
### Improvements from Milestone 2:
1. ASR algorithm for EEG denoising
2. ICA algorithm to separate independent components and remove eye movement artifacts
3. Additional filtering during data epoching
4. ERP visualization
5. Encapsulation into functions for single subject and single session processing

### Issues
1. ASR computation is too slow; skipped in actual execution
2. Temporal cleaning relies only on automatic bad epoch detection during epoching; no manual removal of bad events
3. No manual inspection of bad channels
