"""
Chemical toxicity and classification data.
Based on EPA toxicity categories and California DPR classifications.

EPA Toxicity Categories:
- Category I: Highly toxic (DANGER-POISON)
- Category II: Moderately toxic (WARNING)
- Category III: Slightly toxic (CAUTION)
- Category IV: Practically non-toxic (CAUTION)

Signal Words indicate acute toxicity level.
"""

# Common pesticides with toxicity info
# This is a subset - full database would be loaded from EPA/DPR files
CHEMICAL_INFO = {
    # Glyphosate and salts
    1855: {
        "name": "GLYPHOSATE, ISOPROPYLAMINE SALT",
        "cas_number": "38641-94-0",
        "chemical_class": "Organophosphorus",
        "type": "Herbicide",
        "epa_toxicity_category": "III",
        "signal_word": "CAUTION",
        "carcinogen": "Group 2A (IARC) - Probably carcinogenic",
        "endocrine_disruptor": "Under review",
        "groundwater_contaminant": False,
        "restricted_use": False,
        "notes": "Most widely used herbicide globally. Subject to ongoing health debates."
    },
    2289: {
        "name": "ISOXABEN",
        "cas_number": "82558-50-7",
        "chemical_class": "Benzamide",
        "type": "Herbicide",
        "epa_toxicity_category": "III",
        "signal_word": "CAUTION",
        "carcinogen": "Not likely",
        "endocrine_disruptor": "No",
        "groundwater_contaminant": False,
        "restricted_use": False,
        "notes": "Pre-emergent herbicide for broadleaf weeds."
    },

    # Chlorpyrifos
    253: {
        "name": "CHLORPYRIFOS",
        "cas_number": "2921-88-2",
        "chemical_class": "Organophosphate",
        "type": "Insecticide",
        "epa_toxicity_category": "II",
        "signal_word": "WARNING",
        "carcinogen": "Not classifiable",
        "endocrine_disruptor": "Yes - thyroid",
        "groundwater_contaminant": False,
        "restricted_use": True,
        "neurotoxic": True,
        "notes": "Banned for food uses in CA (2020). Linked to developmental neurotoxicity."
    },

    # Sulfur
    742: {
        "name": "SULFUR",
        "cas_number": "7704-34-9",
        "chemical_class": "Inorganic",
        "type": "Fungicide/Acaricide",
        "epa_toxicity_category": "III",
        "signal_word": "CAUTION",
        "carcinogen": "No",
        "endocrine_disruptor": "No",
        "groundwater_contaminant": False,
        "restricted_use": False,
        "organic_approved": True,
        "notes": "One of oldest pesticides. Approved for organic farming."
    },

    # 1,3-Dichloropropene
    186: {
        "name": "1,3-DICHLOROPROPENE",
        "cas_number": "542-75-6",
        "chemical_class": "Halogenated hydrocarbon",
        "type": "Fumigant/Nematicide",
        "epa_toxicity_category": "I",
        "signal_word": "DANGER",
        "carcinogen": "Likely carcinogen (EPA)",
        "endocrine_disruptor": "Under review",
        "groundwater_contaminant": True,
        "restricted_use": True,
        "volatile": True,
        "notes": "Soil fumigant. Strict buffer zones required. Air quality concerns."
    },

    # Methyl bromide
    359: {
        "name": "METHYL BROMIDE",
        "cas_number": "74-83-9",
        "chemical_class": "Halogenated hydrocarbon",
        "type": "Fumigant",
        "epa_toxicity_category": "I",
        "signal_word": "DANGER-POISON",
        "carcinogen": "Not classifiable",
        "endocrine_disruptor": "No",
        "groundwater_contaminant": False,
        "restricted_use": True,
        "ozone_depleting": True,
        "notes": "Being phased out under Montreal Protocol. Critical use exemptions only."
    },

    # Imidacloprid (neonicotinoid)
    2581: {
        "name": "IMIDACLOPRID",
        "cas_number": "138261-41-3",
        "chemical_class": "Neonicotinoid",
        "type": "Insecticide",
        "epa_toxicity_category": "II",
        "signal_word": "WARNING",
        "carcinogen": "Not likely",
        "endocrine_disruptor": "Under review",
        "groundwater_contaminant": True,
        "restricted_use": False,
        "bee_toxic": True,
        "notes": "Neonicotinoid linked to bee colony collapse. Restricted in EU."
    },

    # Paraquat
    447: {
        "name": "PARAQUAT DICHLORIDE",
        "cas_number": "1910-42-5",
        "chemical_class": "Bipyridylium",
        "type": "Herbicide",
        "epa_toxicity_category": "I",
        "signal_word": "DANGER-POISON",
        "carcinogen": "Not classifiable",
        "endocrine_disruptor": "No",
        "groundwater_contaminant": False,
        "restricted_use": True,
        "highly_toxic_oral": True,
        "notes": "No antidote for poisoning. Certified applicator only. Linked to Parkinson's."
    },

    # Copper sulfate
    104: {
        "name": "COPPER SULFATE (PENTAHYDRATE)",
        "cas_number": "7758-99-8",
        "chemical_class": "Inorganic copper",
        "type": "Fungicide/Algaecide",
        "epa_toxicity_category": "II",
        "signal_word": "WARNING",
        "carcinogen": "No",
        "endocrine_disruptor": "No",
        "groundwater_contaminant": False,
        "restricted_use": False,
        "organic_approved": True,
        "notes": "Common fungicide. Can accumulate in soil with repeated use."
    },

    # Malathion
    367: {
        "name": "MALATHION",
        "cas_number": "121-75-5",
        "chemical_class": "Organophosphate",
        "type": "Insecticide",
        "epa_toxicity_category": "III",
        "signal_word": "CAUTION",
        "carcinogen": "Suggestive evidence (EPA)",
        "endocrine_disruptor": "Under review",
        "groundwater_contaminant": False,
        "restricted_use": False,
        "notes": "Used in mosquito control programs. Less toxic than other OPs."
    },

    # Bacillus thuringiensis
    200: {
        "name": "BACILLUS THURINGIENSIS (BT)",
        "cas_number": "68038-71-1",
        "chemical_class": "Microbial",
        "type": "Insecticide",
        "epa_toxicity_category": "IV",
        "signal_word": "CAUTION",
        "carcinogen": "No",
        "endocrine_disruptor": "No",
        "groundwater_contaminant": False,
        "restricted_use": False,
        "organic_approved": True,
        "notes": "Biological pesticide. Very low mammalian toxicity."
    }
}

