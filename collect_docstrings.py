from lab_remote_control.devices import common
from lab_remote_control.devices import dab
from lab_remote_control.devices import dataformats
from lab_remote_control.devices import supply_load
from lab_remote_control.devices import power_analyzer
import inspect


modules = [common, dab, dataformats, supply_load, supply_load, power_analyzer]


def indent_docstring(docstring: str):
    return '\n'.join([f'    {line}' for line in docstring.splitlines()])


def construct_class_docstring(cls: type):
    base_class = str(inspect.getmro(cls)[1])
    base_class = base_class.replace('class', '')
    base_class = base_class.replace('<', '')
    base_class = base_class.replace('>', '')
    base_class = base_class.replace("'", '')
    base_class = base_class.replace('"', '')
    base_class = base_class.strip()
    signature = f'class {cls.__name__}({base_class}):'
    docstring = inspect.getdoc(cls)
    if not docstring:
        docstring = ''
    docstring = indent_docstring(docstring)
    return '\n'.join([signature, docstring])


def construct_function_docstring(f):
    if isinstance(f, property):
        if f.fget:
            name = f.fget.__name__
        elif f.fset:
            name = f.fset.__name__
        elif f.fget:
            name = f.fdel.__name__
        else:
            raise Exception('No property function')
        signature = f'property {name}'
    else:
        name = f.__name__
        try:
            try:
                signature = f'def {name}({inspect.signature(f)}):'
            except TypeError:
                signature = inspect.getsource(f)
                signature = signature.split('def')[1]
                signature = signature.split(':')[0]
                signature = f'def{signature}:'
        except KeyboardInterrupt:
            pass
    docstring = inspect.getdoc(f)
    if not docstring:
        docstring = ''
    return '\n'.join([signature, docstring])


def construct_class_docstrings(cls):
    class_docstring = construct_class_docstring(cls)
    docstrings = []
    for method_name, method in [item for item in vars(cls).items() if '__' not in item[0] and '_abc_impl' not in item[0]]:
        try:
            if isinstance(method, type):
                docstrings.append(construct_class_docstring(method))
            else:
                docstrings.append(construct_function_docstring(method))
        except AttributeError:
            pass
    docstrings.append('')
    docstrings.sort()
    docstrings = '\n'.join(docstrings)
    docstrings = indent_docstring(docstrings)
    return '\n'.join([class_docstring, docstrings])


if __name__ == '__main__':
    docstrings = []
    for module in modules:
        objects = [item for item in inspect.getmembers(module) if '__' not in item[0] and
                   (type(item[1]) == "<class 'function'>" or isinstance(item[1], type))]
        objects = [item for item in objects if item[1].__module__ == module.__name__]

        object_docstrings = [module.__name__]
        for name, object_ in objects:
            if isinstance(object_, type):
                object_docstrings.append(construct_class_docstrings(object_))
            else:
                object_docstrings.append(object_)
        object_docstrings.append('')
        docstrings.append('\n'.join(object_docstrings))
    docstrings.append('\n')
    docstrings.sort()

    docstrings = '\n'.join(docstrings)
    with open('lab_remote_control_doc.txt', 'w') as f:
        f.write(docstrings)
