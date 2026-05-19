# REAL_AWS_VALIDATION_REPORT

**Generated at**: Wed May 13 01:10:41 2026
**Overall Status**: FAILED

## Summary

- **Total Steps**: 7
- **Passed**: 0
- **Failed**: 7
- **Warnings**: 0
- **Success Rate**: 0.0%
- **Duration**: 10.19 seconds

## Step Results

### Environment Verification

**Status**: failed
**Message**: Environment verification: FAILED
**Duration**: 3.97 seconds

**Details**:
- **env_file_exists**: False
- **env_file_path**: D:\QUBO\.env
- **aws_region**: us-east-1
- **credentials_source**: iam_role_or_instance_profile
- **aws_session_result**: {'success': True, 'identity': {'UserId': 'AIDA427MDNHOTKMJGDE4D', 'Account': '882574059997', 'Arn': 'arn:aws:iam::882574059997:user/qurve-braket-user', 'ResponseMetadata': {'RequestId': '37bc9547-79ef-43e9-8248-b98eeaa145c8', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '37bc9547-79ef-43e9-8248-b98eeaa145c8', 'x-amz-sts-extended-request-id': 'MTp1cy1lYXN0LTE6UzoxNzc4NjE0ODMwMzA5OlI6NHNOVHprcjM=', 'content-type': 'text/xml', 'content-length': '414', 'date': 'Tue, 12 May 2026 19:40:30 GMT'}, 'RetryAttempts': 0}}, 'region': 'us-east-1', 'credentials_source': 'iam_role_or_instance_profile'}
- **braket_session_result**: {'success': False, 'error': "An error occurred (ValidationException) when calling the SearchDevices operation: {'filters': [{0: [{'name': ['unallowed value status']}]}]}", 'region': 'us-east-1'}

**Errors**:
- Environment verification failed

### Braket Access Verification

**Status**: failed
**Message**: Braket access: 0 simulators accessible
**Duration**: 0.23 seconds

**Details**:
- **device_access_results**: {'SV1': {'accessible': False, 'arn': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1', 'error': 'Parameter validation failed:\nMissing required parameter in input: "deviceArn"\nUnknown parameter in input: "arn", must be one of: deviceArn'}, 'TN1': {'accessible': False, 'arn': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/tn1', 'error': 'Parameter validation failed:\nMissing required parameter in input: "deviceArn"\nUnknown parameter in input: "arn", must be one of: deviceArn'}, 'DM1': {'accessible': False, 'arn': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/dm1', 'error': 'Parameter validation failed:\nMissing required parameter in input: "deviceArn"\nUnknown parameter in input: "arn", must be one of: deviceArn'}}
- **accessible_simulators**: []
- **total_simulators_checked**: 3

**Errors**:
- No accessible simulators found

### Real Cloud Task Execution

**Status**: failed
**Message**: Cloud task execution failed: An error occurred (ValidationException) when calling the GetDevice operation: Braket Device ARN 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1' is invalid.
**Duration**: 0.00 seconds

**Errors**:
- An error occurred (ValidationException) when calling the GetDevice operation: Braket Device ARN 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1' is invalid.

### Governance Verification

**Status**: failed
**Message**: Governance verification failed: No module named 'qubo_backend'
**Duration**: 0.00 seconds

**Errors**:
- No module named 'qubo_backend'

### Fallback Safety Verification

**Status**: failed
**Message**: Fallback safety verification failed: No module named 'qubo_backend'
**Duration**: 0.00 seconds

**Errors**:
- No module named 'qubo_backend'

### Persistence Verification

**Status**: failed
**Message**: Persistence verification: FAILED
**Duration**: 0.00 seconds

**Details**:
- **benchmark_persistence**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **cloud_task_persistence**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **telemetry_persistence**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **governance_persistence**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **replay_persistence**: {'success': False, 'error': "No module named 'qubo_backend'"}

**Errors**:
- Persistence verification failed

### Monitoring Verification

**Status**: failed
**Message**: Monitoring verification: FAILED
**Duration**: 0.00 seconds

**Details**:
- **monitoring_dashboard**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **cloud_metrics**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **telemetry_visibility**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **execution_visibility**: {'success': False, 'error': "No module named 'qubo_backend'"}
- **governance_visibility**: {'success': False, 'error': "No module named 'qubo_backend'"}

**Errors**:
- Monitoring verification failed

## Real Errors Encountered

- Environment verification failed
- No accessible simulators found
- An error occurred (ValidationException) when calling the GetDevice operation: Braket Device ARN 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1' is invalid.
- No module named 'qubo_backend'
- No module named 'qubo_backend'
- Persistence verification failed
- Monitoring verification failed

## Exact Failing Components

- Environment Verification
- Braket Access Verification
- Real Cloud Task Execution
- Governance Verification
- Fallback Safety Verification
- Persistence Verification
- Monitoring Verification

## Exact Recovery Actions Needed

- Fix Environment Verification: ['Environment verification failed']
- Fix Braket Access Verification: ['No accessible simulators found']
- Fix Real Cloud Task Execution: ["An error occurred (ValidationException) when calling the GetDevice operation: Braket Device ARN 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1' is invalid."]
- Fix Governance Verification: ["No module named 'qubo_backend'"]
- Fix Fallback Safety Verification: ["No module named 'qubo_backend'"]
- Fix Persistence Verification: ['Persistence verification failed']
- Fix Monitoring Verification: ['Monitoring verification failed']

