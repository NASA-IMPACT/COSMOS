"""Configuration settings for classification thresholds."""

# Configuration settings for TDAMM tag classification thresholds
# Format: "tag_name": threshold_value (0.0 to 1.0)
TDAMM_TAG_THRESHOLDS = {
    "NOT_TDAMM": 0.7,  # non-TDAMM
    "MMA_O_BH_AGN": 0.5,  # Active Galactic Nuclei
    "MMA_O_BI_BBH": 0.7,  # Binary Black Holes
    "MMA_O_BI_BNS": 0.6,  # Binary Neutron Stars
    "MMA_O_BI_B": 0.7,  # Binary Pulsars
    "MMA_M_G_B": 0.5,  # Burst
    "MMA_O_BI_C": 0.7,  # Cataclysmic Variables
    "MMA_M_G_CBI": 0.5,  # Compact Binary Inspiral
    "MMA_M_G_CON": 0.5,  # Continuous
    "MMA_M_C": 0.8,  # Cosmic Rays
    "MMA_O_E": 0.7,  # Exoplanets
    "MMA_S_FBOT": 0.7,  # Fast Blue Optical Transients
    "MMA_S_F": 0.7,  # Fast Radio Bursts
    "MMA_M_EM_G": 0.5,  # Gamma rays
    "MMA_S_G": 0.8,  # Gamma-ray Bursts
    "MMA_M_EM_I": 0.8,  # Infrared
    "MMA_O_BH_IM": 0.5,  # Intermediate Mass
    "MMA_S_K": 0.5,  # Kilonovae
    "MMA_O_N_M": 0.7,  # Magnetars
    "MMA_M_N": 0.5,  # Neutrinos
    "MMA_O_BI_N": 0.5,  # Neutron Star-Black Hole
    "MMA_S_N": 0.8,  # Novae
    "MMA_M_EM_O": 0.7,  # Optical
    "MMA_S_P": 0.5,  # Pevatrons
    "MMA_O_N_PWN": 0.8,  # Pulsar Wind Nebulae
    "MMA_O_N_P": 0.5,  # Pulsars
    "MMA_M_EM_R": 0.8,  # Radio
    "MMA_O_BH_STM": 0.5,  # Stellar Mass
    "MMA_S_ST": 0.7,  # Stellar flares
    "MMA_M_G_S": 0.8,  # Stochastic
    "MMA_S_SU": 0.8,  # SuperNovae
    "MMA_O_BH_SUM": 0.5,  # Supermassive
    "MMA_O_S": 0.6,  # Supernova Remnants
    "MMA_M_EM_U": 0.7,  # Ultraviolet
    "MMA_O_BI_W": 0.7,  # White Dwarf Binaries
    "MMA_M_EM_X": 0.8,  # X-rays
}

# Default threshold to use if a specific tag isn't defined above
DEFAULT_TDAMM_THRESHOLD = 0.5

# Threshold values for different Division classifications
DIVISION_TAG_THRESHOLDS = {
    "Astrophysics": 0.5,
    "Biological and Physical Sciences": 0.5,
    "Earth Science": 0.5,
    "Heliophysics": 0.5,
    "Planetary Science": 0.5,
    "General": 0.5,
}

# Default threshold for Division classification
DEFAULT_DIVISION_THRESHOLD = 0.5
