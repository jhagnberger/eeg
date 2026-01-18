import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import SUBJECTS, SESSIONS, EXCLUDED_SUBJECTS
from src.data_loader import load_data
from src.preprocessing import remove_bad_channels, filtering_referencing, apply_ica_eyes
from src.analysis import make_erp
from src.visualization import make_erp_plot, plot_grand_average

def main():
    # Structure: session -> condition -> list of evokeds
    group_results = {session: {"normal": [], "conflict": []} for session in SESSIONS}
    
    # Track success/fail for reporting
    processed_counts = {session: {"normal": 0, "conflict": 0} for session in SESSIONS}

    print(f"Starting analysis for {len(SUBJECTS)} subjects across {len(SESSIONS)} sessions...")

    for subject_id in SUBJECTS:
        for session in SESSIONS:
            # Check for exclusion
            if subject_id in EXCLUDED_SUBJECTS.get(session, []):
                print(f"Skipping Subject: {subject_id}, Session: {session} (Excluded via config)")
                continue

            print(f"\n--- Processing Subject: {subject_id}, Session: {session} ---")
            try:
                # Load data
                data = load_data(subject_id=subject_id, session=session)
                
                # Remove bad channels
                data = remove_bad_channels(data, subject_id)

                # Filtering and Referencing
                data = filtering_referencing(data)
                
                # Apply ICA
                data = apply_ica_eyes(data)
                
                # ERP for normal condition
                erp_normal = make_erp(data, condition="normal")
                if erp_normal:
                    erp_normal.comment = subject_id
                    group_results[session]["normal"].append(erp_normal)
                    processed_counts[session]["normal"] += 1
                
                # ERP for conflict condition
                erp_conflict = make_erp(data, condition="conflict")
                if erp_conflict:
                    erp_conflict.comment = subject_id
                    group_results[session]["conflict"].append(erp_conflict)
                    processed_counts[session]["conflict"] += 1
                    
            except Exception as e:
                print(f"Error processing {subject_id} {session}: {e}")
                continue

    # Generate Group Plots
    print("\n" + "="*40)
    print("Generating Group Plots...")
    print("="*40)
    
    for session in SESSIONS:
        for condition in ["normal", "conflict"]:
            evokeds = group_results[session][condition]
            count = processed_counts[session][condition]
            print(f"Plotting {session} - {condition} (n={count} subjects)")
            plot_grand_average(evokeds, session, condition)

    # Final Summary
    print("\nAnalysis Summary (Subjects per session/condition):")
    for session in SESSIONS:
        n_norm = processed_counts[session]["normal"]
        n_conf = processed_counts[session]["conflict"]
        print(f"  {session:10}: Normal={n_norm:2}, Conflict={n_conf:2}")

if __name__ == "__main__":
    main()