# EPA Toxicity Category descriptions
EPA_TOXICITY_CATEGORIES = {
    "I": {
        "description": "Highly Toxic",
        "signal_word": "DANGER or DANGER-POISON",
        "oral_ld50": "Up to 50 mg/kg",
        "dermal_ld50": "Up to 200 mg/kg",
        "eye_effects": "Corrosive, corneal opacity irreversible",
        "skin_effects": "Corrosive"
    },
    "II": {
        "description": "Moderately Toxic",
        "signal_word": "WARNING",
        "oral_ld50": "50-500 mg/kg",
        "dermal_ld50": "200-2000 mg/kg",
        "eye_effects": "Corneal opacity reversible in 7 days",
        "skin_effects": "Severe irritation at 72 hours"
    },
    "III": {
        "description": "Slightly Toxic",
        "signal_word": "CAUTION",
        "oral_ld50": "500-5000 mg/kg",
        "dermal_ld50": "2000-20000 mg/kg",
        "eye_effects": "No corneal opacity, irritation reversible",
        "skin_effects": "Moderate irritation at 72 hours"
    },
    "IV": {
        "description": "Practically Non-Toxic",
        "signal_word": "CAUTION (optional)",
        "oral_ld50": ">5000 mg/kg",
        "dermal_ld50": ">20000 mg/kg",
        "eye_effects": "No irritation",
        "skin_effects": "Mild or no irritation"
    }
}

# Chemical classes and their characteristics
CHEMICAL_CLASSES = {
    "Organophosphate": {
        "description": "Inhibit acetylcholinesterase enzyme",
        "concerns": ["Neurotoxicity", "Acute poisoning risk", "Environmental persistence varies"],
        "examples": ["Chlorpyrifos", "Malathion", "Diazinon"]
    },
    "Neonicotinoid": {
        "description": "Systemic insecticides affecting nicotinic acetylcholine receptors",
        "concerns": ["Bee toxicity", "Groundwater contamination", "Persistence in soil"],
        "examples": ["Imidacloprid", "Clothianidin", "Thiamethoxam"]
    },
    "Organochlorine": {
        "description": "Chlorinated hydrocarbons (mostly banned)",
        "concerns": ["Bioaccumulation", "Environmental persistence", "Endocrine disruption"],
        "examples": ["DDT (banned)", "Endosulfan"]
    },
    "Pyrethroid": {
        "description": "Synthetic versions of natural pyrethrins",
        "concerns": ["Aquatic toxicity", "Bee toxicity"],
        "examples": ["Permethrin", "Bifenthrin", "Cypermethrin"]
    },
    "Carbamate": {
        "description": "Inhibit acetylcholinesterase (reversible)",
        "concerns": ["Acute toxicity", "Less persistent than OPs"],
        "examples": ["Carbaryl", "Methomyl", "Aldicarb"]
    }
}

def get_chemical_info(chem_code: int) -> dict:
    """Get toxicity info for a chemical code."""
    return CHEMICAL_INFO.get(chem_code)

def get_toxicity_category_info(category: str) -> dict:
    """Get description of EPA toxicity category."""
    return EPA_TOXICITY_CATEGORIES.get(category)

def get_chemical_class_info(class_name: str) -> dict:
    """Get info about a chemical class."""
    return CHEMICAL_CLASSES.get(class_name)
