# The Linux libgomp workaround is loaded via `addopts = "-p nirikshak._runtime"` in pyproject.toml,
# before pytest captures output; importing it here would restart the process mid-capture.
