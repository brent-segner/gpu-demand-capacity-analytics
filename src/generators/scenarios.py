"""
Scenario Configurations for Synthetic Data Generation
======================================================

Each scenario defines parameters that shape the synthetic data
to illustrate different demand-versus-capacity conditions.
"""

from typing import Dict, Any

SCENARIOS: Dict[str, Dict[str, Any]] = {
    'balanced': {
        'description': 'Demand roughly matches capacity. Healthy queue dynamics with moderate utilization.',
        'demand_capacity_ratio': 0.7,
        'base_wait_seconds': 45,
        'active_ratio': 0.75,
        'eviction_rate': 0.01,
        'autoscale_variance': 0.05,
        'workload_profile': 'balanced',
        'high_demand_queues': None,
    },
    
    'demand_exceeds_capacity': {
        'description': 'More workloads submitted than can be scheduled. Growing queues and long wait times.',
        'demand_capacity_ratio': 1.8,
        'base_wait_seconds': 300,
        'active_ratio': 0.95,
        'eviction_rate': 0.05,
        'autoscale_variance': 0.02,
        'workload_profile': 'efficient',
        'high_demand_queues': ['ml-training-h100', 'ml-training-a100'],
    },
    
    'capacity_fragmentation': {
        'description': 'GPUs exist but cannot be effectively scheduled due to fragmentation or constraints.',
        'demand_capacity_ratio': 0.9,
        'base_wait_seconds': 180,
        'active_ratio': 0.45,
        'eviction_rate': 0.08,
        'autoscale_variance': 0.1,
        'workload_profile': 'fragmented',
        'high_demand_queues': None,
    },
    
    'io_bottleneck': {
        'description': 'GPUs report high utilization but low power draw. Data-starved or I/O bound workloads.',
        'demand_capacity_ratio': 0.6,
        'base_wait_seconds': 30,
        'active_ratio': 0.85,
        'eviction_rate': 0.02,
        'autoscale_variance': 0.03,
        'workload_profile': 'bottlenecked',
        'high_demand_queues': None,
    },
}


def get_scenario_config(scenario_name: str) -> Dict[str, Any]:
    """
    Get configuration for a named scenario.
    
    Args:
        scenario_name: One of 'balanced', 'demand_exceeds_capacity', 
                      'capacity_fragmentation', 'io_bottleneck'
                      
    Returns:
        Dictionary of scenario parameters
        
    Raises:
        ValueError: If scenario name is not recognized
    """
    if scenario_name not in SCENARIOS:
        available = ', '.join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{scenario_name}'. Available: {available}")
    
    return SCENARIOS[scenario_name].copy()


def list_scenarios() -> Dict[str, str]:
    """Return a dictionary of scenario names and descriptions."""
    return {name: config['description'] for name, config in SCENARIOS.items()}
