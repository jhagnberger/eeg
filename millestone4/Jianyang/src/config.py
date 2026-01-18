import os

# Default paths
# Assuming the data is in the parent directory of the project root or similar
# Adjust BIDS_ROOT as necessary based on where the script is run from
BIDS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ds003846"))

SUBJECTS = ["02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
SESSIONS = ["Visual", "Vibro", "EMS"]

BAD_CHANNELS_LIST = {
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

COLORS = {
    "Visual": "C0",
    "Vibro": "C2",
    "EMS": "C1"
}

# Define subjects to exclude for specific sessions due to bad data
EXCLUDED_SUBJECTS = {
    "EMS": ['03', '16'],   # Add the subject ID here, e.g., ["04"]
    "Visual": [],
    "Vibro": []
}
