dnl Options:
dnl   poison[=TIME]  Grow poisonous food items
dnl                  Reach full potency at TIME (default: 20000)
dnl   quiet          Suppress recording of agent-specific data
define(`min_max', `Min$1 $2; Max$1 ifelse($3, `', `Min$1', `$3')')dnl
define(`verbose', `ifdef(`quiet', `False', `True')')dnl
@version 2

# ----------
# Simulation
# ----------
MaxSteps 30000

# -----------
# Environment
# -----------
Barriers []
Domains [
    {
        FoodPatches [
            {
                FoodTypeName "Food"
            }ifdef(`poison', `,
            {
                FoodFraction 0.0
                FoodRate FoodGrowthRate
                FoodTypeName "Poison"
                MaxFoodFraction 1.0
                MaxFoodGrownFraction 1.0
            }')
        ]
    }
]
FoodColor {
    R 0.0
    G 1.0
    B 0.0
}
GroundColor {
    R 0.0
    G 0.25
    B 0.0
}

# ----
# Food
# ----
min_max(Food, 0, 10000)
min_max(FoodEnergy, 500.0)
FoodEnergySizeScale 250.0
FoodGrowthRate 0.5
FoodMaxLifeSpan 250
FoodTypes [
    {
        EnergyPolarity [ 1 ]
        Name "Food"
    }ifdef(`poison', `,
    {
        EatMultiplier [
            dyn(-sys.float_info.min) {
                static float min = -std::numeric_limits<float>::min();
                static float max = -1.0f;
                static float range = max - min;
                static long time = ifelse(poison, `', `20000', `poison')L;
                return Step < time
                    ? min + range * Step / time
                    : max;
            }
        ]
        EnergyPolarity [ -1 ]
        FoodColor {
            R 1.0
            G 0.0
            B 0.0
        }
        Name "Poison"
    }')
]
InitFood 0
ProbabilisticFoodPatches False
RandomInitFoodAge True

# ----------
# Population
# ----------
min_max(Agents, 50, 1000)
EndOnPopulationCrash True
EnergyBasedPopulationControl False
InitAgents 200

# ----------
# Energetics
# ----------
AgeEnergyMultiplier 0.002
min_max(AgentMaxEnergy, 500.0)
DamageRate 5.0
EnergyUseEat 0.01
EnergyUseFight (0.1 * DamageRate)
EnergyUseFixed 0.1
EnergyUseFocus 0.001
EnergyUseMate 0.1
EnergyUseMove 0.1
EnergyUseMultiplier dyn(1.0) {
    return AgentCount > InitAgents
        ? pow((float)AgentCount / InitAgents - 1.0f, 2.0f) + 1.0f
        : 1.0f;
}
EnergyUseNeurons 0.1
EnergyUseSynapses 0.1
EnergyUseTurn 0.1
MinMateEnergyFraction 0.5
RandomSeedEnergy True
min_max(SizeEnergyPenalty, 1.0, (MaxAgentSize / MinAgentSize))

# ----------
# Physiology
# ----------
min_max(AgentMaxSpeed, 1.0)
min_max(AgentSize, 1.0)
min_max(AgentStrength, 1.0)
BodyGreenChannel F
EnableMateWaitFeedback True
EnableSpeedFeedback True
min_max(EnergyFractionToOffspring, 0.5)
min_max(HorizontalFieldOfView,
    (MaxVisionNeuronsPerGroup * 2.0),
    (MaxVisionNeuronsPerGroup * 20.0))
InvertFocus True
InvertMateWaitFeedback True
MateWait 25
MaxSizeFightAdvantage MaxSizeEnergyPenalty
NoseColor B
ProbabilisticMating True
RandomSeedMateWait True
RetinaWidth (MaxVisionNeuronsPerGroup * 2)
YawRate MinHorizontalFieldOfView

# ------------
# Neural Model
# ------------
min_max(ExcitatoryNeuronsPerGroup, 0, MaxVisionNeuronsPerGroup)
FixedInitSynapseWeight True
min_max(InhibitoryNeuronsPerGroup, 0, MaxVisionNeuronsPerGroup)
min_max(InternalNeuralGroups, 0, 10)
LearningMode Prebirth
min_max(LearningRate, 0.004)
MaxSynapseWeight 5.0
MaxSynapseWeightInitial 0.5
MirroredTopologicalDistortion True
OrderedInternalNeuralGroups True
PreBirthCycles int(
    (MaxSynapseWeight - MaxSynapseWeightInitial)
    / (MaxLearningRate * 0.25))
SimpleSeedYawBiasDelta (0.5 / MaxBiasWeight)
SynapseWeightDecayRate (1.0 - MaxLearningRate * 0.25 / MaxSynapseWeight)
min_max(VisionNeuronsPerGroup, 7)

# -------------
# Genetic Model
# -------------
min_max(CrossoverPoints, 1)
DieAtMaxAge False
GeneticOperatorResolution Byte
min_max(LifeSpan, MaxSteps)
min_max(MutationRate, 1.0)
min_max(MutationStdevPower, 4.0)
SeedType Simple

# ---------
# Recording
# ---------
RecordAgentEnergy verbose
RecordBirthsDeaths True
RecordBrainAnatomy verbose
RecordBrainFunction verbose
RecordFoodConsumption True
RecordFoodEnergy True
RecordGenomes verbose
RecordGitRevision True
RecordPopulation True
RecordSynapses verbose
