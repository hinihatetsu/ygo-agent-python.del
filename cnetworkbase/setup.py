from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

ext = Extension('networkbase_cpp',
                sources=[
                    "networkbase.pyx",
                    "src\\network.cpp",
                    "src\\layer.cpp",
                    "src\\translate.cpp",
                    "src\\networkinfo.cpp",
                ],
                language = "c++",
                extra_compile_args=["-DEIGEN_NO_DEBUG"],
            )

setup(
    ext_modules = cythonize(ext,  language_level = "3"),
    include_dirs = [
        numpy.get_include(),
        ".\\include\\"
    ]
)