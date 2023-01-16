from dataclasses import dataclass

QueryType = dict[str, bool | str | list[list[str]] | dict[str, str | bool]]


@dataclass
class Instance:

    """Class for storing information about a created instance."""

    actual_status: str | None = None
    bundle_id: int | None = None
    bw_nvlink: float | None = None
    compute_cap: int | None = None
    cpu_cores: int | None = None
    cpu_cores_effective: float | None = None
    cpu_name: str | None = None
    cpu_ram: int | None = None
    cpu_util: float | None = None
    cuda_max_good: float | None = None
    cur_state: str | None = None
    direct_port_count: int | None = None
    direct_port_end: int | None = None
    direct_port_start: int | None = None
    disk_bw: float | None = None
    disk_name: str | None = None
    disk_space: float | None = None
    disk_util: int | None = None
    dlperf: float | None = None
    dlperf_per_dphtotal: float | None = None
    dph_base: float | None = None
    dph_total: float | None = None
    driver_version: str | None = None
    duration: float | None = None
    end_date: str | None = None
    external: bool | None = None
    flops_per_dphtotal: float | None = None
    geolocation: str | None = None
    gpu_display_active: bool | None = None
    gpu_frac: float | None = None
    gpu_lanes: int | None = None
    gpu_mem_bw: float | None = None
    gpu_name: str | None = None
    gpu_ram: int | None = None
    gpu_temp: float | None = None
    gpu_util: float | None = None
    has_avx: int | None = None
    host_id: int | None = None
    hosting_type: int | None = None
    id: int | None = None
    image_args: list[str] | None = None
    image_runtype: str | None = None
    image_uuid: str | None = None
    inet_down: float | None = None
    inet_down_billed: bool | None = None
    inet_down_cost: float | None = None
    inet_up: float | None = None
    inet_up_billed: bool | None = None
    inet_up_cost: float | None = None
    intended_status: str | None = None
    is_bid: bool | None = None
    jupyter_token: str | None = None
    label: str | None = None
    local_ipaddrs: str | None = None
    logo: str | None = None
    machine_dir_ssh_port: int | None = None
    machine_id: int | None = None
    mem_limit: float | None = None
    mem_usage: float | None = None
    min_bid: float | None = None
    mobo_name: str | None = None
    next_state: str | None = None
    num_gpus: int | None = None
    pci_gen: float | None = None
    pcie_bw: float | None = None
    ports: list[int] | None = None
    public_ipaddr: str | None = None
    reliability2: float | None = None
    rentable: bool | None = None
    score: float | None = None
    ssh_host: str | None = None
    ssh_idx: str | None = None
    ssh_port: int | None = None
    start_date: float | None = None
    status_msg: str | None = None
    storage_cost: float | None = None
    storage_total_cost: float | None = None
    total_flops: float | None = None
    verification: str | None = None
    vmem_usage: float | None = None
    webpage: str | None = None


@dataclass
class Machine:

    """Class for storing information about a listed machine."""

    bundle_id: int | None = None
    bundled_results: int | None = None
    bw_nvlink: float | None = None
    compute_cap: int | None = None
    cpu_cores: int | None = None
    cpu_cores_effective: float | None = None
    cpu_name: str | None = None
    cpu_ram: int | None = None
    cuda_max_good: float | None = None
    direct_port_count: int | None = None
    disk_bw: float | None = None
    disk_name: str | None = None
    disk_space: float | None = None
    dlperf: float | None = None
    dlperf_per_dphtotal: float | None = None
    dph_base: float | None = None
    dph_total: float | None = None
    driver_version: str | None = None
    duration: float | None = None
    end_date: float | None = None
    external: bool | None = None
    flops_per_dphtotal: float | None = None
    geolocation: str | None = None
    gpu_display_active: bool | None = None
    gpu_frac: float | None = None
    gpu_lanes: int | None = None
    gpu_mem_bw: float | None = None
    gpu_name: str | None = None
    gpu_ram: int | None = None
    has_avx: int | None = None
    host_id: int | None = None
    hosting_type: int | None = None
    id: int | None = None
    inet_down: float | None = None
    inet_down_billed: float | None = None
    inet_down_cost: float | None = None
    inet_up: float | None = None
    inet_up_billed: float | None = None
    inet_up_cost: float | None = None
    is_bid: bool | None = None
    logo: str | None = None
    machine_id: int | None = None
    min_bid: float | None = None
    mobo_name: str | None = None
    num_gpus: int | None = None
    pci_gen: float | None = None
    pcie_bw: float | None = None
    pending_count: int | None = None
    public_ipaddr: str | None = None
    reliability2: float | None = None
    rented: bool | None = None
    rentable: bool | None = None
    score: float | None = None
    start_date: float | None = None
    storage_cost: float | None = None
    storage_total_cost: float | None = None
    total_flops: float | None = None
    verification: str | None = None
    webpage: str | None = None
