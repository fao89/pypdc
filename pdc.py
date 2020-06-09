import requests
from semantic_version import SimpleSpec, Version

PYPI_ROOT = "https://pypi.org/pypi/{}/json"
PULP_PLUGINS = [
    "galaxy-ng",
    "pulp-ansible",
    "pulp-certguard",
    "pulp-container",
    "pulp-cookbook",
    "pulp-deb",
    "pulp-file",
    "pulp-gem",
    "pulp-maven",
    "pulp-npm",
    "pulp-python",
    "pulp-rpm",
]

pulpcore_url = PYPI_ROOT.format("pulpcore")
response = requests.get(pulpcore_url)
pulpcore_releases = response.json()["releases"].keys()
to_remove = []

for pulpcore_version in reversed([*pulpcore_releases]):
    PULP_PLUGINS = [i for i in PULP_PLUGINS if i not in to_remove]
    shown = False
    for plugin in PULP_PLUGINS:
        pkg_url = PYPI_ROOT.format(plugin)
        response = requests.get(pkg_url)
        if response.status_code == 404:
            print(f"{plugin}  not found on PyPI")
            continue

        plugin_version = response.json()["info"]["version"]
        plugin_requirements = response.json()["info"]["requires_dist"]
        pulpcore_requirement = [r for r in plugin_requirements if "pulpcore" in r][0]
        req = pulpcore_requirement.split("(")[-1].replace(")", "")
        minor = req.split(".")[-1]
        for index, c in enumerate(minor):
            if not c.isdigit():
                break
        index = len(minor) if len(minor) == 1 else index
        spec = SimpleSpec(req.replace(minor, minor[0:index]))
        matches = spec.match(Version(pulpcore_version))
        if matches:
            if not shown:
                print(f"\nCompatible with pulpcore-{pulpcore_version}")
                shown = True
            print(f" -> {plugin}-{plugin_version} requirement: {pulpcore_requirement}")
            to_remove.append(plugin)

