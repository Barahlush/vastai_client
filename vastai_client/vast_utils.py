from __future__ import print_function, unicode_literals

import json
import re

from loguru import logger

from vastai_client.models import QueryType

try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError  # type: ignore

try:
    input = raw_input  # type: ignore  # Python 2.X
except NameError:
    pass


def translate_null_strings_to_blanks(d: dict[str, str]) -> dict[str, str]:
    """Map over a dict and translate any null string values into ' '.
    Leave everything else as is. This is needed because you cannot add TableCell
    objects with only a null string or the client crashes.

    :param Dict d: dict of item values.
    :rtype Dict:
    """

    def translate_nulls(s: str) -> str:
        # Beware: locally defined function.
        if s == "":
            return " "
        return s

    new_d = {k: translate_nulls(v) for k, v in d.items()}
    return new_d


def parse_query(
    query_str: str | list[str],
    res: QueryType | None = None,
) -> QueryType:
    """Basically takes a query string (like the ones in the examples of commands
    for the search__offers function) and processes it into a dict of URL parameters
    to be sent to the server.

    Args:
        query_str (str): The query string to be processed.
        res (dict): The dictionary to store the URL parameters.

    Returns
    -------
        dict: The processed dictionary of URL parameters.
    """
    if res is None:
        res = {}
    if isinstance(query_str, list):
        query_str = " ".join(query_str)
    query_str = query_str.strip()
    opts = re.findall(
        (
            "([a-zA-Z0-9_]+)"
            "( *[=><!]+| +(?:[lg]te?|nin|neq|eq|not ?eq|not ?in|in) )"
            "?( *)(\\[[^\\]]+\\]|[^ ]+)?( *)"
        ),
        query_str,
    )

    joined = "".join("".join(x) for x in opts)
    if joined != query_str:
        raise ValueError(
            "Unconsumed text. Did you forget to quote your query? "
            + repr(joined)
            + " != "
            + repr(query_str)
        )
    for field, op, _, value, _ in opts:
        value = value.strip(",[]")
        if field not in res:
            res[field] = {}
        v = res[field]

        op = op.strip()
        op_name = op_names.get(op)

        if field in field_alias:
            field = field_alias[field]

        if field not in fields:
            logger.warning(
                "Warning: Unrecognized field: {},"
                "see list of recognized fields.".format(field),
            )
        if not op_name:
            raise ValueError(
                "Unknown operator. Did you forget to quote your query? "
                + repr(op).strip("u")
            )
        if op_name in ["in", "notin"]:
            value = [x.strip() for x in value.split(",") if x.strip()]
        if not value:
            raise ValueError(
                "Value cannot be blank. Did you forget to quote your query? "
                + repr((field, op, value))
            )
        if not field:
            raise ValueError(
                "Field cannot be blank. Did you forget to quote your query? "
                + repr((field, op, value))
            )
        if value in ["?", "*", "any"]:
            if op_name != "eq":
                raise ValueError("Wildcard only makes sense with equals.")
            if type(v) is dict:
                if field in v:
                    del v[field]
            if field in res:
                del res[field]
            continue

        if field in field_multiplier:
            value = str(float(value) * field_multiplier[field])

        if type(v) is dict:
            v[op_name] = value.replace('_', ' ')
        res[field] = v
    return res


def parse_vast_url(url_str: str) -> tuple[int, str]:
    """Breaks up a vast-style url in the form instance_id:path and does
        some basic sanity type-checking.

    Args:
        url_str (str): The vast-style url in the form of instance_id:path.

    Returns
    -------
         tuple: instance_id and path.
    """
    path = url_str
    if ":" in url_str:
        url_parts = url_str.split(":", 2)
        if len(url_parts) == 2:
            instance_id_str, path = url_parts
        else:
            raise ValueError("Invalid VRL (Vast resource locator).")

        try:
            instance_id = int(instance_id_str)
        except Exception:
            raise ValueError("Instance id must be an integer.")

    valid_unix_path_regex = re.compile('^(/)?([^/\0]+(/)?)+$')
    # Got this regex from https://stackoverflow.com/questions/537772/what-is-the-most-correct-regular-expression-for-a-unix-file-path
    if (path != "/") and (valid_unix_path_regex.match(path) is None):
        raise ValueError(
            f"Path component: {path} of VRL is not a valid Unix style path."
        )

    return (instance_id, path)


