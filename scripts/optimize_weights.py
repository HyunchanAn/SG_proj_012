#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

import httpx
from scipy.optimize import minimize
from loguru import logger

# Add src to path so we can import mcda
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.core.mcda import calculate_topsis_scores, MCDA_CONFIG

MODULE_004_URL = os.getenv("MODULE_004_URL", "http://localhost:8004")

def fetch_ground_truth_matches():
    """
    In a real scenario, this would fetch from a database table tracking successful 
    real-world matches (e.g., successful lab tests or field deployments).
    For the sake of this optimizer, we mock a few known "golden" pairs.
    """
    return [
        {
            "query": {"se": 32.0, "rough": 600.0, "proc": 3, "finish": "Hairline"},
            "expected_best_product_code": "PRD-001"
        },
        {
            "query": {"se": 40.0, "rough": 1000.0, "proc": 3, "finish": "2B"},
            "expected_best_product_code": "PRD-002"
        },
        {
            "query": {"se": 35.0, "rough": 800.0, "proc": 3, "finish": "BA"},
            "expected_best_product_code": "PRD-003"
        }
    ]

def fetch_product_catalog():
    """Mock catalog to match the golden pairs."""
    return [
        {"id": "PRD-001", "se": 32.0, "rough": 600.0, "proc": 2, "finish": "Hairline"},
        {"id": "PRD-002", "se": 40.0, "rough": 1000.0, "proc": 3, "finish": "2B"},
        {"id": "PRD-003", "se": 35.0, "rough": 800.0, "proc": 1, "finish": "BA"},
        {"id": "PRD-004", "se": 33.0, "rough": 700.0, "proc": 2, "finish": "Any"}
    ]

def evaluate_weights(weights_array, ground_truth, catalog):
    # weights_array = [w_se, w_rough, w_proc, w_finish]
    # We want to minimize the distance from the top score to the expected product.
    # Alternatively, maximize the number of top-1 matches.
    # Since scipy.minimize needs a continuous differentiable function, we use the 
    # negative of the score of the expected product minus the max score of other products.
    
    # Normalize weights to sum to 1.0
    w_sum = sum(weights_array)
    if w_sum <= 0:
        return 9999.0 # Penalty
        
    w = [val / w_sum for val in weights_array]
    
    # Update global config memory temporarily for calculate_topsis_scores
    MCDA_CONFIG["weights"]["surface_energy"] = w[0]
    MCDA_CONFIG["weights"]["roughness"] = w[1]
    MCDA_CONFIG["weights"]["processability"] = w[2]
    MCDA_CONFIG["weights"]["finish_type"] = w[3]
    
    total_loss = 0.0
    
    for case in ground_truth:
        q = case["query"]
        expected_code = case["expected_best_product_code"]
        
        scored = calculate_topsis_scores(
            req_se=q["se"], req_rough=q["rough"], req_proc=q["proc"], req_finish=q["finish"],
            candidates=catalog
        )
        
        expected_score = 0.0
        max_other_score = 0.0
        
        for c in scored:
            if c["id"] == expected_code:
                expected_score = c["topsis_score"]
            else:
                if c["topsis_score"] > max_other_score:
                    max_other_score = c["topsis_score"]
                    
        # Loss function: we want expected_score > max_other_score + margin
        margin = 5.0
        loss = max(0, max_other_score + margin - expected_score)
        total_loss += loss
        
    return total_loss

def main():
    logger.info("Starting Offline Weight Optimization based on Ground Truth DB...")
    
    ground_truth = fetch_ground_truth_matches()
    catalog = fetch_product_catalog()
    
    # Initial guess
    initial_weights = [0.4, 0.2, 0.2, 0.2]
    
    # Bounds for weights (0 to 1)
    bounds = [(0.01, 1.0), (0.01, 1.0), (0.01, 1.0), (0.01, 1.0)]
    
    res = minimize(
        evaluate_weights, 
        initial_weights, 
        args=(ground_truth, catalog),
        method='L-BFGS-B',
        bounds=bounds
    )
    
    if res.success:
        optimized = res.x / sum(res.x)
        logger.info(f"Optimization Successful!")
        logger.info(f"Optimal Weights -> SE: {optimized[0]:.4f}, Roughness: {optimized[1]:.4f}, Proc: {optimized[2]:.4f}, Finish: {optimized[3]:.4f}")
        
        # Save to config
        config_path = Path(__file__).resolve().parent.parent / "src" / "core" / "config.json"
        with open(config_path, "r") as f:
            cfg = json.load(f)
            
        cfg["weights"]["surface_energy"] = round(optimized[0], 4)
        cfg["weights"]["roughness"] = round(optimized[1], 4)
        cfg["weights"]["processability"] = round(optimized[2], 4)
        cfg["weights"]["finish_type"] = round(optimized[3], 4)
        
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=4)
        logger.info(f"Saved optimized weights to {config_path}")
    else:
        logger.error("Optimization failed.")

if __name__ == "__main__":
    main()
