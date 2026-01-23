import unicodedata
import re
import json



class Project:
    def __init__(self,name:str):
        # These must all be pickleable
        self.name:str = name
        self.backend_option:str = "None"
        self.scan_from = 0
        self.scan_to = 10
        self.webcam_index = 0 # warning, if we load this and it doesn't work then we have an issue
        self.gap_fill_max = 3
        self.webcam_exposure = None

        self.scans = []

    def get_filename(self):
        return f"{self.name}.marimapper"

    def save(self):
        print("saving")
        json_data = json.dumps(self.__dict__, sort_keys=True, indent=4)
        with open(f"{self.name}.marimapper" , "w") as file:
            file.write(json_data)
        print("saved")

    def load(self, project_filename):
        try:
            with open(project_filename, "r") as file:
                self.__dict__ = json.load(file)
                return True
        except:
            return False


