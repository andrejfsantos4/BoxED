import json
import logging
from os import path
import numpy as np
import typing as tp

import helpers


class Pose:
    """ Represents a 6-dimensional pose. """

    def __init__(self, rotation: list[list[float]], translation: list[float]):
        self.rotation = np.asarray(rotation)
        self.translation = np.asarray(translation)


class PoseWithTime(Pose):
    """ Represents a 6-dimensional pose with a timestamp in milliseconds, relative to master clock that starts at scene
    start. """

    def __init__(self, rotation: list[list[float]], translation: list[float], time_stamp: int):
        super().__init__(rotation, translation)
        self.time_stamp = time_stamp


class Obj:
    """ Represents an object in the dataset. Includes its name, unique ID, and pick and place pose. """

    def __init__(self):
        self.name: tp.Optional[str] = None
        self.unique_id: tp.Optional[int] = None
        self.pick_pose: tp.Optional[Pose] = None
        self.place_pose: tp.Optional[Pose] = None

    def add_obj_info(self, name: str, pick_rot: list[list[float]], pick_trans: list[float],
                     place_rot: list[list[float]], place_trans: list[float]):
        """ Processes and saves the object's information. """
        self.name = helpers.get_clean_name(name)
        self.unique_id = int(name[-4:])  # The last 4 characters are the unique object ID
        self.pick_pose = Pose(pick_rot, pick_trans)
        self.place_pose = Pose(place_rot, place_trans)


class ObjWithTraj(Obj):
    """ Represents an object and its trajectory in the dataset. Extends the *Obj* class to add a trajectory attribute,
    which is a list of *PoseWithTime* objects. """

    def __init__(self):
        super().__init__()
        self.trajectory: tp.List[PoseWithTime] = []

    def add_traj(self, traj_file: str):
        """ Loads a trajectory from a trajectory file. """
        with open(traj_file) as f:
            data = json.load(f)

        for pose_time in data:
            self.trajectory.append(PoseWithTime(pose_time['rotation'], pose_time['translation'],
                                                pose_time['timeStamp']))


class Scene:
    """ Represents a scene (i.e., a set of objects that the participant packs into the box). Includes the objects in
    this scene, the order in which they were packed (not explicitly, but it matches the order in which they are saved in
    the objects list) and the grasp and placement poses. """

    def __init__(self):
        self.scene_num: tp.Optional[int] = None
        self.initial_objs: tp.List[str] = []
        self.objs_info: tp.List[ObjWithTraj] = []
        self.cam_traj: tp.List[PoseWithTime] = []

    def add_objects(self, scene_file: str, scene_number: int):
        """ Loads the PickPlace file of each scene. The order of the objects is preserved. """
        self.scene_num = scene_number

        with open(scene_file) as f:
            data = json.load(f)

        # For each object in the PickPlace file, load its name, pick and place poses into an ObjWithTraj object (the
        # trajectory of the object is loaded afterwards)
        for obj_data in data:
            new_obj = ObjWithTraj()
            new_obj.add_obj_info(obj_data['id'], obj_data['pickRotation'], obj_data['pickTranslation'],
                                 obj_data['placeRotation'], obj_data['placeTranslation'])
            self.objs_info.append(new_obj)

    def add_obj_traj(self, scene_files: list[str]):
        """ Loads the trajectory of each object in the scene. """
        for obj in self.objs_info:
            for file in scene_files:
                # Search for the trajectory file that corresponds to this object
                if obj.name in file:
                    obj.add_traj(file)
                    break

    def add_cam_traj(self, cam_traj_file: str):
        """ Loads the camera trajectory file of this scene. """
        with open(cam_traj_file) as f:
            data = json.load(f)

        for cam_pose_time in data:
            self.cam_traj.append(PoseWithTime(cam_pose_time.rotation, cam_pose_time.translation,
                                              cam_pose_time.timeStamp))


