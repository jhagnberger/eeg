import mne

def make_erp(data, condition="conflict"):
    evts, evts_dict = mne.events_from_annotations(data)
    
    # Filter events based on condition
    wanted_keys = [e for e in evts_dict.keys() if f"normal_or_conflict:{condition}" in e and "box:touched" in e]
    evts_dict_stim = dict((k, evts_dict[k]) for k in wanted_keys if k in evts_dict)
    
    if not evts_dict_stim:
        print(f"No events found for condition: {condition}")
        return None

    # Epoching
    # Baseline correction aligned to teammate's (-0.3, 0)
    epochs = mne.Epochs(data, evts, evts_dict_stim, tmin=-0.3, tmax=0.7, event_repeated='drop', baseline=(-0.3, 0))
    
    # Correct time
    epochs = epochs.load_data().shift_time(-0.063)
    
    # Apply final bandpass filter
    # epochs = epochs.copy().filter(l_freq=0.2, h_freq=35.0)
    
    # Return evoked response for FCz
    return epochs.average().copy().pick(['FCz'])
