# Santa's Magical World
## Context
First project done as a part of the *"Tech-Front Manager 2"* training provided by **Matrice Association**. The project initial statement was given by **rBean** learning platform.

## Santa's API
This project first aim was to apply our basic knowledge of Python programming with the usage of **FLASK** & **RESTful API**.
Using classic methods *(e.g. GET, POST, PUT, DELETE)*, we were asked to work on a interfaceless API generating informations on multiple sort of items, categories, toys, elves, wishes or schedules.
The whole process forced us to confront several issues, like handling password using a give hashing technique, or handling multiple error cases.

## Resolution approach

In order to avoid repetitive piece of code, I choose to factor out some elements. Here are some of the created functions:
```python
checkExistingValue()
fetchOutput()
postItem()
updateItem()
```
All the functions are located in the `methods.py` file, alongside some documentation.
All the routes are located in the `run.py` file.

The research part has been a crucial phase, but can be improved.
There's still a lot to do in order to simplify the code. Function must be simpler, and this first attempt to factor highlited some new issues, like too much intricacies and dependencies.

## Configuration

Configuration in order to test the code is quite easy, please use a simple virtual environment and the usual:
```bash
pip install -r requirements.txt
```
To run some tests, you will find bash scripts in the *tests* directory.