from setuptools import find_packages, setup

package_name = 'health_monitor_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jdb3',
    maintainer_email='jalen.beeman@gmail.com',
    description='TODO: Package description',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            f'communications_monitor = {package_name}.communications_monitor:main',
            f'computer_monitor = {package_name}.computer_monitor:main',
            f'chassis_monitor = {package_name}.chassis_monitor:main',
            f'arm_monitor = {package_name}.arm_monitor:main',
            f'comms_monitor = {package_name}.comms_monitor:main'
        ],
    },
)
