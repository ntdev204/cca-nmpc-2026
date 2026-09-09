from setuptools import find_packages, setup


package_name = "rai_runtime_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            [f"resource/{package_name}"],
        ),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    description="HTTP/WebRTC bridge for the canonical CCA-NMPC ROS 2 runtime.",
    license="Proprietary research code",
    entry_points={
        "console_scripts": [
            "runtime_bridge = rai_runtime_bridge.main:main",
            "slam_supervisor = rai_runtime_bridge.slam_supervisor:main",
        ]
    },
)