class Participant:
    """ Contains all the scenes (sets of objects) that a participant packed in the box."""

    def __init__(self):
        self.part_num: tp.Optional[int] = None  # Participant number
        self.scenes: tp.List[Scene] = []

    def add_objects(self, part_files: list[str], part_scene_nums: list[tuple[int, int]]):
        """
        Loads all the information of the pick and place sequence of objects.

        :param part_files: All the pick and place files corresponding to this Participant.
        :param part_scene_nums: The participant and scene numbers in the same order as the files.
        :return: A Participant object with all the corresponding data.
        """
        self.part_num = part_scene_nums[0][0]

        # Separate files by scene and create a Scene object for each one
        for part_scene_num, part_file in zip(part_scene_nums, part_files):
            new_scene = Scene()
            new_scene.add_objects(part_file, part_scene_num[1])
            self.scenes.append(new_scene)

    def add_trajectories(self, part_files: list[str], part_scene_nums: list[tuple[int, int]],
                         cam_part_files=None, cam_part_scene_nums=None) -> None:
        """
        Loads the trajectories of all the objects corresponding to this participant.

        :param part_files: All the objects' trajectory files corresponding to this Participant.
        :param part_scene_nums: The participant and scene numbers in the same order as the object files.
        :param cam_part_files: (optional) All the camera's trajectory files corresponding to this Participant.
        :param cam_part_scene_nums: (optional) The participant and scene numbers in the same order as the camera files.
        """

        # Get the files that correspond to each scene
        aux_scene_nums = np.asarray([x[1] for x in part_scene_nums])
        for scene in self.scenes:
            scene_files = [i for (i, v) in zip(part_files, aux_scene_nums == scene.scene_num) if v]
            scene.add_obj_traj(scene_files)
            # Verify whether to load the camera trajectory or not
            if cam_part_files is not None:
                # Get the camera trajectory file (only one file) corresponding to this participant and scene
                scene.add_cam_traj(cam_part_files[cam_part_scene_nums.index((self.part_num, scene.scene_num))])


