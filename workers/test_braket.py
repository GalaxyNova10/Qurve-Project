from braket.circuits import Circuit
from braket.devices import LocalSimulator

print("BRAKET IMPORT SUCCESS")

device = LocalSimulator()

circuit = Circuit().h(0).cnot(0, 1)

task = device.run(circuit, shots=10)

result = task.result()

print("MEASUREMENTS:")
print(result.measurements)
