"""Contains helper functions for the reaction time analysis. These functions are used in the reactiontime_analysis.ipynb
notebook to preprocess the data, epoch it, and perform a GLM analysis with reaction times as predictor. The functions
are organized in a way that they can be easily reused for other analyses as well."""

import mne
import numpy as np
from matplotlib import pyplot as plt
from mne_bids import BIDSPath, read_raw_bids
import os
import shutil
import pandas as pd
from mne.stats import linear_regression


def remove_problematic_annotations(bids_root="/Users/jan/Documents/git/ds003846"):
    """Removes problematic columns from participants.tsv to prevent BIDS-related warnings. The function creates a
    backup of the original participants.tsv file before removing the problematic columns.
    
    Args:
        bids_root: The root directory of the BIDS dataset.
    """
    problematic_columns = ['cap_size', 'block_1', 'block_2', 'block_3']
    participants_tsv_path = os.path.join(bids_root, "participants.tsv")
    backup_tsv_path = os.path.join(bids_root, "participants_original.tsv")
    if os.path.exists(participants_tsv_path):
        try:
            # Create a backup of the original file
            if not os.path.exists(backup_tsv_path):
                shutil.copy(participants_tsv_path, backup_tsv_path)
                print(f"Backup created: {backup_tsv_path}")

            # Load the tsv file
            participants_df = pd.read_csv(participants_tsv_path, sep='\t')

            # Remove problematic columns if they exist
            columns_to_remove = [col for col in problematic_columns if col in participants_df.columns]
            if columns_to_remove:
                print(f"Removing columns {columns_to_remove} from {participants_tsv_path}")
                participants_df = participants_df.drop(columns=columns_to_remove)

            # Save the cleaned file back to the original path
            participants_df.to_csv(participants_tsv_path, sep='\t', index=False)
        except Exception as e:
            print(f"Error processing {participants_tsv_path}: {e}")


def get_available_sessions(bids_root="/Users/jan/Documents/git/ds003846", subject_id="02"):
    """Returns the available sessions (e.g., visual, vibro, EMS) for a given subject. This is necessary because some
    subjects did not participate in all sessions.
    
    Args:
        bids_root: The root directory of the BIDS dataset.
        subject_id: The ID of the subject (e.g., "02") as string.
    
    Returns:
        A list of available session names for the subject.
    """
   
    subject_path = os.path.join(bids_root, f"sub-{subject_id}")
    sessions = []
    if os.path.exists(subject_path):
        for entry in os.listdir(subject_path):
            if entry.startswith("ses-"):
                sessions.append(entry.replace("ses-", ""))
    return sessions


def load_data(bids_root="/Users/jan/Documents/git/ds003846", subject_id="02", session="EMS", show_plots=False):
    """Loads EEG data for the given subject and session. Additionally, it can print raw info and plot electrode
    positions for visual inspection. It also sets the Fp1 and Fp2 channels, which are close to the eyes, as EOG
    channels for later eye blink artifact removal.
    
    Args:
        bids_root: The root directory of the BIDS dataset.
        subject_id: The ID of the subject (e.g., "02") as string.
        session: The name of the session (e.g., "EMS").
        show_plots: Whether to print raw info and plot electrode positions.
   
    Returns:
        The loaded raw EEG data for further use.
    """
    
    bids_path = BIDSPath(subject=subject_id, task="PredictionError", session=session,
                        datatype='eeg', suffix='eeg',
                        root=bids_root)

    # Read the file
    raw = read_raw_bids(bids_path)
    if show_plots:
        print(raw.info)

    # Plot electrode positions
    if show_plots:
        raw.plot_sensors(show_names=True)
    
    # Set Fp1 and Fp2 channels as EOG (electrooculography aka eye movement channel). These electrodes are close to the
    # eyes and can be used to detect eye blinks and other eye movements following the MNE BIDS documentation:
    # https://mne.tools/mne-bids-pipeline/stable/settings/general.html#mne_bids_pipeline._config.eog_channels
    raw.set_channel_types({'Fp1': 'eog', 'Fp2': 'eog'})
    
    return raw


def remove_bad_channels(raw, subject_id, show_plots=False):
    """Remove bad channels from raw data for each subject. We use the bad channels reported in the original
    implementation. The function updates the raw.info['bads'] list with the bad channels for later use.
    
    Args:
        raw: The raw EEG data to update with bad channels.
        subject_id: The ID of the subject (e.g., "02").
        show_plots: Whether to print the list of bad channels after updating.
    """
    
    bad_channels_list = {
        2: [4, 16],
        3: [9, 10, 55, 60],
        4: [41],
        5: [1, 33, 41, 42],
        6: [9, 16, 43, 46, 10, 14],
        7: [17, 32, 49],
        8: [41, 42, 62, 63, 9, 17, 55],
        9: [12, 41, 46],
        10: [42, 45, 41, 33, 17],
        11: [22],
        12: [2, 22, 31, 64],
        13: [7, 16, 40, 46, 48],
        14: [2, 3, 7, 16, 28],
        15: [5, 6, 12, 33, 34, 46],
        16: [28, 29, 41, 45, 60],
        17: [1, 2, 3, 22, 28, 36],
        18: [15, 17, 26, 30, 45],
        19: [15, 22, 26, 46, 55, 59, 60],
        20: [2, 8, 11, 36, 62]
    }

    bad_channels = bad_channels_list.get(subject_id, [])
    raw.info['bads'] = [raw.ch_names[ch-1] for ch in bad_channels]
    
    if show_plots:
        print(raw.info['bads'])


