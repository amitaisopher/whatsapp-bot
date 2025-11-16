## Dev environment tips
- Use `uv` as package manager.
- Use Ruff as linter for Python files. use `uvx ruff check . --fix`  and `uvx ruff format` to check all files.
- Include type annotations for all code you generate.
- Use PyTest as the testing framework to run tests
- Generate Dockerfile and Docker Compose files in order to run the app and any required services on containers.
 
## Testing instructions
- All tests should be added to `tests` folder which should be located under project's root folder.
- From the project's root you can just call `uv run pytest`.
- To focus on one step, add the Vitest pattern: `uv pytest run -t "<test name>"`.
- Fix any test or type errors until the whole suite is green.
- 
- Add or update tests for the code you change, even if nobody asked.
 
## PR instructions
- Always run `uvx ruff check . --fix`, and `uvx ruff format`, and `uv run pytest`  before committing.
- Always make sure to update doc files (located in docs folder) as well as Readme.md file.
- Document that changes of refactors and updates in CHANGELOG.md file - this will help to keep track any changes made to the code over time in chronological manner.