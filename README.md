# Box packing with Everyday items Dataset

This dataset is a collection of human experts packing groceries into a box. 
BoxED was collected in Virtual Reality (an example video is available [here](https://youtu.be/TUd-eCDG5i8)) and captures many parameters of this task,
including 6-DOF pick-and-place grasp poses, object trajectories, packing sequence and more. 
This dataset enables learning models that generate human-like behaviors for multiple aspects of this task from humans.

![](./Images/cover_image.png "Data collection in Virtual Reality")

## How to Use
In this [file](example.py) you'll find an example of how to import the dataset into the Python importer provided [here](boxed_importer.py).
This importer will load all the data into an object-oriented structure for easier use. Refer to its [documentation](boxed_importer.py)
for more details on how the data is saved and how you can use it.

Alternatively, you can simply use the data directly. Everything is stored in the JSON format and available in [this folder](Dataset).

## Dataset Details
| **Parameter**      | **File name**          | **Quantity** | **Format** | **Description**                                                      |
|:------------------:|:----------------------:|:------------:|:----------:|:--------------------------------------------------------------------:|
| Grasp Pose         | PickPlace_dataset      | 4644         | JSON       | 6-DoF grasp pose                                                     |
| Placement Pose     | PickPlace_dataset      | 4644         | JSON       | 6-DoF placement pose inside the box                                  |
| Packing Sequence   | PickPlace_dataset      | 263          | JSON       | Sequence in which the objects were packed                            |
| Object Trajectory  | <obj_id>_trajectory    | 4644         | JSON       | Trajectory of the object from the table to the box, sampled at 20 Hz |
| Headset Trajectory | main_camera_trajectory | 263          | JSON       | Trajectory of the headset during the experiment                      |
| Objects in Scene   | initial_objects        | 263          | JSON       | List of objects and their poses at the start of each scene           |
| Top-Down View      | top_down               | 263          | PNG        | Top-down image of the initial layout of the objects                  |


For a detailed overview of the contents of the dataset, collection procedure or purpose, please refer to [this thesisLINK]().

Alternatively, for a shorter overview refer to Section III of this [this article](https://arxiv.org/abs/2210.01645).

## Environment Details
A minimalistic version of the Unity environment used to collect BoxED is available [here](https://github.com/andrejfsantos4/BoxED_Environment). It only contains the main components (objects, gripper, table, etc).
