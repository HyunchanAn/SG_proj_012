# Benchmark & E2E Test Report

- **Repository**: SG_proj_012
- **Date**: 2026-07-14 22:44:49

## 1. E2E Testing Summary
❌ **Status**: FAILED

### Test Logs (Snippet)
```text
            "required_processability_level": 3
        }
        res = client.post("/match", json=payload)
>       assert res.status_code == 200
E       assert 404 == 200
E        +  where 404 = <Response [404 Not Found]>.status_code

tests/test_main.py:29: AssertionError
____________________________ test_match_no_results _____________________________

    def test_match_no_results():
        # If required_processability_level is extremely low (e.g. 0), we shouldn't match anything since lowest DB product is 1
        payload = {
            "substrate_id": "sub-123",
            "surface_energy": 32.0,
            "roughness": 600.0,
            "finish_type": "Hairline",
            "required_processability_level": 0
        }
        res = client.post("/match", json=payload)
>       assert res.status_code == 200
E       assert 404 == 200
E        +  where 404 = <Response [404 Not Found]>.status_code

tests/test_main.py:50: AssertionError
=========================== short test summary info ============================
FAILED tests/test_main.py::test_match_successful - assert 404 == 200
FAILED tests/test_main.py::test_match_no_results - assert 404 == 200
============================== 2 failed in 5.00s ===============================

```

## 2. Models Detected
- No pre-trained weights or models detected in this repository.