def parse_env(envs: str | None) -> dict[str, str]:
    """Parse the environment variables provided to the docker container.

    Args:
        envs (str | None): String with environment variables: "'-e ASR_MODEL=base'".

    Returns
    -------
        dict[str, str]: The parsed environment variables.
    """
    result: dict[str, str] = {}
    if envs is None:
        return result
    env = envs.split(' ')
    prev = None
    for e in env:
        if prev is None:
            if (e == "-e") or (e == "-p"):
                prev = e
            else:
                return result
        else:
            if prev == "-p":  # type: ignore
                if set(e).issubset(set("0123456789:")):
                    result["-p " + e] = "1"
                else:
                    return result
            elif prev == "-e":
                e = e.strip(" '\"")
                if set(e).issubset(
                    set(
                        "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_="
                    )
                ):
                    kv = e.split('=')
                    result[kv[0]] = kv[1]
                else:
                    return result
            prev = None
    return result


# print(parse_env("-e TYZ=BM3828 -e BOB=UTC -p 10831:22 -p 8080:8080"))


op_names = {
    ">=": "gte",
    ">": "gt",
    "gt": "gt",
    "gte": "gte",
    "<=": "lte",
    "<": "lt",
    "lt": "lt",
    "lte": "lte",
    "!=": "neq",
    "==": "eq",
    "=": "eq",
    "eq": "eq",
    "neq": "neq",
    "noteq": "neq",
    "not eq": "neq",
    "notin": "notin",
    "not in": "notin",
    "nin": "notin",
    "in": "in",
}

field_alias = {
    "cuda_vers": "cuda_max_good",
    "display_active": "gpu_display_active",
    "reliability": "reliability2",
    "dlperf_usd": "dlperf_per_dphtotal",
    "dph": "dph_total",
    "flops_usd": "flops_per_dphtotal",
}

field_multiplier = {
    "cpu_ram": 1000,
    "gpu_ram": 1000,
    "duration": 1.0 / (24.0 * 60.0 * 60.0),
}

fields = {
    "bw_nvlink",
    "compute_cap",
    "cpu_cores",
    "cpu_cores_effective",
    "cpu_ram",
    "cuda_max_good",
    "direct_port_count",
    "driver_version",
    "disk_bw",
    "disk_space",
    "dlperf",
    "dlperf_per_dphtotal",
    "dph_total",
    "duration",
    "external",
    "flops_per_dphtotal",
    "gpu_display_active",
    "gpu_mem_bw",
    "gpu_name",
    "gpu_ram",
    "has_avx",
    "host_id",
    "id",
    "inet_down",
    "inet_down_cost",
    "inet_up",
    "inet_up_cost",
    "machine_id",
    "min_bid",
    "mobo_name",
    "num_gpus",
    "pci_gen",
    "pcie_bw",
    "reliability2",
    "rentable",
    "rented",
    "storage_cost",
    "total_flops",
    "verification",
    "verified",
}

all_fields = [
    "bundle_id",
    "bundled_results",
    "bw_nvlink",
    "compute_cap",
    "cpu_cores",
    "cpu_cores_effective",
    "cpu_name",
    "cpu_ram",
    "cuda_max_good",
    "direct_port_count",
    "disk_bw",
    "disk_name",
    "disk_space",
    "dlperf",
    "dlperf_per_dphtotal",
    "dph_base",
    "dph_total",
    "driver_version",
    "duration",
    "end_date",
    "external",
    "flops_per_dphtotal",
    "geolocation",
    "gpu_display_active",
    "gpu_frac",
    "gpu_lanes",
    "gpu_mem_bw",
    "gpu_name",
    "gpu_ram",
    "has_avx",
    "host_id",
    "hosting_type",
    "id",
    "inet_down",
    "inet_down_billed",
    "inet_down_cost",
    "inet_up",
    "inet_up_billed",
    "inet_up_cost",
    "is_bid",
    "logo",
    "machine_id",
    "min_bid",
    "mobo_name",
    "num_gpus",
    "pci_gen",
    "pcie_bw",
    "pending_count",
    "public_ipaddr",
    "reliability2",
    "rentable",
    "rented",
    "score",
    "start_date",
    "storage_cost",
    "storage_total_cost",
    "total_flops",
    "verification",
    "webpage",
]
