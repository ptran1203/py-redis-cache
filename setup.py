import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "redis-cache-py",
    version = "0.0.2",
    author = "Phat Tran",
    author_email = "phatth1203@gmail.com",
    description = "Redis Cache For Python",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/ptran1203/py-redis-cache",
    project_urls = {
        "Bug Tracker": "https://github.com/ptran1203/py-redis-cache/issues",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # package_dir = {"": "."},
    packages=setuptools.find_packages(),
    install_requires=['redis>=5.0.0'],
    setup_requires=['pytest-runner==5.3.1'],
    tests_require=['pytest==6.2.5', 'redis==4.4.4'],
)