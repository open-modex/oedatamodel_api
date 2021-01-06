"""
Build documentation on all module (.py) files in a directory.
The result is stored in json format and later rendered in the
index.html. The generated files are stored in the app static
directory.

Known Issues: The command "python webapp.py" sometimes throws
an exception if "python package_docs.py" is not run first.
"""
import ast
import inspect
import importlib
import os
from oedatamodel_api.settings import ROOT_DIR, APP_DIR, APP_STATIC_DIR
import logging
import json


def saveToJsonFile(data, filename, filepath=APP_STATIC_DIR, encoding="utf-8"):
    logging.info("saving %s" % filepath)
    # if json.
    with open(os.path.join(filepath, filename), "w", encoding=encoding) as f:
        return json.dump(data, f, sort_keys=True, indent=2)


def loadFromJsonFile(filepath, filename=None, encoding="utf-8"):
    logging.info("load file: %s" % filename)
    if os.path.exists(os.path.join(filepath, filename)):
        with open(os.path.join(filepath, filename), "r", encoding=encoding) as f:
            return json.load(f)
    else:
        print("The directory: {} or file: {} does not exist! If the directory is empty, try to run package_docs.py first.".format(filepath, filename))


def getCurrentlyAvailableMappings(base_path, dir_name):
    """

    :param base_path:
    :param dir_name:
    :return:
    """

    mappings = []
    mappings_dir = os.path.join(base_path, dir_name)

    for m in os.listdir(mappings_dir):
        mapping_details_json = loadFromJsonFile(mappings_dir, m)
        mapping = {"name": m.split(".")[0], "base_mapping": mapping_details_json["base_mapping"]}
        mappings.append(mapping)

    return {"mapping_collection": mappings}




def moduleFilter(module_docs):
    """
    applys an filter to a list object that contains all modules in a
    directory. the filter can be applied by the moduleblacklist parameter.

    :param moduleblacklist:
    :param modulelist:
    :return:
    """

    module_scope = ["mapping_custom"]

    modules = module_docs["data"]
    filtered_modules = [module for module in modules if module_scope[0] in module.values()]

    return filtered_modules


def buildPackageDocs(package_path=APP_DIR):
    """
    Create basic documentation from all .py files in a package source
    directory.
    The Documentation is created at build time and is intended to
    be saved to a file. The result is stored as key: value where
    the key is either the module name, class name or function name
    and the value contians the corresponding docstring that is defined
    at the beginning of the file/class/function.

    :param package_path: PATH to package source folder
    :return:
    """

    def validatePackagePath(path):
        pass

    def getModuleMembersDocstring(module):
        """
        Get the the name and docstring for module members like
        module, classes and functions. The result is expected
        to exclude classes or functions that are imported to the
        module.

        :param module:
        :return:
        """

        # really need this? /
        # Find better way to read script metadata (comment at the top)
        with open(module, 'r') as f:
            tree = ast.parse(f.read())

        # module file name
        mod_n = os.path.basename(module)
        # package name
        package_scr = os.path.basename(os.path.dirname(module))
        # remove the file format (.py) to get module name
        module_scr = mod_n.split(".")[0]
        # import statement like: from package import module
        dyn_import = importlib.import_module(module_scr, package="."+package_scr)

        all_classes = []
        for name, data in inspect.getmembers(dyn_import, inspect.isclass):
            # exclude imports
            if data.__module__ == module_scr:
                # ToDo: Check if structure {key: {key: value}} is valid -> maybe [] is better
                current_class = {"name": "{}".format(name), "description": "{}".format(inspect.getdoc(data))}
                all_classes.append(current_class)

        all_functions = []
        for name, data in inspect.getmembers(dyn_import, inspect.isfunction):
            # exclude imports
            if data.__module__ == module_scr:
                # ToDo: Check if structure {key: {key: value}} is valid -> maybe [] is better
                current_func = {"name": "{}".format(name), "description": "{}".format(inspect.getdoc(data))}
                # print(current_func)
                all_functions.append(current_func)

        # print(all_functions)

        # get the Docstring at the top of a script file
        general_docs = ast.get_docstring(tree)
        mod_class_docs = all_classes
        mod_func_docs = all_functions

        return {"ModuleName": module_scr,
                "ModuleGeneralDescription": general_docs,
                "ClassDocs": mod_class_docs,
                "FunctionDocs": mod_func_docs}

    try:
        # ToDO: Validate the package path
        folder_modules = [str(file) for file in package_path.iterdir() if str(file).endswith('.py')]
        resp = {"data": [getModuleMembersDocstring(module) for module in folder_modules]}
        # resp.update(**getModuleMembersDocstring(folder_modules))
        return resp

    except Exception as e:
        logging.ERROR(e)
        logging.ERROR("Does the folder at: {} exists?".format(package_path))


if __name__ == '__main__':
    # Build module Docs and save to json file
    a = buildPackageDocs()
    result = moduleFilter(a)
    saveToJsonFile(result[0], "docs_custom_mapping.json")

    # Get available mappings and save to json file
    b = getCurrentlyAvailableMappings(APP_DIR, "mappings")
    saveToJsonFile(b, "docs_current_mappings.json")
