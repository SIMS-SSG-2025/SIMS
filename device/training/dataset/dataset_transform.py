import yaml
import os

def load_class_mapping(yaml_path):
    """
    Load class names from yaml file and return id to class name dict.
    """
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    names = data.get("names", [])
    names = [names[i] for i in range(len(names))]
    return {i: name for i, name in enumerate(names)}

def get_class_names(filename):
    """
    Load class names from yaml file.

    Args:
        filename (str): Path to YAML file.

    Returns list[str]: List of class names.
    """
    with open(filename, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("names", [])


def load_id_to_class(filename):
    """
    Loads id-to-class mappings from YAML file.

    Args:
        yaml_file_path (str): Path to the YAML file.

    Returns:
        dict: Dictionary mapping IDs (int) to class names (str)
    """
    with open(filename, 'r', encoding="utf-8") as file:
        data = yaml.safe_load(file)

    names_dict = data.get('names', {})
    cls_names = [v for k, v in sorted(names_dict.items(), key=lambda item: int(item[0]))]
    return cls_names


def remap_labels(labels_dir, keep_classes):
    """
    Remaps labels from 0 to N-1

    Args:
        labels_dir (str): path to YOLO label txt files
        keep_classes (list[int]): list of original class IDs to keep
    """
    keep_classes = sorted(keep_classes)
    id_map = {old: new for new, old in enumerate(keep_classes)}
    print("Mapping:", id_map)

    for file in os.listdir(labels_dir):
        if not file.endswith(".txt"):
            continue
        #path = os.path.join(labels_dir, file)
        path = r"\\?\\" + os.path.abspath(os.path.join(labels_dir, file))
        lines_out = []
        with open(path, "r") as f:
            for line in f:
                parts = line.strip().split()
                cls_id = int(parts[0])
                if cls_id in id_map:
                    parts[0] = str(id_map[cls_id])
                    lines_out.append(" ".join(parts))
        with open(path, "w") as f:
            f.write("\n".join(lines_out))


def remove_annotations(dataset_dir, class_names, classes_to_remove):
    """
    Create filtered label files by removing specified classes.

    Args:
        dataset_dir (str): Path to dataset directory.
        class_names (list[str]): List of class names.
        classes_to_remove (list[str]): List of class names to remove.

    """
    class_to_idx = {class_name: i for i, class_name in enumerate(class_names)}
    remove_ids = {class_to_idx[cls] for cls in classes_to_remove}

    all_ids = set(class_to_idx.values())
    keep_classes = sorted(all_ids - remove_ids)

    for split in ["train", "valid", "test"]:
        split_dir = os.path.join(dataset_dir, split)
        labels_dir = os.path.join(split_dir, "labels")
        print(labels_dir)
        new_labels_dir = os.path.join(split_dir, "labels_filtered")
        os.makedirs(new_labels_dir, exist_ok=True)
        for label_file in os.listdir(labels_dir):
            with open(os.path.join(labels_dir, label_file), "r", encoding="utf-8") as file:
                lines = file.readlines()

            filtered_lines = [
                line for line in lines if int(line.split()[0]) not in remove_ids
            ]

            #save_file = os.path.join(new_labels_dir, label_file)
            # save_file = r"\\?\\" + os.path.join(new_labels_dir, label_file)
            save_file = r"\\?\\" + os.path.abspath(os.path.join(new_labels_dir, label_file))
            with open(save_file, "w", encoding="utf-8") as file:
                file.writelines(filtered_lines)

    for split in ["train", "valid", "test"]:
        split_dir = os.path.join(dataset_dir, split)
        labels_dir = os.path.join(split_dir, "labels_filtered")
        remap_labels(labels_dir, keep_classes)

    new_class_names = [class_names[idx] for idx in keep_classes]
    yaml_data = {
        "nc": len(keep_classes),
        "names": new_class_names,
    }
    with open("ppe_dataset_filtered.yaml", "w") as file:
        yaml.dump(yaml_data, file)


if __name__ == '__main__':
    #cls_names = load_id_to_class("ppe_dataset.yaml")
    cls_names = get_class_names("ppe_dataset.yaml")
    print(cls_names)
    # cls_to_remove = ['Mask', 'NO-Mask', 'Safety Cone', 'machinery']
    cls_to_remove = ['gloves', 'boots', 'goggles', 'no_goggle', 'no_gloves', 'no_boots']
    #remove_annotations("ppe-dataset", cls_names, cls_to_remove)

