# 1. Update output format to enable automatic inline annotations.
# 2. From documentation: "Currently, the Ruff formatter does not
#    sort imports. In order to both sort imports and format, call
#    the Ruff linter and then the formatter"
ruff check --select I --fix --output-format=github .
ruff format .
