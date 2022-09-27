"""
This file contains an example of how to import BoxED using the object-oriented framework in boxed_importer.py

This script was developed and tested with Python 3.9, but should be compatible with other versions.
"""
from boxed_importer import BoxED


if __name__ == '__main__':
    # Set this to be the full path to the folder that contains the dataset
    root_dir = r"...\BoxED\Dataset"

    # Instantiate the class which imports the dataset (may take a few seconds)
    boxed = BoxED(root_folder=root_dir)

    # At this point the dataset has been loaded into memory and can be used. Please refer to boxed_importer.py to see
    # the structure of the data

    # For instance, to get all the packing sequences in the dataset
    sequences = boxed.get_sequences(start_token=True)
    print(f"An example packing sequence is: {sequences[0]}")

    # You can also request all the grasp poses
    grasp_poses = boxed.get_grasp_poses('pick')
