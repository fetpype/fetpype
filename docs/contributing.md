# Contributing
Fetpype is an open source project and welcomes contributions! Here are some ideas on how to help:

- Writing and improving the documentation
- Reporting or fixing bugs
- Adding your amazing pre-processing/reconstruction/segmentation/surface extraction method to fetpype.
- Other features or enhancements


## Reporting Bugs
Bugs and issues can be reported on [GitHub](https://github.com/fetpype/fetpype/issues). Please check the bug has not already been reported by searching the issue tracker before submitting a new issue!

## Adding your method to fetpype
Fetpype is designed to be a modular wrapper around exiting tools. It is based running calls to docker/singularity containers defined in a yaml file.

If you wish to incorporate your method into fetpype, please have a look at the page describing the pipeline step to which you want to contribute (i.e. [preprocessing](preprocessing.md), [reconstruction](reconstruction.md), [segmentation](segmentation.md) or [surface extraction](surface.md)). Each page describes what the step does, what kind of input and output are expected, and the tags that can be provided to interact with your container image. If you have trouble in making your method compatible with fetpype, don't hesitate opening an issue on [GitHub](https://github.com/fetpype/fetpype/issues).

## Feature Requests
Feature requests can be made on [GitHub](https://github.com/fetpype/fetpype/issues) as well!

## Solving Issues
Any new feature, bug fix or documentation contribution is welcome as a pull request (PR)! To do that, simply open a new [GitHub PR](https://github.com/fetpype/fetpype/pulls) with your contribution. Please include a clear description of the problem, refer to any relevant issues, and explain how your contribution solves the problem, and on which data you were able to test it.