For final deadline:

- implement a client (web, gui or cli) that makes the user pick between the hypermedia controls at the current node, and
  generates forms depending on the schema. If we do it as a cli we can reuse some of the code from the exercise
- crudely implement profile picture endpoint that returns one picture for all students, it doesn't matter at this point
- implement auxiliary service (not REST, as standalone process that answers to requests) that generates student card for
  given student id. Client application will use this service directly.

Improvemennts and future development:

- Use hashes or random numbers in URLs instead of database IDs, to avoid exposing them and having possible
  exploits/breaches. Courses could use their `code`, students probably shouldn't use their `ssn`.
- StudentAssessmentCollection/Item and CourseAssessmentCollection/Item are almost the same class. This would be the
  first simplification to apply to our API.