def filtering_referencing(data, show_plots=False):
    """Applies filtering (line noise removal and band-pass filtering), resampling to reduce the amounts of data, and
    re-referencing to the data. Additionally, it recovers the FCz channel which is only implicitly present in the 
    data as reference channel.
    
    Args:
        data: The raw EEG data to preprocess.
        show_plots: Whether to plot the filtered data.
    Returns:
        The preprocessed raw EEG data ready for further analysis.
    """
    
    if show_plots:
        fig = data.plot(start=0, duration=1, n_channels=16)
        fig.savefig("raw_1s.pdf", format="pdf")
        fig = data.plot(start=60, duration=5, n_channels=16)
        fig.savefig("raw.pdf", format="pdf")
        fig = data.copy().pick(["Cz"]).compute_psd().plot()
        fig.savefig("psd_raw.pdf", format="pdf")
        
    # Remove line noise with notch filter at 50 Hz and its harmonics (150 Hz). We noticed that there is also a peak
    # at 150 Hz in the power spectrum, which is likely a multiple of the 50 Hz line noise, so we remove it as well.
    data = data.load_data().copy().notch_filter(freqs=[50, 150])

    # Apply band-pass filter between 0.1 Hz and 125 Hz
    data = data.filter(l_freq=0.1, h_freq=125.0)

    # Resample with 250 Hz for less data size
    data = data.copy().resample(sfreq=250)
    
    if show_plots:
        fig = data.plot(start=60, duration=5, n_channels=16)
        fig.savefig("filtered.pdf", format="pdf")
        fig = data.copy().pick(["Cz"]).compute_psd().plot()
        fig.savefig("psd_filtered.pdf", format="pdf")

    # We need FCz for our analysis, which was used as reference. We add it here as a reference channel
    # and later re-reference to average to get the FCz signal back.
    data.add_reference_channels(['FCz'])
    
    # Set montage (aka electrode positions). This is required for the topographic plots later. We remove the Fp1 and
    # Fp2 channels from the montage because we get some warnings of these channels. Since we set them as EOG channels,
    # they are not required for the analysis and we can safely ignore them.
    montage = mne.channels.make_standard_montage('standard_1020')
    ch_pos = montage.get_positions()['ch_pos']
    # Remove Fp1 and Fp2 from the montage because we get some warning
    ch_pos.pop('Fp1', None)
    ch_pos.pop('Fp2', None)
    # Create a new montage without Fp1 and Fp2
    new_montage = mne.channels.make_dig_montage(ch_pos=ch_pos, coord_frame='head')
    data.set_montage(new_montage)

    # Re-reference to average, which returns the FCz signal back as it was used as reference before
    data = data.set_eeg_reference('average')
    
    if show_plots:
        fig = data.plot(start=60, duration=5, n_channels=16)
        fig.savefig("rereferenced.pdf", format="pdf")
        fig = data.copy().pick(["Cz"]).compute_psd().plot()
        fig.savefig("psd_rereferenced.pdf", format="pdf")
        
    return data


def apply_ica_eyes(data, show_plots=False):
    """Applies ICA with EOG correlation to remove eye movements.
    
    Good reference to analyze ICA components: https://labeling.ucsd.edu/tutorial/labels
    
    Args:
        data: The raw EEG data to preprocess.
        show_plots: Whether to plot the ICA components and their properties for visual inspection.
    
    Returns:
        The raw EEG data with eye movement artifacts removed.
    """
    
    # Compute ICA with 20 components
    ica = mne.preprocessing.ICA(n_components=20, random_state=97, max_iter="auto")
    ica.fit(data)

    # Check/correlate the components with Fp1 and Fp2 channels as EOG (electrooculography aka eye movement channel)
    eog_inds, eog_scores = ica.find_bads_eog(data, ch_name=['Fp1', 'Fp2'])
    
    if show_plots:
        fig = ica.plot_scores(eog_scores)
        fig.savefig("ica_scores.pdf", format="pdf")
        fig = ica.plot_properties(data, picks=eog_inds)[0]
        fig.savefig("ica_properties.pdf", format="pdf")

    if show_plots:
        fig = ica.plot_sources(data, start=60)
        fig.savefig("ica_sources.pdf", format="pdf")
        fig = ica.plot_components()
        fig.savefig("ica_components.pdf", format="pdf")

    # Remove ICA artifact components/ remove the eye movement components
    ica.exclude = eog_inds
    data = ica.apply(data)
    
    return data


