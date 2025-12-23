"""Device selection utility.

ベンダーごとの最適化は未実装だが、onnxruntime が利用可能ならプロバイダ一覧から
簡易的に NPU/GPU/CPU を推定する。見つからない場合は "auto" を返す。
"""

from __future__ import annotations

from typing import Iterable


def _classify(providers: Iterable[str]) -> str:
    # 優先順: NPU -> GPU -> CPU -> auto
    providers_lower = [p.lower() for p in providers]

    npu_keywords = [
        "qnnexecutionprovider",
        "snpeexecutionprovider",
        "coremlexecutionprovider",
        "vitisexecutionprovider",
        "npu",
        "dmlexecutionprovider",  # DirectML (Windows NPU/accelerator 統合ケース)
    ]
    if any(any(k in p for k in npu_keywords) for p in providers_lower):
        return "NPU"

    gpu_keywords = ["cudaexecutionprovider", "rocexecutionprovider", "dmlexecutionprovider"]
    if any(any(k in p for k in gpu_keywords) for p in providers_lower):
        return "GPU"

    if any("cpuexecutionprovider" in p for p in providers_lower):
        return "CPU"

    return "auto"


def selected_device() -> str:
    try:
        import onnxruntime as ort  # type: ignore

        providers = ort.get_available_providers()
    except Exception:
        return "auto"

    if not providers:
        return "auto"

    return _classify(providers)
