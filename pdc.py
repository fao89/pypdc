import aiohttp
import asyncio
from datetime import datetime

from aiohttp.client_exceptions import ClientResponseError
from packaging.version import Version
from packaging.requirements import Requirement

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


def sort_releases(releases):
    release_dates = {}
    for release, data in releases.items():
        dt_string = data[0]["upload_time"]
        upload_time = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")
        release_dates[release] = upload_time
    return [k for k, v in sorted(release_dates.items(), key=lambda item: item[1], reverse=True)]


async def get_pypi_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            pypi_data = await response.json()
            return pypi_data


async def print_compatible_plugins(pulpcore_releases):
    pypi_plugins_data = []
    for plugin in PULP_PLUGINS:
        pkg_url = PYPI_ROOT.format(plugin)
        try:
            pypi_plugins_data.append(get_pypi_data(pkg_url))
        except ClientResponseError as exc:
            if 404 == exc.status:
                print(f"{plugin}  not found on PyPI")
                continue

    done, _ = await asyncio.wait(pypi_plugins_data)
    pypi_plugins_data = [i.result() for i in done]

    for idx, pulpcore_version in enumerate(pulpcore_releases):
        if idx == 3:  # Last 3 releases
            break
        shown = False
        for pypi_data in pypi_plugins_data:
            plugin = pypi_data["info"]["name"]
            latest_plugin_version = pypi_data["info"]["version"]
            plugin_versions = sort_releases(pypi_data["releases"])

            for plugin_version in plugin_versions:
                if plugin_version == latest_plugin_version:
                    plugin_requirements = pypi_data["info"]["requires_dist"]
                else:
                    req_data = await get_pypi_data(PYPI_ROOT.format(f"{plugin}/{plugin_version}"))
                    plugin_requirements = req_data["info"]["requires_dist"]
                pulpcore_req_for_plugin = Requirement(
                    [r for r in plugin_requirements if "pulpcore" in r][0]
                )
                if Version(pulpcore_version) in pulpcore_req_for_plugin.specifier:
                    if not shown:
                        print(f"\nCompatible with pulpcore-{pulpcore_version}")
                        shown = True
                    full_plugin_name = f"{plugin}-{plugin_version}"
                    print(f" -> {full_plugin_name: <35} requirement: {pulpcore_req_for_plugin}")
                    break

if __name__ == "__main__":
    pulpcore_url = PYPI_ROOT.format("pulpcore")
    response = asyncio.run(get_pypi_data(pulpcore_url))
    pulpcore_releases = sort_releases(response["releases"])
    asyncio.run(print_compatible_plugins(pulpcore_releases))
