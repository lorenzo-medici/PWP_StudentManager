## Internal ReadMe

### IMPORTANT STUFF:

- Use `with app.app_context():` when accessing the database
- Use `studentmanager.utils.generate_ssn` to generate valid ssn's based on the date object passes (e.g. `datetime.date(2000, 1, 1)`)
- Use `url_for("api.sensoritem", sensor="uo-donkeysensor-1")` instead
  of `api.url_for(SensorItem, sensor="uo-donkeysensor-1")` (of course with our entity names)
- You can create a file for each pair of resources in `studentmanager/resources`
- Example project for implementing resources: https://github.com/enkwolf/pwp-course-sensorhub-api-example

### TO IMPLEMENT

- resource classes
- json schema
- url validator
- tests

### Daniel

- Assessments

### Alessandro

- Students

### Pranav

- Courses

### Lorenzo

- Project structure
- regex for student ssn
- wiki

# TODO:

- Check why `from model import model` is not at the top in `app.py`
- Add Client example in the wiki for Deadline 1
- Fix project structure

### Usage

1. Initialising empty SQLite database:

`flask --app app init-db`

2. Generate and persist test data:

`flask --app app testgen`

3. Run the application:

`flask --app app run`
