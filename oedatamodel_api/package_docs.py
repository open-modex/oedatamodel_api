import ast
import inspect
import importlib
import os
from oedatamodel_api.settings import ROOT_DIR, APP_DIR, APP_STATIC_DIR
import logging
import json


def saveToJsonFile(data, filepath, encoding="utf-8"):
    logging.info("saving %s" % filepath)
    with open(filepath, "w", encoding=encoding) as f:
        return json.dump(data, f, sort_keys=True, indent=2)


def buildPackageDocs(package_path=APP_DIR):
    """
    Create basic documentation from all .py files in a directory.
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

    def moduleFilter(moduleblacklist, modulelist):
        """
        Applys an filter to a list object that contains all modules in a
        directory. The filter can be applied by the moduleblacklist parameter.

        :param moduleblacklist:
        :param modulelist:
        :return:
        """
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

        # really need this?
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

        all_classes = {}
        for name, data in inspect.getmembers(dyn_import, inspect.isclass):
            # exclude imports
            if data.__module__ == module_scr:
                # ToDo: Check if structure {key: {key: value}} is valid -> maybe [] is better
                current_class = {"{}".format(name): "{}".format(inspect.getdoc(data))}
                all_classes.update(current_class)

        all_functions = {}
        for name, data in inspect.getmembers(dyn_import, inspect.isfunction):
            # exclude imports
            if data.__module__ == module_scr:
                # ToDo: Check if structure {key: {key: value}} is valid -> maybe [] is better
                current_func = {"{}".format(name): "{}".format(inspect.getdoc(data))}
                all_functions.update(current_func)

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
        # ToDo: Dump to JSON
        resp = {"data": [getModuleMembersDocstring(module) for module in folder_modules]}
        # resp.update(**getModuleMembersDocstring(folder_modules))
        print(resp)
        return resp

    except Exception as e:
        logging.ERROR(e)
        logging.ERROR("Does the folder at: {} exists?".format(package_path))


if __name__ == '__main__':
    buildPackageDocs()
