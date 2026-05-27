import torch
import os


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Config:
    def __init__(self, precision="fp32"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.is_half = self.device != "cpu" and precision == "fp16"
        self.gpu_name = (
            torch.cuda.get_device_name(int(self.device.split(":")[-1]))
            if self.device.startswith("cuda")
            else None
        )
        self.precision = precision
        self.gpu_mem = None
        self.x_pad, self.x_query, self.x_center, self.x_max = self.device_config()

    def has_mps(self) -> bool:
        # Check if Metal Performance Shaders are available - for macOS 12.3+.
        return torch.backends.mps.is_available()

    def has_xpu(self) -> bool:
        # Check if XPU is available.
        return hasattr(torch, "xpu") and torch.xpu.is_available()

    def set_precision(self, precision):
        if precision not in ["fp32", "fp16"]:
            raise ValueError("Invalid precision type. Must be 'fp32' or 'fp16'.")
        
        self.precision = precision
        self.is_half = self.device != "cpu" and precision == "fp16"
        
        # Update device config when precision changes
        self.x_pad, self.x_query, self.x_center, self.x_max = self.device_config()
        
        return f"Set precision to {precision}."

    def get_precision(self):
        return self.precision

    def device_config(self) -> tuple:
        if self.device.startswith("cuda"):
            self.set_cuda_config()
        elif self.has_mps():
            self.device = "mps"
            self.is_half = False
            self.precision = "fp32"
        else:
            self.device = "cpu"
            self.is_half = False
            self.precision = "fp32"

        # Configuration based on precision
        if self.precision == "fp16":
            x_pad, x_query, x_center, x_max = (3, 10, 60, 65)
        else:  # fp32
            x_pad, x_query, x_center, x_max = (1, 6, 38, 41)
        
        # Adjust for low GPU memory if applicable
        if self.gpu_mem is not None and self.gpu_mem <= 4:
            x_pad, x_query, x_center, x_max = (1, 5, 30, 32)

        return x_pad, x_query, x_center, x_max

    def set_cuda_config(self):
        i_device = int(self.device.split(":")[-1])
        self.gpu_name = torch.cuda.get_device_name(i_device)
        
        # Zluda detection
        if self.gpu_name and self.gpu_name.endswith("[ZLUDA]"):
            print("Zluda compatibility enabled, experimental feature.")
            torch.backends.cudnn.enabled = False
            torch.backends.cuda.enable_flash_sdp(False)
            torch.backends.cuda.enable_math_sdp(True)
            torch.backends.cuda.enable_mem_efficient_sdp(False)
        
        # Low-end GPU detection
        low_end_gpus = ["16", "P40", "P10", "1060", "1070", "1080"]
        if self.gpu_name and any(gpu in self.gpu_name for gpu in low_end_gpus):
            # Estimate GPU memory for low-end GPUs (you might want to set this explicitly)
            self.gpu_mem = 4  # Assume 4GB for low-end GPUs
