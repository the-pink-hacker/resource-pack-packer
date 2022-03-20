import json
import os
from typing import Optional

from resource_pack_packer.selectors import parse_minecraft_identifier


def get_from_dict(dictionary: dict, key: str, default=None):
    if key in dictionary:
        return dictionary[key]
    return default


def find_model(identifier: str, temp_dir: str) -> str:
    model_path = parse_minecraft_identifier(identifier, "models", "json")
    return os.path.join(temp_dir, model_path)


class Model:
    parent: Optional[str]
    textures: Optional[dict]
    elements: list[dict]
    display: Optional[dict]

    def __init__(self, parent: Optional[str], textures: Optional[dict], elements: list[dict], display: Optional[dict], temp_dir: str):
        self.parent = parent
        self.textures = textures
        self.elements = elements
        self.display = display

        if self.parent is not None:
            self.apply_parent(temp_dir)

    @staticmethod
    def parse(data: dict, temp_dir: str) -> "Model":
        return Model(get_from_dict(data, "parent"),
                     get_from_dict(data, "textures"),
                     get_from_dict(data, "elements", []),
                     get_from_dict(data, "display"),
                     temp_dir)

    @staticmethod
    def parse_file(file, temp_dir: str) -> "Model":
        with open(file, "r") as model:
            data = json.load(model)
        return Model.parse(data, temp_dir)

    def apply_parent(self, temp_dir: str):
        parent_model = Model.parse_file(os.path.join(temp_dir, find_model(self.parent, temp_dir)), temp_dir)

        # Apply elements to child
        if len(self.elements) == 0:
            self.elements = parent_model.elements

    @staticmethod
    def save(model: "Model", path: str):
        model_data = {}
        if model.parent is not None:
            model_data |= {"parent": model.parent}
        if model.textures is not None:
            model_data |= {"textures": model.textures}
        if len(model.elements) >= 1:
            model_data |= {"elements": model.elements}
        if model.display is not None:
            model_data |= {"display": model.display}

        with open(path, "w", encoding="utf-8") as file:
            json.dump(model_data, file, indent=2, ensure_ascii=False)


class RPPModel:
    identifier: str
    modify: dict

    def __init__(self, identifier: str, modify: dict):
        self.identifier = identifier
        self.modify = modify

    @staticmethod
    def parse(data: dict) -> "RPPModel":
        return RPPModel(get_from_dict(data, "identifier"), get_from_dict(data, "modify"))

    @staticmethod
    def parse_file(file: str) -> "RPPModel":
        with open(file, "r") as model:
            data = json.load(model)
        return RPPModel.parse(data)

    def _modify(self, temp_dir: str) -> Model:
        model = Model.parse_file(find_model(self.modify["model"], temp_dir), temp_dir)
        if self.modify["type"] == "translate":
            x = get_from_dict(self.modify["arguments"], "x", 0.0)
            y = get_from_dict(self.modify["arguments"], "y", 0.0)
            z = get_from_dict(self.modify["arguments"], "z", 0.0)

            for element in model.elements:
                element["from"] = [element["from"][0] + x, element["from"][1] + y, element["from"][2] + z]
                element["to"] = [element["to"][0] + x, element["to"][1] + y, element["to"][2] + z]
        return model

    def process(self, temp_dir: str) -> tuple[Model, str]:
        return self._modify(temp_dir), self.identifier
