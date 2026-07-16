# Contributing
Fetpype is an open source project and welcomes contributions! Here are some ideas on how to help:

1. Writing and improving the documentation
2. Reporting or fixing bugs
3. Adding your amazing pre-processing/reconstruction/segmentation/surface extraction method to fetpype.
4. Other features or enhancements

## 1. Improving documentation
Feel free to contribute to the documentation through a pull request. The documentation is a set of markdown pages in the `docs` folder. To edit and build it locally, you can first install the required packages and then deploy it locally:
```
pip install mkdocs-material pymdown-extensions mkdocstrings-python mkdocs-awesome-pages-plugin mkdocs-bibtex
mkdocs serve
```
This will serve the documentation, which you will be able to see by opening the local address `http://127.0.0.1:8000/` on your browser. 

## 2. Reporting Bugs
Bugs and issues can be reported on [GitHub](https://github.com/fetpype/fetpype/issues). Please check the bug has not already been reported by searching the issue tracker before submitting a new issue!

## 3. Adding your method to fetpype
Fetpype is designed to be a modular wrapper around exiting tools. It is based running calls to docker/singularity containers defined in a yaml file.

If you wish to incorporate your method into fetpype, please have a look at the page describing the pipeline step to which you want to contribute (i.e. [preprocessing](preprocessing.md), [reconstruction](reconstruction.md), [segmentation](segmentation.md) or [surface extraction](surface.md)). Each page describes what the step does, what kind of input and output are expected, and the tags that can be provided to interact with your container image. If you have trouble in making your method compatible with fetpype, don't hesitate opening an issue on [GitHub](https://github.com/fetpype/fetpype/issues).

## 4. Feature Requests
Feature requests can be made on [GitHub](https://github.com/fetpype/fetpype/issues) as well!

---
## Concrete steps
When you have developed something that you would like to add to Fetpype, you can then run the tests locally, along with flake8 formatting.

### Running tests locally
Install the package with the dev dependencies:
```
pip install -e ".[dev]"
```
Then run the test suite from the root of the repository:
```
pytest tests/
```

### Running flake8
The formatting must follow flake8, which can be installed and run in the command line. More info [here](https://flake8.pycqa.org/en/latest/).

### Solving Issues
Any new feature, bug fix or documentation contribution is welcome as a pull request (PR)! To do that, simply open a new [GitHub PR](https://github.com/fetpype/fetpype/pulls) with your contribution. Please include a clear description of the problem, refer to any relevant issues, and explain how your contribution solves the problem, and on which data you were able to test it.