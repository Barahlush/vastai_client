#!/usr/bin/env python3

from __future__ import print_function, unicode_literals

import json
import os
import sys
import time
from dataclasses import asdict
from dacite import from_dict


import requests
from loguru import logger
from vastai_client.models import Instance, Machine, QueryType
from vastai_client.vast_utils import parse_env, parse_query, parse_vast_url

try:
    from urllib import quote_plus  # type: ignore # Python 2.X
except ImportError:
    from urllib.parse import quote_plus  # Python 3+

try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError  # type: ignore

try:
    input = raw_input  # type: ignore
except NameError:
    pass


# server_url_default = "https://vast.ai"
server_url_default = "https://console.vast.ai"
# server_url_default  = "https://vast.ai/api/v0"
api_key_file_base = "~/.vast_api_key"
api_key_file = os.path.expanduser(api_key_file_base)


class VastClient:

    """Python client for Vast.ai API."""

    def __init__(
        self,
        api_key: str | None = None,
        url: str = server_url_default,
        api_key_file: str = api_key_file,
    ):
        """VastClient constructor.
        Args:
            api_key (str | None, optional): api key. Defaults to None.
            url (str, optional): server REST api url. Defaults to server_url_default.
            api_key_file (str, optional): file where api key is stored. Defaults to api_key_file_base.

        Raises
        ------
            ValueError: Must provide `api_key` or `api_key_file_base` where the key is stored.
        """
        self.url = url
        if api_key is None and not os.path.exists(api_key_file):
            raise ValueError(
                "Must provide `api_key` or `api_key_file_base` where the key is stored."
            )
        elif api_key:
            self.api_key = api_key
        else:
            with open(api_key_file, 'r') as f:
                self.api_key = f.read().strip()

    def apiurl(
        self,
        subpath: str,
        query_args: dict[str, str | QueryType] | None = None,
    ) -> str:
        """Creates the endpoint URL for a given combination of parameters.

        :param str subpath: added to end of URL to further specify endpoint.
        :param typing.Dict query_args: specifics such as API key and search parameters that complete the URL.
        :rtype str:
        """
        if query_args is None:
            query_args = {}

        query_args["api_key"] = self.api_key

        if query_args:
            return (
                self.url
                + "/api/v0"
                + subpath
                + "?"
                + "&".join(
                    "{x}={y}".format(
                        x=x, y=quote_plus(y if isinstance(y, str) else json.dumps(y))
                    )
                    for x, y in query_args.items()
                )
            )
        else:
            return self.url + "/api/v0" + subpath

    def copy(self, src: str, dst: str, identity: str | None = None) -> None:
        """Copy directories between instances and/or local..

        Args:
        ----
        src (str): instance_id:/path to source of object to copy.
        dst (str): instance_id:/path to target of copy operation.
        identity (str | None, optional):  Location of ssh private key. Optional.
        """
        url = self.apiurl('/commands/rsync/')
        src_id, src_path = parse_vast_url(src)
        dst_id, dst_path = parse_vast_url(dst)
        logger.info(f'copying {src_id}:{src_path} {dst_id}:{dst_path}')
        req_json = {
            'client_id': 'me',
            'src_id': src_id,
            'dst_id': dst_id,
            'src_path': src_path,
            'dst_path': dst_path,
        }
        r = requests.put(url, json=req_json, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            if rj['success']:
                logger.info(
                    'Remote to Remote copy initiated - check instance status bar for progress updates (~30 seconds delayed).'
                )
            else:
                logger.error(rj['msg'])
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))

    def search_offers(
        self,
        type: str = 'on-demand',
        search_query: str = 'external=false rentable=true verified=true',
        sort_order: str = 'score-',
        no_default: bool = False,
        disable_bundling: bool = False,
        storage: float = 5.0,
    ) -> list[Machine]:
        """Search for instance types using custom query.

        Query syntax:

            query = comparison comparison...
            comparison = field op value
            field = <name of a field>
            op = one of: <, <=, ==, !=, >=, >, in, notin
            value = <bool, int, float, etc> | 'any'

        note: to pass '>' and '<' on the command line, make sure to use quotes
        note: to encode a string query value (ie for gpu_name), replace any spaces ' ' with underscore '_'


        Examples
        --------
            ./vast search offers 'compute_cap > 610 total_flops < 5'
            ./vast search offers 'reliability > 0.99  num_gpus>=4' -o 'num_gpus-'
            ./vast search offers 'rentable = any'
            ./vast search offers 'reliability > 0.98 num_gpus=1 gpu_name=RTX_3090'

        Available fields:

              Name                  Type       Description

            bw_nvlink               float     bandwidth NVLink
            compute_cap:            int       cuda compute capability*100  (ie:  650 for 6.5, 700 for 7.0)
            cpu_cores:              int       # virtual cpus
            cpu_cores_effective:    float     # virtual cpus you get
            cpu_ram:                float     system RAM in gigabytes
            cuda_vers:              float     cuda version
            direct_port_count       int       open ports on host's router
            disk_bw:                float     disk read bandwidth, in MB/s
            disk_space:             float     disk storage space, in GB
            dlperf:                 float     DL-perf score  (see FAQ for explanation)
            dlperf_usd:             float     DL-perf/$
            dph:                    float     $/hour rental cost
            driver_version          string    driver version in use on a host.
            duration:               float     max rental duration in days
            external:               bool      show external offers
            flops_usd:              float     TFLOPs/$
            gpu_mem_bw:             float     GPU memory bandwidth in GB/s
            gpu_name:               string    GPU model name (no quotes, replace spaces with underscores, ie: RTX_3090 rather than 'RTX 3090')
            gpu_ram:                float     GPU RAM in GB
            gpu_frac:               float     Ratio of GPUs in the offer to gpus in the system
            has_avx:                bool      CPU supports AVX instruction set.
            id:                     int       instance unique ID
            inet_down:              float     internet download speed in Mb/s
            inet_down_cost:         float     internet download bandwidth cost in $/GB
            inet_up:                float     internet upload speed in Mb/s
            inet_up_cost:           float     internet upload bandwidth cost in $/GB
            machine_id              int       machine id of instance
            min_bid:                float     current minimum bid price in $/hr for interruptible
            num_gpus:               int       # of GPUs
            pci_gen:                float     PCIE generation
            pcie_bw:                float     PCIE bandwidth (CPU to GPU)
            reliability:            float     machine reliability score (see FAQ for explanation)
            rentable:               bool      is the instance currently rentable
            rented:                 bool      is the instance currently rented
            storage_cost:           float     storage cost in $/GB/month
            total_flops:            float     total TFLOPs from all GPUs
            verified:               bool      is the machine verified

        Args:
        ----
        type (str): Show 'bid'(interruptible) or 'on-demand' offers. (default: on-demand).
        search_query (str): Query to search for. default: 'external=false rentable=true verified=true'.
        sort_order (str): Comma-separated list of fields to sort on. postfix field with - to sort desc. ex: -o 'num_gpus,total_flops-'. (default: score-).
        no_default (bool): Disable default query. (default: False)
        disable_bundling (bool): Show identical offers. This request is more heavily rate limited. (default: False)
        storage (float): Amount of storage to use for pricing, in GiB. default=5.0GiB (default: 5.0).
        """
        field_alias = {
            'cuda_vers': 'cuda_max_good',
            'reliability': 'reliability2',
            'dlperf_usd': 'dlperf_per_dphtotal',
            'dph': 'dph_total',
            'flops_usd': 'flops_per_dphtotal',
        }
        try:
            if no_default:
                query: QueryType = {}
            else:
                query = {
                    'verified': {'eq': True},
                    'external': {'eq': False},
                    'rentable': {'eq': True},
                }
            if search_query is not None:
                query = parse_query(search_query, query)
            order: list[list[str]] = []
            for name in sort_order.split(','):
                name = name.strip()
                if not name:
                    continue
                direction = 'asc'
                if name.strip('-') != name:
                    direction = 'desc'
                field = name.strip('-')
                if field in field_alias:
                    field = field_alias[field]
                order.append([field, direction])
            query['order'] = order
            query['type'] = type
            if query['type'] == 'interruptible':
                query['type'] = 'bid'
            if disable_bundling:
                query['disable_bundling'] = True
        except ValueError as e:
            logger.error('Error: ', e)
            raise e
        url = self.apiurl('/bundles', {'q': query})
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        rows = r.json()['offers']
        return [from_dict(data_class=Machine, data=row) for row in rows]

    def get_instances(self) -> list[Instance]:
        """Display user's current instances."""
        req_url = self.apiurl('/instances', {'owner': 'me'})
        r = requests.get(req_url, timeout=10)
        r.raise_for_status()
        rows = r.json()['instances']
        return [from_dict(data_class=Instance, data=row) for row in rows]

    def ssh_url(self, instance_id: int) -> str | None:
        """ssh url helper.

        Args:
        ----
        instance_id (int): id of instance.
        """
        return self.get_ssh_url(instance_id, 'ssh://')

    def scp_url(self, instance_id: int) -> str | None:
        """scp url helper.

        Args:
        ----
        instance_id (int): id of instance.
        """
        return self.get_ssh_url(instance_id, 'scp://')

    def get_ssh_url(self, instance_id: int, protocol: str) -> str | None:
        """Creates an ssh url for the given instance.

        Args:
        instance_id (int): id of the instance.
        protocol (str): `ssh://` or `scp://` .

        Returns
        -------
            str | None: constructed ssh url.
        """
        req_url = self.apiurl("/instances", {"owner": "me"})
        r = requests.get(req_url, timeout=10)
        r.raise_for_status()
        rows = r.json()["instances"]
        if instance_id:
            (instance,) = [r for r in rows if r['id'] == instance_id]
        elif len(rows) > 1:
            logger.error("Found multiple running instances")
            return None
        else:
            (instance,) = rows
        return f'{protocol}root@{instance["ssh_host"]}:{instance["ssh_port"]}'

    def get_hosted_machines(self, quiet: bool) -> list[Machine]:
        """[Host] Returns hosted machines
        Args:
            quiet (bool): only display numeric ids.
        """
        req_url = self.apiurl('/machines', {'owner': 'me'})
        r = requests.get(req_url, timeout=10)
        r.raise_for_status()
        rows = r.json()['machines']
        return [from_dict(data_class=Machine, data=row) for row in rows]

    def show_hosted_machines(self, quiet: bool, raw: bool) -> None:
        """[Host] Show hosted machines.

        Args:
        ----
        quiet (bool): only display numeric ids.
        raw (bool): print raw json.
        """
        machines = self.get_hosted_machines(quiet)
        rows = [asdict(machine) for machine in machines]
        if raw:
            logger.info(json.dumps(rows, indent=1, sort_keys=True))
        else:
            for machine in rows:
                if quiet:
                    logger.info('{id}'.format(id=machine['id']))
                else:
                    logger.info('{N} machines: '.format(N=len(rows)))
                    logger.info(
                        '{id}: {json}'.format(
                            id=machine['id'],
                            json=json.dumps(machine, indent=4, sort_keys=True),
                        )
                    )

    def reboot_instance(self, id: int) -> bool:
        """Reboot (stop/start) an instance
        Args:
            id (int): id of instance to reboot.

        Returns
        -------
            bool: True if successful, False otherwise.
        """
        url = self.apiurl('/instances/reboot/{id}/'.format(id=id))
        r = requests.put(url, json={}, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            if rj['success']:
                logger.info('Rebooting instance {id}.'.format(**locals()))
                return True
            else:
                logger.error(rj['msg'])
                return False
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))
            return False

    def start_instance(self, id: int) -> bool:
        """Start a stopped instance
        Args:
            id (int): id of instance to start/restart.

        Returns
        -------
            bool: True if successful, False otherwise.
        """
        url = self.apiurl('/instances/{id}/'.format(id=id))
        r = requests.put(url, json={'state': 'running'}, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            if rj['success']:
                logger.info('starting instance {id}.'.format(**locals()))
                return True
            else:
                logger.error(rj['msg'])
                return False
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))
            return False

    def stop_instance(self, id: int) -> bool:
        """Stop a running instance
        Args:
            id (int): id of instance to stop.

        Returns
        -------
            bool: True if successful, False otherwise.
        """
        url = self.apiurl('/instances/{id}/'.format(id=id))
        r = requests.put(url, json={'state': 'stopped'}, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            if rj['success']:
                logger.info('stopping instance {id}.'.format(**locals()))
                return True
            else:
                logger.error(rj['msg'])
                return False
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))
            return False

    def label_instance(self, id: int, label: str) -> bool:
        """Assign a string label to an instance.

        Args:
            id (int): id of instance to label.
            label (str): label to set.

        Returns
        -------
            bool: True if successful, False otherwise.
        """
        url = self.apiurl('/instances/{id}/'.format(id=id))
        r = requests.put(url, json={'label': label}, timeout=10)
        r.raise_for_status()
        rj = r.json()
        if rj['success']:
            logger.info('label for {id} set to {label}.'.format(**locals()))
            return True
        else:
            logger.error(rj['msg'])
            return False

    def destroy_instance(self, id: int) -> bool:
        """Destroy an instance (irreversible, deletes data).

        Args:
            id (int): id of instance to delete.

        Returns
        -------
            bool: True if successful, False otherwise.
        """
        url = self.apiurl('/instances/{id}/'.format(id=id))
        r = requests.delete(url, json={}, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            if rj['success']:
                logger.info('destroying instance {id}.'.format(**locals()))
                return True
            else:
                logger.error(rj['msg'])
                return False
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))
            return False

    def execute(self, ID: int, COMMAND: str) -> bool:
        """Execute a (constrained) remote command on a machine.

        Args:
        ----
        ID (int): id of instance to execute on.
        COMMAND (str): command to execute.
        """
        url = self.apiurl('/instances/command/{id}/'.format(id=ID))
        r = requests.put(url, json={'command': COMMAND}, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            if rj['success']:
                logger.info('Executing {command} on instance {id}.'.format(**locals()))
                return True
            else:
                logger.error(rj['msg'])
                return False
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))
            return False

    def logs(self, INSTANCE_ID: int, tail: str) -> bool:
        """Get the logs for an instance.

        Args:
        ----
        INSTANCE_ID (int): id of instance.
        tail (str): Number of lines to show from the end of the logs (default '1000').
        """
        url = self.apiurl('/instances/request_logs/{id}/'.format(id=INSTANCE_ID))
        json = {}
        if tail:
            json['tail'] = tail
        r = requests.put(url, json=json, timeout=10)
        r.raise_for_status()
        if r.status_code == 200:
            rj = r.json()
            for i in range(0, 30):
                time.sleep(1)
                url = (
                    self.url + '/static/docker_logs/C' + str(INSTANCE_ID & 255) + '.log'
                )
                logger.info(f'waiting on logs for instance {INSTANCE_ID}')
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    logger.info(r.text)
                    return True
            else:
                logger.error(rj['msg'])
                return False
        else:
            logger.error(r.text)
            logger.error('failed with error {r.status_code}'.format(**locals()))
            return False

    def create_instance(
        self,
        id: int,
        image: str,
        price: float | None = None,
        login: str | None = None,
        label: str | None = None,
        onstart: str | None = None,
        onstart_cmd: str | None = None,
        ssh: bool | None = None,
        jupyter: bool | None = None,
        direct: bool | None = None,
        jupyter_dir: str | None = None,
        jupyter_lab: bool | None = None,
        lang_utf8: bool | None = None,
        python_utf8: bool | None = None,
        env: str | None = None,
        args: list[str] | None = None,
        create_from: str | None = None,
        force: bool | None = None,
        disk: float = 10,
    ) -> str | None:
        """Creates a new instance.

        Args:
        ----
        id (int): id of instance type to launch.
        image (str): docker container image to launch.
        price (float): per machine bid price in $/hour.
        disk (float): size of local disk partition in GB (default: 10).
        login (str): docker login arguments for private repo authentication, surround with '' .
        label (str): label to set on the instance.
        onstart (str): filename to use as onstart script.
        onstart_cmd (str): contents of onstart script as single argument.
        ssh (bool): Launch as an ssh instance type.
        jupyter (bool): Launch as a jupyter instance instead of an ssh instance.
        direct (bool): Use (faster) direct connections for jupyter & ssh.
        jupyter_dir (str): For runtype 'jupyter', directory in instance to use to launch jupyter. Defaults to image's working directory.
        jupyter_lab (bool): For runtype 'jupyter', Launch instance with jupyter lab.
        lang_utf8 (bool): Workaround for images with locale problems: install and generate locales before instance launch, and set locale to C.UTF-8.
        python_utf8 (bool): Workaround for images with locale problems: set python's locale to C.UTF-8.
        env (str): env variables and port mapping options, surround with '' .
        args (list[str]): list of arguments passed to container ENTRYPOINT. Onstart is recommended for this purpose.
        create_from (str): Existing instance id to use as basis for new instance. Instance configuration should usually be identical, as only the difference from the base image is copied.
        force (bool): Skip sanity checks when creating from an existing instance.
        """
        if onstart:
            with open(onstart, 'r') as reader:
                onstart_cmd = reader.read()
        runtype = 'ssh'
        if args:
            runtype = 'args'
        if jupyter_dir or jupyter_lab:
            jupyter = True
        if jupyter and runtype == 'args':
            logger.error(
                "Error: Can't use 'jupyter' and 'args' together. Try 'onstart' or 'onstart_cmd' instead of 'args'.",
                file=sys.stderr,
            )
            return None
        if jupyter:
            runtype = (
                'jupyter_direc ssh_direct ssh_proxy'
                if direct
                else 'jupyter_proxy ssh_proxy'
            )
        if ssh:
            runtype = 'ssh_direct ssh_proxy' if direct else 'ssh_proxy'
        url = self.apiurl('/asks/{id}/'.format(id=id))
        r = requests.put(
            url,
            json={
                'client_id': 'me',
                'image': image,
                'args': args,
                'env': parse_env(env),
                'price': price,
                'disk': disk,
                'label': label,
                'onstart': onstart_cmd,
                'runtype': runtype,
                'image_login': login,
                'python_utf8': python_utf8,
                'lang_utf8': lang_utf8,
                'use_jupyter_lab': jupyter_lab,
                'jupyter_dir': jupyter_dir,
                'create_from': create_from,
                'force': force,
            },
            timeout=10,
        )
        r.raise_for_status()
        logger.info('Started. {}'.format(r.json()))

        return str(r.json())

    def change_bid(self, id: int, price: float) -> None:
        """Change the bid price for a spot/interruptible instance.

        Args:
        ----
        id (int): id of instance type to change bid.
        price (float): per machine bid price in $/hour.
        """
        url = self.apiurl('/instances/bid_price/{id}/'.format(id=id))
        logger.info(f'URL: {url}')
        r = requests.put(url, json={'client_id': 'me', 'price': price}, timeout=10)
        r.raise_for_status()
        logger.info('Per gpu bid price changed: {}'.format(r.json()))

    def reset_api_key(self) -> None:
        """Reset your api-key (get new key from website)."""
        logger.info('fml')
        url = self.apiurl('/commands/reset_apikey/')
        r = requests.put(url, json={'client_id': 'me'}, timeout=10)
        r.raise_for_status()
        logger.info('api-key reset {}'.format(r.json()))

    def set_api_key(self, new_api_key: str) -> None:
        """Set api-key (get your api-key from the console/CLI).

        Args:
        ----
        new_api_key (str): Api key to set as currently logged in user.
        """
        with open(api_key_file, 'w') as writer:
            writer.write(new_api_key)
        logger.info('Your api key has been saved in {}'.format(api_key_file))
