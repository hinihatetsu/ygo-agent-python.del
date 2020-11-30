from setuptools import setup, Extension
import numpy
from Cython.Build import cythonize

ext = Extension('networkbase',
                sources=[
                    "networkbase.pyx",
                    "src\\network.cpp",
                    "src\\layer.cpp",
                    "src\\translate.cpp",
                ],
                language = "c++",
                extra_compile_args=[],
            )

setup(
    name = 'networkbase',
    ext_modules = cythonize(ext,  language_level = "3"),
    include_dirs = [
        numpy.get_include(),
        ".\\src\\",
        "C:\\Users\\Shuhei\\dev\\C_C++\\include\\",
    ]
)