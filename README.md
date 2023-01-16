# vastai-client

[![Build Status](https://github.com/Barahlush/vastai-client/workflows/test/badge.svg?branch=master&event=push)](https://github.com/Barahlush/vastai-client/actions?query=workflow%3Atest)
[![Python Version](https://img.shields.io/pypi/pyversions/vastai-client.svg)](https://pypi.org/project/vastai-client/)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)

Python client for the Vast.ai cloud rent service. This package provides a Python client, that allows to list, create, destroy GPU instances programmaticaly, using Python.

There is an official Vast.ai [CLI](https://github.com/vast-ai/vast-python), however it can only be used through the command line.


## Installation

```bash
pip install vastai-client
```


## Example

With the package you can list offers and run selected machines:

```python
from vastai_client import VastClient

client = VastClient(api_key=<your_api_key>)
available_machines = client.search_offers(search_query='reliability > 0.98 num_gpus=1 gpu_name=RTX_3090', sort_order='dph-')
print(available_machines)

selected_machine = available_machines[0]
client.create_instance(id=selected_machine.id, image='pytorch/pytorch', ssh=True)
```

For more details, watch documentation.

## License

[MIT](https://github.com/Barahlush/vastai-client/blob/master/LICENSE)


## Credits

This project was generated with [`wemake-python-package`](https://github.com/wemake-services/wemake-python-package). Current template version is: [9899cb192f754a566da703614227e6d63227b933](https://github.com/wemake-services/wemake-python-package/tree/9899cb192f754a566da703614227e6d63227b933). See what is [updated](https://github.com/wemake-services/wemake-python-package/compare/9899cb192f754a566da703614227e6d63227b933...master) since then.
