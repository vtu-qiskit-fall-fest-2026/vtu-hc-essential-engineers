"""Hour-0 check: can this account run dynamic circuits and mid-circuit measurement?

Put your API key in .env (IBM_QUANTUM_TOKEN=...; gitignored, never commit it),
or save it with QiskitRuntimeService.save_account().
"""

from nirikshak.hardware import DEFAULT_BACKEND, get_service

service = get_service()
dynamic = [b.name for b in service.backends(dynamic_circuits=True)]
mcm = [b.name for b in service.backends(filters=lambda b: "measure_2" in b.supported_instructions)]

print("Dynamic-circuit backends:     ", dynamic)
print("measure_2 (MidCircuitMeasure):", mcm)
print(f"{DEFAULT_BACKEND}: dynamic={DEFAULT_BACKEND in dynamic}, measure_2={DEFAULT_BACKEND in mcm}")
