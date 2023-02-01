#!/usr/bin/env python3

import os
import json
from typing import Dict, Union
import random
import glob
import argparse

def merge_annotations(annotation_files, output2):
    merged_annotations = {"licenses":[], "info": [], "categories": [],"images": [], "annotations": []}
    category_lookup = {}
    max_annotation_id = 0
    max_image_id = 0
    max_annotation_img_id = 0

    license = [{"name": "", "id": 0, "url": ""}]
    info = [{"contributor": "", "date_created": "", "description": "", "url": "", "version": "", "year": ""}]    

    merged_annotations["info"].append(info)
    merged_annotations["licenses"].append(license)

    for annotation_file in annotation_files:
        with open(annotation_file, "r") as f:
            annotation_data = json.load(f)

        for category in annotation_data["categories"]:
            category_lookup[category["id"]] = category
            merged_annotations["categories"].append(category)

        for image in annotation_data["images"]:
            image["id"] = max_image_id + 1
            max_image_id += 1
            merged_annotations["images"].append(image)

        for annotation in annotation_data["annotations"]:
            annotation_category = category_lookup[annotation["category_id"]]
            if annotation_category["id"] == 1:
                annotation["name"] = annotation_category["name"]
                annotation["id"] = max_annotation_id + 1
                annotation["image_id"] = annotation["image_id"] + max_annotation_img_id
                max_annotation_id += 1
                merged_annotations["annotations"].append(annotation)
        
        max_annotation_img_id = len(merged_annotations["images"])
    save_annotations_file(merged_annotations, outputfolder2, "merged_annotations.json")

    return merged_annotations



def save_annotations_file(annotation_file_json, outputfolder1, file_name):
    if not os.path.exists(outputfolder1):
        os.makedirs(outputfolder1)
    with open(os.path.join(outputfolder1, file_name), "w") as file:
        json.dump(annotation_file_json, file)


def select_annotations_by_supercategory_name(merged_annotations_json, supercategory_names, outputfolder1):
    selected_annotations = {"licenses":[], "info": [],"categories": [],"images": [], "annotations": []}

    license = [{"name": "", "id": 0, "url": ""}]
    info = [{"contributor": "", "date_created": "", "description": "", "url": "", "version": "", "year": ""}]    

    selected_annotations["info"].append(info)
    selected_annotations["licenses"].append(license)

    for category in merged_annotations_json["categories"]:
            selected_annotations["categories"].append(category)

    y = []
    for annotation in merged_annotations_json["annotations"]:
        if annotation["name"] in supercategory_names:
            selected_annotations["annotations"].append(annotation)
            y.append(annotation["image_id"])

    for image in merged_annotations_json["images"]:
        if image["id"] in y:
            selected_annotations["images"].append(image)
    
    save_annotations_file(selected_annotations, outputfolder2, f"supercategory_annotations.json")
    return selected_annotations

def split_annotations(annotation_file_json, outputfolder2, train_split=0.8):

    train_annotations = {"licenses":[], "info": [],"categories": [],"images": [], "annotations": []}
    val_annotations = {"licenses":[], "info": [],"categories": [],"images": [], "annotations": []}

    license = [{"name": "", "id": 0, "url": ""}]
    info = [{"contributor": "", "date_created": "", "description": "", "url": "", "version": "", "year": ""}]    

    train_annotations["info"].append(info)
    train_annotations["licenses"].append(license)
    val_annotations["info"].append(info)
    val_annotations["licenses"].append(license)

    categories = list(set([category["name"] for category in annotation_file_json["categories"]]))
 
    for category in categories:
        category_annotations = [anno for anno in annotation_file_json["annotations"] if anno["name"] == category]
        num_training = int(len(category_annotations) * train_split)                         ## "category_type"
        
        random.shuffle(category_annotations)

        training_annotations = category_annotations[:num_training]
        validation_annotations = category_annotations[num_training:]
        
        train_annotations["annotations"].extend(training_annotations)
        val_annotations["annotations"].extend(validation_annotations)
        
        train_annotations["categories"] = annotation_file_json["categories"]
        val_annotations["categories"] = annotation_file_json["categories"]  

        print("training annotation of",category,":",len(training_annotations))
        print("validation annotation of",category,":",len(validation_annotations))
    # Collect all images ids used in annotations
    train_img_id = set([anno["image_id"] for anno in train_annotations["annotations"]])
    val_img_id = set([anno["image_id"] for anno in val_annotations["annotations"]])
    
    # filter images 
    train_annotations["images"] = [img for img in annotation_file_json["images"] if img["id"] in train_img_id]
    val_annotations["images"] = [img for img in annotation_file_json["images"] if img["id"] in val_img_id]
    
    save_annotations_file(train_annotations, outputfolder2, "train_annotations.json")
    save_annotations_file(val_annotations, outputfolder2, "val_annotations.json")
    
    return train_annotations, val_annotations

def check_dataset(coco_format_json: list):
    image_paths = set()
    image_ids = set()

    for file in coco_format_json:
        with open(file, "r") as f:
            file_data = json.load(f)
            
            if "images" not in file_data or "annotations" not in file_data:
                print(f"{file} does not contain 'images' or 'annotations' keys.")
                continue
            
            for image in file_data["images"]:
                if "file_name" not in image or "id" not in image:
                    print(f"{file} contains an image object without 'file_name' or 'id' keys.")
                    continue
                
                if image["file_name"] in image_paths:
                    print("Duplicate image file path found: ", image["file_name"])
                else:
                    image_paths.add(image["file_name"])
                image_ids.add(image["id"])
    
            for annotation in file_data["annotations"]:
                if "image_id" not in annotation or "id" not in annotation:
                    print(f"{file} contains an annotation object without 'image_id' or 'id' keys.")
                    continue
                
                if annotation["image_id"] not in image_ids:
                    print("Annotation with id ", annotation["id"], " has invalid image_id: ", annotation["image_id"])

outputfolder2 = "outputfolder1"
outputfolder = "sorted_annotations"
with open("folder_path.json", "r") as f:
    data = json.load(f)

folder_path = data["folder_path"]

print(f"Folder path: {folder_path}")

json_files = glob.glob(os.path.join(folder_path, '**/*.json'), recursive=True)

check_dataset(json_files)


json_files1 = glob.glob(os.path.join(folder_path, '**/*.json'), recursive=True)
merged_annotations = merge_annotations(json_files1,outputfolder2)

parser = argparse.ArgumentParser(description='Get inputs from user')
parser.add_argument('inputs', type=str, nargs='*', help='The inputs from the user')

args = parser.parse_args()
print('Inputs:', args.inputs)
supercategory_name = args.inputs
#supercategory_name = {"cookies_box_small_face","soap","coffee_bottle_top"} ##user_list
selected_annotations = select_annotations_by_supercategory_name(merged_annotations, supercategory_name, outputfolder2)

# Split annotations
t, v = split_annotations(selected_annotations, outputfolder2=outputfolder2)

