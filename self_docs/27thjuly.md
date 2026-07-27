# Show evaluations to the frontend

- create a frontend page in @../operations-copilot-js and serve @src/routes/eval.py api endpoints to the frontend
- only one page should cover the evaluations, create a div with a dropdown from where user selects the scenario.
- once user selects the scenario, the below div should render the json from the orchestrator_dataset.json 
- a play button should be on the right of the div, at the bisection of the div, clicking which fires off the evaluation
- the evaluation returns are then rendered at another div below.
- the return format should be one type of results from all the eval apis, showing a table matching correctness, actual agent output and expected result