class BoxED:
    """
    Stores the entire "Box packing with Everyday items Dataset" and provides helper methods to facilitate its use. Contains methods for:
    loading dataset from folder, reading specific attributes of the dataset, and more.

    A *BoxED* object stores the path to the root folder of the dataset, a flag that signals whether camera
    trajectories should be loaded or not (they are very large) and a list of *Participant* objects. Each participant
    stores its number and a list of *Scene* objects. A scene is a set of objects that the participant packed into the
    box. Each *Scene* object stores all the information of the objects in it.
    """

    UNIQ_OBJS = 26
    """ Number of the 1st participant for whom the 1st scene has unique objects only (this feature hadn't been 
    implemented before) """

    # List of all object names in the dataset
    ALL_OBJS = ["002 masterchef can", "003 cracker box", "004 sugar box", "005 tomato soup can", "006 mustard bottle",
                "007 tuna fish can", "008 pudding box", "010 potted meat can", "011 banana", "012 strawberry",
                "013 apple", "014 lemon", "015 peach", "016 pear", "017 orange", "018 plum", "021 bleach cleanser",
                "025 mug", "057 racquetball", "058 golf ball", "100 half egg carton", "101 bread", "102 toothbrush",
                "103 toothpaste"]
    """ List of all object's names. """

    def __init__(self, root_folder: str, load_cam_traj=False):
        """
        Reads and loads the dataset (may take a few moments to finish).

        :param root_folder: Folder where the dataset is located
        :param load_cam_traj: Whether to load_pick_place the camera trajectories or not.
        """
        logging.basicConfig(format='BoxED %(levelname)s: %(message)s', level=logging.INFO)
        self.participants: tp.List[Participant] = []

        if root_folder is None:
            logging.error("Please specify the root folder where the dataset is.")
            exit(1)
        if not path.exists(root_folder) or not path.isdir(root_folder):
            logging.error("Specified root directory doesn't exist or is not a directory.")
            exit(1)

        self.root_folder = root_folder  # The root folder where the dataset is stored
        self.load_cam_traj = load_cam_traj
        self.load_pick_place()
        self.load_trajectories()

    def load_pick_place(self):
        pickplace_files, part_scene_nums = helpers.file_crawler(root_folder=self.root_folder,
                                                                target_filename='PickPlace_dataset')
        start_idx = 0
        # Separate files per participant
        for i in range(len(part_scene_nums)):
            # If the next file belongs to a different participant create a new participant
            if part_scene_nums[start_idx][0] != part_scene_nums[i][0]:
                self.add_participant(pickplace_files[start_idx:i], part_scene_nums[start_idx:i])
                start_idx = i
            # Else if the participant is the same but the file is the last file in the list create a new participant
            elif part_scene_nums[start_idx][0] == part_scene_nums[i][0] and i == len(part_scene_nums) - 1:
                self.add_participant(pickplace_files[start_idx:i + 1], part_scene_nums[start_idx:i + 1])
            # Special case where the next file is the last file and belongs to a different participant
            if i == len(part_scene_nums) - 1 and part_scene_nums[start_idx][0] != part_scene_nums[i][0]:
                self.add_participant([pickplace_files[i]], [part_scene_nums[i]])

    def add_participant(self, pick_place_files: list[str], part_scene_nums: list[tuple[int, int]]):
        new_participant = Participant()
        new_participant.add_objects(pick_place_files, part_scene_nums)
        self.participants.append(new_participant)

    def load_trajectories(self):
        """ Loads all object trajectories in the dataset. """
        trajectory_files, part_scene_nums = helpers.file_crawler(root_folder=self.root_folder,
                                                                 target_filename='trajectory')
        # Get the files that correspond to each participant
        aux_part_nums = np.asarray([x[0] for x in part_scene_nums])
        for part in self.participants:
            part_files = [i for (i, v) in zip(trajectory_files, aux_part_nums == part.part_num) if v]
            part_nums = [i for (i, v) in zip(part_scene_nums, aux_part_nums == part.part_num) if v]

            # Separate object trajectory files from camera trajectory files. This is done by adding camera trajectory
            # files to a new list and saving their indexes to a list to remove them from the original part/scenes
            # numbers list and files list
            cam_part_files, cam_part_nums, pop_idxs = [], [], []
            for i, (part_file, part_num) in enumerate(zip(part_files, part_nums)):
                if "main_camera_trajectory" in part_file:
                    cam_part_files.append(part_file)
                    cam_part_nums.append(part_num)
                    pop_idxs.append(i)
            for index in sorted(pop_idxs, reverse=True):
                del part_nums[index]
                del part_files[index]

            # Add this participant's trajectories
            if self.load_cam_traj:
                part.add_trajectories(part_files, part_nums, cam_part_files, cam_part_nums)
            else:
                part.add_trajectories(part_files, part_nums)

    def get_sequences(self, unique_objs_only=False, start_token=False) -> list[list[str]]:
        """
        Returns all the ordered sequences in which the objects were packed inside the box.

        :param start_token: If set to True all sequences are prepended with a start token, "<start>"
        :param unique_objs_only: If set to True only the sequences containing only unique objects are returned.
        """
        seqs = []
        for participant in self.participants:
            # Check if this participant has a scene with unique objects only
            if unique_objs_only and participant.part_num < BoxED.UNIQ_OBJS:
                continue
            for scene in participant.scenes:
                # Check if this is the first scene (i.e., only has unique objects)
                if unique_objs_only and scene.scene_num >= 2:
                    continue
                scene_seq = [obj.name for obj in scene.objs_info]
                if start_token:
                    scene_seq.insert(0, "<start>")
                seqs.append(scene_seq)

        return seqs

    def get_scene_durations(self) -> list[int]:
        """ Returns all the durations in milliseconds of each scene (i.e., of each box-packing). """
        durations = []
        for participant in self.participants:
            for scene in participant.scenes:
                durations.append(scene.objs_info[-1].trajectory[-1].time_stamp -
                                 scene.objs_info[0].trajectory[0].time_stamp)

        return durations

    def get_grasp_poses(self, grasp_type: str, objs: tp.Union[str, list[str]] = 'all') -> dict[str, list[Pose]]:
        """
        Returns all the grasp poses available for one or more objects in the dataset.

        :param grasp_type: Chooses between 'pick' or 'place' poses
        :param objs: Specifies the target object(s). Can be the object name, a list of objects names or 'all' for all
        grasps of all objects. Check BoxED.ALL_OBJS to see all object names
        :return: Returns a dictionary where the keys are the objects' names and each value is a list of Pose objects,
        each representing a grasp pose.
        """
        if grasp_type not in ['pick', 'place']:
            logging.error("grasp_type argument must be either 'pick' or 'place'.")
            exit(1)

        grasp_poses = {}
        target_objs = []
        if isinstance(objs, str):
            if objs == 'all':
                target_objs = BoxED.ALL_OBJS
            elif objs in BoxED.ALL_OBJS:
                target_objs.append(objs)
            else:
                logging.error("Specified object name is invalid. Check BoxED.All_OBJS for the list of all objects.")
                exit(1)
        elif isinstance(objs, list) and all(isinstance(elem, str) for elem in objs):
            if all(elem in BoxED.ALL_OBJS for elem in objs):
                target_objs = objs
            else:
                logging.error("At least one of the specified objects is invalid. Check BoxED.All_OBJS for the list "
                              "of all objects.")

                exit(1)
        else:
            logging.error("objs must be either: 'all' for all the objects, a list of object names or an object name.")
            exit(1)

        for participant in self.participants:
            for scene in participant.scenes:
                for obj in scene.objs_info:
                    if obj.name in target_objs:
                        # Object not yet in dictionary, create Pose list for it
                        if obj.name not in grasp_poses:
                            grasp_poses[obj.name] = [obj.pick_pose] if grasp_type == 'pick' else [obj.place_pose]
                        # Object already in dictionary, simply append the new pose to its list
                        else:
                            grasp_poses[obj.name].append(obj.pick_pose if grasp_type == 'pick' else obj.place_pose)

        return grasp_poses
