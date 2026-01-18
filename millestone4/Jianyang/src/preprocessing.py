import mne
from .config import BAD_CHANNELS_LIST

def remove_bad_channels(raw, subject_id):
    """Remove bad channels from raw data based on their descriptions and inspections."""
    bad_channels = BAD_CHANNELS_LIST.get(int(subject_id), [])
    # Filter out channels that don't exist in the raw object to avoid errors
    existing_bads = [raw.ch_names[ch] for ch in bad_channels if ch < len(raw.ch_names)]
    raw.info['bads'].extend(existing_bads)
    print(f"Bad channels marked: {raw.info['bads']}")
    return raw

def filtering_referencing(data):
    """Applies filtering and re-referencing to the data."""
    # Remove line noise
    # Note: load_data() is redundant if data is already loaded, but mne sometimes needs preloading for filtering
    if not data.preload:
        data.load_data()
        
    data = data.copy().notch_filter(freqs=[50, 150])

    # Apply bandpass filter
    data = data.filter(l_freq=0.1, h_freq=125.0)

    # Resample with 250 Hz for less data size
    data = data.copy().resample(sfreq=250)

    # Add reference channels
    # Only add if not already present or handled
    try:
        data.add_reference_channels(['FCz'])
    except ValueError:
        print("Reference channel 'FCz' might already exist or issue adding it.")
    
    # Set montage (aka electrode positions)
    montage = mne.channels.make_standard_montage('standard_1020')
    try:
        # Remove Fp1 and Fp2 from the montage because we get some warning if they are marked as EOG
        # but present in a standard EEG montage
        ch_pos = montage.get_positions()['ch_pos']
        ch_pos.pop('Fp1', None)
        ch_pos.pop('Fp2', None)
        # Create a new montage without Fp1 and Fp2
        new_montage = mne.channels.make_dig_montage(ch_pos=ch_pos, coord_frame='head')
        data.set_montage(new_montage)
    except ValueError as e:
        print(f"Warning setting montage: {e}")

    # Re-reference to average
    data = data.set_eeg_reference('average')
    
    return data

def apply_ica_eyes(data, plot=False):
    """Applies ICA to remove eye movements."""
    # Remove artifacts with ICA
    ica = mne.preprocessing.ICA(n_components=20, random_state=97, max_iter="auto")
    ica.fit(data)

    # Check with Fp1 and Fp2 channels as EOG (electrooculography aka eye movement channel)
    # Ensure they exist
    eog_channels = [ch for ch in ['Fp1', 'Fp2'] if ch in data.ch_names]
    
    if eog_channels:
        eog_inds, eog_scores = ica.find_bads_eog(data, ch_name=eog_channels)
        
        if plot:
            try:
                ica.plot_scores(eog_scores, show=True)
                ica.plot_properties(data, picks=eog_inds, show=True)
                ica.plot_components(show=True)
            except Exception as e:
                print(f"Could not plot ICA: {e}")
        
        # Remove ICA components
        # Remove the eye movement components
        ica.exclude = eog_inds
        data = ica.apply(data)
    else:
        print("Channel Fp1/Fp2 not found, skipping EOG artifact removal with ICA.")
    
    return data
