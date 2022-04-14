import os
import numpy as np
import matplotlib.pyplot as plt
import json
import sys
import argparse
from pathlib import Path


def dicts_in_list(new_list: list):  # returns a list of all dictionaries
    dicts = []  # list of dictionaries
    for item in new_list:
        if isinstance(item, dict):  # adding a new dictionary in a list
            dicts.append(item)
        elif isinstance(item, list):  # recursion if it is a list
            dicts = dicts + dicts_in_list(item)
    return dicts


# finding the maximum nesting of lists named children[] in the json file
def UI_tree_depth_finder(my_dict: dict, count=0):
    branches = []  # list of branches depths
    for key in my_dict or ():
        if (isinstance(my_dict[key], list)) and (key == "children"):
            for item in dicts_in_list(my_dict[key]):
                branches.append(1)
                count = UI_tree_depth_finder(item, count)
                branches[-1] += count  # adding a number we had got from recursion
        elif (isinstance(my_dict[key], list)) and (key != "children"):
            for item in dicts_in_list(my_dict[key]):
                branches.append(0)
                count = UI_tree_depth_finder(item, count)
                branches[-1] += count  # adding a number we had got from recursion
        elif isinstance(my_dict[key], dict):
            branches.append(0)
            count = UI_tree_depth_finder(my_dict[key], count)
            branches[-1] += count  # adding a number we had got from recursion
    if not branches:
        count = 0
    else:
        count = max(branches)
    return count


def apps_traces_max_of_screens_counter(base_path):
    p = Path(base_path)
    count_of_apps = 0  # amount of apps in dataset
    count_of_traces = 0  # amount of traces in dataset
    screen_count = 0  # current trace length
    max_screen_count = 0  # max length of a trace
    for current_application in p.iterdir():
        count_of_apps += 1
        for current_trace in current_application.iterdir():
            count_of_traces += 1
            for current_info in current_trace.iterdir():
                if current_info.name == "screenshots":
                    for current_screenshot in current_info.iterdir():
                        screen_count += 1
                    if screen_count > max_screen_count:
                        max_screen_count = screen_count
                    screen_count = 0
    max_screen_count >>= 1  # Division by 2 using a bit shift, because in my dataset there is a duplication
    # of files of the form: ._a.jpg and a.jpg
    numbers_list = [count_of_apps, count_of_traces, max_screen_count]
    return numbers_list


def histogram_of_traces_lengths_builder(my_path, size):
    x = np.arange(1, size + 1)
    y = np.zeros(size + 1, dtype=int)
    cur_path = Path(my_path)
    screenshots_count = 0  # current trace length
    for cur_application in cur_path.iterdir():
        for cur_trace in cur_application.iterdir():
            for cur_info in cur_trace.iterdir():
                if cur_info.name == "screenshots":
                    for cur_screenshot in cur_info.iterdir():
                        screenshots_count += 1
                    screenshots_count >>= 1  # similarly with the operation on max_count
                    y[screenshots_count] += 1
                    screenshots_count = 0
    coords = [x, y]
    return coords


def max_depth_of_UI_tree_finder(start_path):
    max_depth = 0  # max depth of a UI-tree
    app_with_max_depth = ""
    curr_path = Path(start_path)
    live_path = curr_path
    for curr_application in curr_path.iterdir():
        for curr_trace in curr_application.iterdir():
            for curr_info in curr_trace.iterdir():
                if curr_info.name == "view_hierarchies":
                    for curr_json in curr_info.iterdir():
                        if curr_json.name[:2] != "._":
                            live_path = os.path.join(curr_info, curr_json.name)
                            with open(live_path) as file:
                                current_dictionary = json.load(file)
                                depth = UI_tree_depth_finder(current_dictionary)
                                if depth > max_depth:
                                    max_depth = depth
                                    app_with_max_depth = curr_application.name
                                    json_wth_max_depth = curr_json.name
    info_list = [max_depth, app_with_max_depth, json_wth_max_depth]
    return info_list


def Parser_creator():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?')
    return parser


if __name__ == '__main__':
    my_parser = Parser_creator()
    namespace = my_parser.parse_args()
    if namespace.path:
        current_path = namespace.path
    else:
        print("You must pass the path to the dataset")
        sys.exit()
    my_list = apps_traces_max_of_screens_counter(current_path)
    # Finished counting all the necessary values
    print("This dataset has ", my_list[0], " apps")
    print("This dataset has ", my_list[1], " traces")
    # Starting finding the number of paths of different lengths
    coordinate_lines = histogram_of_traces_lengths_builder(current_path, my_list[2])
    result_list = max_depth_of_UI_tree_finder(current_path)
    print("Maximum depth of a UI-tree in this dataset is:", result_list[0],
          ".And it is achieved on the app: ",
          result_list[1], " in json file: ", result_list[2])

    # Building a histogram based on the data obtained the number of traces of different lengths
    fig, ax = plt.subplots()
    ax.bar(coordinate_lines[0], coordinate_lines[1][1:])
    ax.set_facecolor('seashell')
    fig.set_facecolor('floralwhite')
    fig.set_figwidth(12)
    fig.set_figheight(6)
    ax.set_xlabel("Length of trace")
    ax.set_ylabel("Number of applications")
    ax.set_title("Histogram of the dependence of the number of paths on their length")
    plt.show()
