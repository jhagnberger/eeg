from mne_bids import BIDSPath, read_raw_bids
from .config import BIDS_ROOT

def load_data(bids_root=BIDS_ROOT, subject_id="02", session="EMS"):
    """Loads EEG data for the given subject and session."""
    print(f"Loading data for subject {subject_id}, session {session} from {bids_root}")
    bids_path = BIDSPath(subject=subject_id, task="PredictionError", session=session,
                        datatype='eeg', suffix='eeg',
                        root=bids_root)

    # Read the file
    raw = read_raw_bids(bids_path)
    # raw.info 
    
    # Set Fp1 and Fp2 channel as EOG (electrooculography aka eye movement channel)
    # This prevents them from being used in EEG average referencing and helps ICA
    try:
        raw.set_channel_types({'Fp1': 'eog', 'Fp2': 'eog'})
    except ValueError:
        print("Warning: Fp1 or Fp2 not found in channels, skipping EOG type setting.")
    
    # Plot electrode positions (commented out in original, keeping it optional or removing)
    # raw.plot_sensors(show_names=True)
    
    return raw
