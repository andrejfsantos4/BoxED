import os
import re
from typing import Tuple, List


def file_crawler(root_folder: str, target_filename: str, uniq_seqs=False) -> tuple[list[str], list[tuple[int, int]]]:
    """
    Returns the paths to all files whose name contains *target_filename* in all subdirectories of *root_folder*,
    as a list. These paths are ordered according to the participant number first and then according to scene number.

    :param uniq_seqs: (For PickPlace sequences only) If set to True, only the sequences with unique objects only are
    returned.
    """
    all_file_paths = []
    part_scene_nums = []
    for path, subdirs, files in os.walk(root_folder):
        for name in files:
            if target_filename in name:
                # Get the participant and scene number
                part_scene_number = tuple(int(s) for s in re.findall(r'\d+', path))

                # If only uniq_seqs are requested, verify that it's the 1st scene and the participant number is greater
                # than 25 (only those have unique objects in the 1st scene), before adding path to list
                if uniq_seqs and (part_scene_number[1] != 1 or part_scene_number[0] < 26):
                    continue

                all_file_paths.append(os.path.join(path, name))
                part_scene_nums.append(part_scene_number)

    # Sort paths along participant number and scene number
    # all_file_paths.sort(key=lambda path: tuple(int(s) for s in re.findall(r'\d+', path)))
    all_file_paths = [x for _, x in sorted(zip(part_scene_nums, all_file_paths))]
    part_scene_nums = [x for x, _ in sorted(zip(part_scene_nums, all_file_paths))]
    return all_file_paths, part_scene_nums


def get_clean_name(name: str) -> str:
    """
    Removes the portions of the name that contain brackets, integer IDs, etc.

    Eg: *010 box(clone)-29932* becomes *010 box*
    """
    # Delete the portion of the ID string that may have "(clone)" and/or the unique integer identifier)
    idx1 = name.find('(')
    idx2 = name.find('-')
    delete_idx = len(name)

    # Get the smallest positive integer from idx1 and idx2
    if idx1 != -1 or idx2 != -1:
        delete_idx = min(idx1, idx2) if min(idx1, idx2) > 0 else max(idx1, idx2)

    return name[0:delete_idx]
