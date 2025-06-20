import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class WastewaterTreatmentSimulation:
    def __init__(self, plan: int = 1):
        """
        Initialize the wastewater treatment simulation for either Plan 1 or Plan 2.
        
        Args:
            plan: 1 or 2, indicating which treatment plan to simulate
        """
        self.plan = plan
        self.flow_rate = 200  # m³/day
        self.hourly_flow = self.flow_rate / 24  # m³/hour
        
        # Initialize raw wastewater concentrations (mg/L unless otherwise noted)
        self.raw_wastewater = {
            'pH': 7.5,  # assumed initial pH
            'TSS': 47.6 if plan == 1 else 47.57,
            'TDS': 669,
            'COD': 1552,
            'BOD': 1025 if plan == 1 else 536,
            'Conductivity': 1214.4,  # µS/cm
            'Turbidity': 345,  # NTU
            'Alkalinity': 151.3,  # as CaCO₃
            'Total Nitrates': 28.2 if plan == 1 else 26.8,  # NO₃⁻
            'Total Phosphates': 96.6,
            'Total Color': 11423.3 if plan == 1 else 10852.1,  # HU
            'Total Zinc': 5.0  # assumed initial concentration (mg/L)
        }
        
        # Recommended effluent limits
        self.effluent_limits = {
            'TSS': 20,
            'TDS': 500,
            'COD': 150,
            'BOD': 30,
            'Conductivity': 1000,
            'Turbidity': 5,
            'Alkalinity': (50, 150),  # range
            'Total Nitrates': 10,
            'Total Phosphates': 5,
            'Total Color': 50,
            'Total Zinc': 2.0  # assumed limit
        }
        
        # Initialize treatment units
        self.treatment_units = self._initialize_treatment_units()
        
        # Track concentrations through each stage
        self.concentration_history = []
        
    def _initialize_treatment_units(self) -> List[Dict]:
        """Initialize the treatment units based on the selected plan."""
        if self.plan == 1:
            return [
                {'name': 'Fine Screen', 'function': self.fine_screen},
                {'name': 'Plain Sedimentation', 'function': self.plain_sedimentation},
                {'name': 'Electrocoagulation', 'function': self.electrocoagulation},
                {'name': 'Rapid Sand Filter', 'function': self.rapid_sand_filter}
            ]
        else:
            return [
                {'name': 'Fine Screen', 'function': self.fine_screen},
                {'name': 'Coagulation Tank', 'function': self.coagulation_tank},
                {'name': 'Flocculation Chamber', 'function': self.flocculation_chamber},
                {'name': 'Sedimentation', 'function': self.sedimentation},
                {'name': 'Electrocoagulation', 'function': self.electrocoagulation},
                {'name': 'Rapid Sand Filter', 'function': self.rapid_sand_filter}
            ]
    
    def run_simulation(self) -> Dict[str, Dict[str, float]]:
        """Run the complete treatment simulation and return the results."""
        current_concentrations = self.raw_wastewater.copy()
        self.concentration_history = [('Raw Wastewater', current_concentrations.copy())]
        
        for unit in self.treatment_units:
            current_concentrations = unit['function'](current_concentrations)
            self.concentration_history.append((unit['name'], current_concentrations.copy()))
        
        return self.concentration_history
    
    def evaluate_compliance(self) -> Dict[str, Tuple[float, bool]]:
        """Evaluate if final effluent meets recommended limits."""
        if not self.concentration_history:
            self.run_simulation()
            
        final_effluent = self.concentration_history[-1][1]
        compliance = {}
        
        for param, value in final_effluent.items():
            if param == 'pH':  # pH doesn't have a specified limit in the data
                compliance[param] = (value, True)
                continue
                
            if param not in self.effluent_limits:
                continue
                
            limit = self.effluent_limits[param]
            
            if isinstance(limit, tuple):  # Range check (for alkalinity)
                meets_limit = limit[0] <= value <= limit[1]
            else:
                meets_limit = value <= limit
                
            compliance[param] = (value, meets_limit)
            
        return compliance
    
    def print_results(self):
        """Print the simulation results in a readable format."""
        if not self.concentration_history:
            self.run_simulation()
            
        print(f"\n{'='*50}")
        print(f"TROPICAL TIMBER PAPER MILL WASTEWATER TREATMENT SIMULATION")
        print(f"Treatment Plan {self.plan} Results")
        print(f"{'='*50}\n")
        
        # Print concentrations at each stage
        headers = ["Parameter"] + [stage[0] for stage in self.concentration_history]
        params = list(self.raw_wastewater.keys())
        
        # Prepare data for printing
        data = []
        for param in params:
            row = [param]
            for stage in self.concentration_history:
                row.append(f"{stage[1][param]:.2f}")
            data.append(row)
        
        # Print the table
        print(tabulate(data, headers=headers, tablefmt="grid"))
        
        # Print compliance results
        print("\nFINAL EFFLUENT COMPLIANCE CHECK:")
        compliance = self.evaluate_compliance()
        compliance_data = []
        for param, (value, meets) in compliance.items():
            status = "PASS" if meets else "FAIL"
            if isinstance(self.effluent_limits.get(param, 0), tuple):
                limit = f"{self.effluent_limits[param][0]}-{self.effluent_limits[param][1]}"
            else:
                limit = f"≤{self.effluent_limits.get(param, 'N/A')}"
            compliance_data.append([param, f"{value:.2f}", limit, status])
        
        print(tabulate(compliance_data, 
                      headers=["Parameter", "Effluent Value", "Limit", "Status"], 
                      tablefmt="grid"))
    
    # Treatment unit functions
    def fine_screen(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Fine Screen treatment unit."""
        # Mid-point removal efficiencies
        removals = {
            'BOD': 0.025,  # 0-5%
            'COD': 0.0,    # 0%
            'TSS': 0.10,  # 5-15%
            'TDS': 0.0,    # 0%
            'Total Color': 0.0,  # 0%
            'Turbidity': 0.025,  # 0-5%
            'Conductivity': 0.025,  # <5%
            'Alkalinity': 0.025,  # <5%
            'Total Nitrates': 0.025,  # <5%
            'Total Phosphates': 0.025,  # <5%
            'Total Zinc': 0.05  # assumed 5% removal
        }
        
        # Apply removals
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        return new_concentrations
    
    def plain_sedimentation(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Plain Sedimentation treatment unit (Plan 1)."""
        removals = {
            'BOD': 0.325,  # 25-40%
            'COD': 0.25,  # 20-30%
            'TSS': 0.60,  # 50-70%
            'TDS': 0.0,    # 0%
            'Total Color': 0.15,  # 10-20%
            'Turbidity': 0.40,  # 30-50%
            'Conductivity': 0.025,  # <5%
            'Alkalinity': 0.025,  # <5%
            'Total Nitrates': 0.025,  # <5%
            'Total Phosphates': 0.15,  # 10-20%
            'Total Zinc': 0.30  # assumed 30% removal
        }
        
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        return new_concentrations
    
    def coagulation_tank(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Coagulation Tank treatment unit (Plan 2)."""
        removals = {
            'BOD': 0.20,  # 15-25%
            'COD': 0.30,  # 20-40%
            'TSS': 0.55,  # 40-70%
            'TDS': 0.075,  # 5-10%
            'Total Color': 0.50,  # 40-60%
            'Turbidity': 0.65,  # 50-80%
            'Conductivity': 0.10,  # 5-15%
            'Alkalinity': 0.20,  # 10-30%
            'Total Nitrates': 0.20,  # 10-30%
            'Total Phosphates': 0.80,  # 70-90%
            'Total Zinc': 0.60  # assumed 60% removal
        }
        
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        return new_concentrations
    
    def flocculation_chamber(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Flocculation Chamber treatment unit (Plan 2)."""
        removals = {
            'BOD': 0.075,  # 5-10%
            'COD': 0.15,  # 10-20%
            'TSS': 0.30,  # 20-40%
            'TDS': 0.025,  # <5%
            'Total Color': 0.20,  # 10-30%
            'Turbidity': 0.45,  # 30-60%
            'Conductivity': 0.025,  # <5%
            'Alkalinity': 0.025,  # <5%
            'Total Nitrates': 0.025,  # <5%
            'Total Phosphates': 0.15,  # 10-20%
            'Total Zinc': 0.20  # assumed 20% removal
        }
        
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        return new_concentrations
    
    def sedimentation(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Sedimentation treatment unit (Plan 2)."""
        removals = {
            'BOD': 0.50,  # 40-60%
            'COD': 0.35,  # 20-50%
            'TSS': 0.70,  # 60-80%
            'TDS': 0.0,    # 0%
            'Total Color': 0.30,  # 20-40%
            'Turbidity': 0.55,  # 40-70%
            'Conductivity': 0.025,  # <5%
            'Alkalinity': 0.025,  # <5%
            'Total Nitrates': 0.025,  # <5%
            'Total Phosphates': 0.875,  # 80-95%
            'Total Zinc': 0.50  # assumed 50% removal
        }
        
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        return new_concentrations
    
    def electrocoagulation(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Electrocoagulation treatment unit."""
        if self.plan == 1:
            removals = {
                'BOD': 0.725,  # 60-85%
                'COD': 0.725,  # 60-85%
                'TSS': 0.825,  # 70-95%
                'TDS': 0.20,  # 10-30%
                'Total Color': 0.725,  # 50-95%
                'Turbidity': 0.875,  # 80-95%
                'Conductivity': 0.20,  # 10-30%
                'Alkalinity': 0.20,  # 10-30%
                'Total Nitrates': 0.30,  # 20-40%
                'Total Phosphates': 0.80,  # 70-90%
                'Total Zinc': 0.85  # assumed 85% removal
            }
        else:
            removals = {
                'BOD': 0.75,  # 60-90%
                'COD': 0.725,  # 60-85%
                'TSS': 0.825,  # 70-95%
                'TDS': 0.20,  # 10-30%
                'Total Color': 0.73,  # 50-96%
                'Turbidity': 0.825,  # 70-95%
                'Conductivity': 0.20,  # 10-30%
                'Alkalinity': 0.20,  # 10-30%
                'Total Nitrates': 0.30,  # 20-40%
                'Total Phosphates': 0.80,  # 70-90%
                'Total Zinc': 0.85  # assumed 85% removal
            }
        
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        # Adjust pH due to electrocoagulation
        new_concentrations['pH'] = self._adjust_pH(concentrations['pH'])
        
        return new_concentrations
    
    def rapid_sand_filter(self, concentrations: Dict[str, float]) -> Dict[str, float]:
        """Model the Rapid Sand Filter treatment unit."""
        removals = {
            'BOD': 0.20,  # 10-30%
            'COD': 0.10,  # 5-15%
            'TSS': 0.875,  # 80-95%
            'TDS': 0.0,    # 0%
            'Total Color': 0.30,  # 20-40%
            'Turbidity': 0.895,  # 80-99%
            'Conductivity': 0.025,  # <5%
            'Alkalinity': 0.025,  # <5%
            'Total Nitrates': 0.025,  # <5%
            'Total Phosphates': 0.30,  # 20-40%
            'Total Zinc': 0.20  # assumed 20% removal
        }
        
        new_concentrations = concentrations.copy()
        for param, removal in removals.items():
            new_concentrations[param] *= (1 - removal)
            
        return new_concentrations
    
    def _adjust_pH(self, current_pH: float) -> float:
        """Adjust pH based on electrocoagulation effects."""
        # Electrocoagulation can affect pH depending on electrode material and wastewater composition
        # This is a simplified model - in reality, pH changes would depend on many factors
        if current_pH < 7:
            return min(current_pH * 1.1, 7.0)  # Slight increase if acidic
        elif current_pH > 8:
            return max(current_pH * 0.95, 7.5)  # Slight decrease if basic
        else:
            return current_pH  # Minimal change if near neutral


# Example usage
if __name__ == "__main__":
    from tabulate import tabulate
    
    print("Tropical Timber Paper Mill Wastewater Treatment Simulation")
    
    # Run Plan 1 simulation
    print("\nRunning Plan 1 Simulation...")
    plan1_sim = WastewaterTreatmentSimulation(plan=1)
    plan1_results = plan1_sim.run_simulation()
    plan1_sim.print_results()
    
    # Run Plan 2 simulation
    print("\nRunning Plan 2 Simulation...")
    plan2_sim = WastewaterTreatmentSimulation(plan=2)
    plan2_results = plan2_sim.run_simulation()
    plan2_sim.print_results()
