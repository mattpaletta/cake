import inspect
import subprocess
import sys
from distutils.command.build import build
from setuptools.command.install import install

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup

    ez_setup.use_setuptools()
    from setuptools import setup, find_packages


def compile_proto():
    cmd = "{0} -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. --mypy_out=. {1}".format(
            sys.executable.split("/")[-1],
            "cake/proto/cake.proto")
    print(cmd)
    ret = subprocess.call([cmd], shell = True)


class BuildCommand(build):
    def run(self):
        compile_proto()
        build.run(self)


class InstallCommand(install):
    def run(self):
        compile_proto()  # TODO:// Don't recompile if don't need to
        if not self._called_from_setup(inspect.currentframe()):
            # Run in backward-compatibility mode to support bdist_* commands.
            install.run(self)
        else:
            install.do_egg_install(self)  # OR: install.do_egg_install(self)

setup(
    name="cake",
    version="0.0.1",
    url='https://github.com/mattpaletta/cake',
    packages=find_packages(),
    include_package_data=True,
    install_requires=["grpcio",
                      "grpcio-tools",
                      "mypy-protobuf"],
    setup_requires=["grpcio-tools", "mypy-protobuf"],
    author="Matthew Paletta",
    author_email="mattpaletta@gmail.com",
    description="Cake implementation",
    license="BSD",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications',
    ],
    cmdclass={
        'build': BuildCommand,
        'install': InstallCommand,
    },
)