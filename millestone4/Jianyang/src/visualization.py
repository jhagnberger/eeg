import mne
import matplotlib.pyplot as plt
from .config import COLORS

def make_erp_plot(normal_data, conflict_data, subject_id, save=True, show=False):
    """
    Plots ERPs for normal and conflict conditions comparison.
    normal_data: dict of session -> evoked
    conflict_data: dict of session -> evoked
    """
    
    # Filter out Nones
    normal_data = {k: v for k, v in normal_data.items() if v is not None}
    conflict_data = {k: v for k, v in conflict_data.items() if v is not None}
    
    figures = []

    if normal_data:
        fig_normal = mne.viz.plot_compare_evokeds(
            normal_data,
            picks="FCz",
            time_unit="ms",
            colors=COLORS,
            title=f"Subject {subject_id} - Normal (FCz)",
            show=show
        )
        figures.append(fig_normal)
        
        if save:
            # Handle case where fig might be a list
            fig_to_save = fig_normal[0] if isinstance(fig_normal, list) else fig_normal
            fig_to_save.savefig(f"subject_{subject_id}_normal_erp.png")

    if conflict_data:
        fig_conflict = mne.viz.plot_compare_evokeds(
            conflict_data,
            picks="FCz",
            time_unit="ms",
            colors=COLORS,
            title=f"Subject {subject_id} - Conflict (FCz)",
            show=show
        )
        figures.append(fig_conflict)
        
        if save:
            fig_to_save = fig_conflict[0] if isinstance(fig_conflict, list) else fig_conflict
            fig_to_save.savefig(f"subject_{subject_id}_conflict_erp.png")
    
    if save and not show:
        plt.close('all')
        print(f"Saved ERP plots for Subject {subject_id}")
        
    return figures

def plot_grand_average(evokeds_list, session, condition, save=True, show=False):
    """
    Plots individual subjects and grand average for a specific session and condition.
    evokeds_list: list of Evoked objects (one per subject)
    """
    if not evokeds_list:
        print(f"No data for {session} - {condition}")
        return

    # Calculate Grand Average
    grand_avg = mne.grand_average(evokeds_list)
    
    # Prepare dict for plotting
    plotted_data = {}
    styles = {}
    colors = {}
    
    # Session color for the average
    session_color = COLORS.get(session, "black")
    
    # Generate distinct colors for subjects using a colormap
    # 'tab20' is good for up to 20 distinct categorical colors
    cmap = plt.get_cmap('tab20')
    
    for i, ev in enumerate(evokeds_list):
        subj = ev.comment
        # Removing the underscore prefix to show in legend
        key = f"Subj {subj}" 
        plotted_data[key] = ev
        styles[key] = {"linewidth": 1.0, "alpha": 0.7}
        # Assign a color from the colormap based on index
        # We use i % 20 to cycle if there are more than 20 (though unlikely here)
        colors[key] = cmap(i % 20)
        
    plotted_data["Average"] = grand_avg
    styles["Average"] = {"linewidth": 4.0, "alpha": 1.0, "linestyle": "--"} # Dashed for average to distinguish
    colors["Average"] = "black" # Force black for average for high contrast
    
    fig = mne.viz.plot_compare_evokeds(
        plotted_data,
        picks="FCz",
        time_unit="ms",
        colors=colors,
        styles=styles,
        title=f"{session} - {condition.capitalize()} (FCz)",
        show=show,
        legend='upper right'
    )
    

    if save:
        filename = f"group_analysis_{session}_{condition}.png"
        fig_to_save = fig[0] if isinstance(fig, list) else fig
        fig_to_save.savefig(filename)
        print(f"Saved {filename}")
        
    if not show:
        plt.close('all')