def make_epoched_data(data, condition="conflict", show_plots=False):
    """Epochs the data for the given condition and extracts reaction times.
    
    Args:
        data: The raw EEG data to epoch.
        condition: The condition to epoch (e.g., "conflict" or "normal").
        show_plots: Whether to plot the reaction times for visual inspection.
        
    Returns:
        The epoched data for the given condition and the corresponding reaction times.
    """
    evts, evts_dict = mne.events_from_annotations(data)
    
    wanted_keys = [e for e in evts_dict.keys() if f"normal_or_conflict:{condition}" in e and "box:touched" in e]
    evts_dict_stim = dict((k, evts_dict[k]) for k in wanted_keys if k in evts_dict)
        
    # Apply final bandpass filter
    data = data.filter(l_freq=0.1, h_freq=45.0)
    
    # Epoching
    epochs = mne.Epochs(data, evts, evts_dict_stim, tmin=-0.3, tmax=0.7, event_repeated='drop', baseline=(-0.3, 0))
    
    # Correct time
    epochs = epochs.load_data().shift_time(-0.063)
    
    # Drop bad epochs
    epochs.pick(["FCz"])
    reject_criteria = dict(eeg=150e-6) 
    epochs.drop_bad(reject=reject_criteria)
    
    # Get reaction time of events
    reaction_times = []
    for k in epochs.event_id.keys():
        splitted = k.split(";")
        for split in splitted:
            if "reaction_time" in split:
                reaction_times.append(split.split(":")[-1])
    reaction_times = np.array(reaction_times, dtype=float)
    
    # plot reaction times as scatter plot
    if show_plots:
        plt.figure(figsize=(10, 5))
        plt.hist(reaction_times, bins=20, color="blue", alpha=0.7)
        plt.title(f"Reaction Times for condition '{condition}'")
        plt.xlabel("Reaction Time (s)")
        plt.ylabel("Count")
        plt.show()
    
    return epochs.copy().pick(['FCz']), reaction_times


def make_glm(epochs_normal, epochs_conflict, reaction_times_normal, reaction_times_conflict, show_plots=False):
    """Performs a GLM analysis with condition and reaction times as predictors.
    
    Args:
        epochs_normal: The epochs for the normal condition.
        epochs_conflict: The epochs for the conflict condition.
        reaction_times_normal: The reaction times for the normal condition.
        reaction_times_conflict: The reaction times for the conflict condition.
        show_plots: Whether to plot the beta values for the condition and reaction times.
        
    Returns: 
        The beta values for the type and reaction times.
    """
    epochs_all = mne.concatenate_epochs([epochs_normal, epochs_conflict])
    rt_all = np.concatenate([reaction_times_normal, reaction_times_conflict])
    type_code = np.concatenate([np.zeros(len(reaction_times_normal), dtype=int), np.ones(len(reaction_times_conflict), dtype=int)])
    
    # Remove the mean to avoid a correlation between type and reaction times.
    # We only care about slow/fast reaction times
    rt_centered = rt_all.copy()
    mean_match = rt_all[type_code == 0].mean()
    mean_mismatch = rt_all[type_code == 1].mean()
    rt_centered[type_code == 0] -= mean_match
    rt_centered[type_code == 1] -= mean_mismatch
    
    # type_code: 0 = match, 1 = mismatch
    # rt_centered: centered reaction times
    design_matrix = np.column_stack([
        np.ones(len(type_code)),
        type_code,
        rt_centered
    ])
    names = ["Intercept", "Type", "RT_centered"]

    glm_results = linear_regression(epochs_all, design_matrix, names=names)

    beta_type = glm_results["Type"].beta
    beta_rt        = glm_results["RT_centered"].beta
    
    if show_plots:
        beta_type.plot()
        beta_rt.plot()
    
    return beta_type, beta_rt


def make_grand_average_plot(beta_type, beta_rt):
    """Plots the grand-average of the beta type and centered reaction time.
    
    Args:
        beta_type: The beta values for the type predictor.
        beta_rt: The beta values for the reaction time predictor.
    """
    
    colors = {"Visual": "C0",
        "Vibro": "C3",
        "EMS": "C8"
    }    
    
    figs = mne.viz.plot_compare_evokeds(
        beta_type,
        picks="FCz",
        time_unit="ms",
        colors=colors,
        title="Beta Type (FCz)",
        ylim=dict(eeg=[-6, 7])
    )
    fig = figs[0]
    fig.set_size_inches(6, 4)
    fig.savefig("beta_type.pdf", format="pdf")
    
    figs = mne.viz.plot_compare_evokeds(
        beta_rt,
        picks="FCz",
        time_unit="ms",
        colors=colors,
        title="Beta Centered Reaction Time (FCz)",
        ylim=dict(eeg=[-6, 7])
    )
    fig = figs[0]
    fig.set_size_inches(6, 4)
    fig.savefig("beta_rt.pdf", format="pdf")
    