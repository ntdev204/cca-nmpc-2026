from setuptools import find_packages, setup


package_name = "cca_perception"

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
    description="Camera pose recognition and LiDAR-fused context input for CCA-NMPC.",
    license="Proprietary research code",
    entry_points={
        "console_scripts": [
            "cca_perception_node = cca_perception.perception_node:main",
        ]
    },
)
