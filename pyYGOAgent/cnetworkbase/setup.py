from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

ext = Extension('networkbase',
                sources=[
                    "networkbase.pyx",
                    "src\\network.cpp",
                    "src\\layer.cpp",
                    "src\\translate.cpp",
                ],
                language = "c++",
                extra_compile_args=["-DEIGEN_NO_DEBUG"],
            )

setup(
    name = 'networkbase',
    ext_modules = cythonize(ext,  language_level = "3"),
    include_dirs = [
        numpy.get_include(),
        ".\\include\\",
        #/path/to/Eigen,
    ]
)