from setuptools import setup, find_packages

setup(name='aqualin-mqtt',
      version='0.9',
      description='aqualin to mqtt daemon',
      author='dmitry pervushin',
      author_email='dpervushin@gmail.com',
      url='http://github.com/dmitry-pervushin',
      entry_points={
         'console_scripts': [
             'aqualin-mqtt-daemon=aqualin_mqtt.__main__:main'
         ]
      },
      data_files = [('configs', ['aqualin.yaml'])],
      packages=find_packages(),
     )
