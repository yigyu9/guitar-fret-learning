"""Pre-tanh Action Residual Coordinator prototype.

This package deliberately does not expose or modify source-policy hidden
activations.  A future latent synchronizer belongs in ``full.latent_sync`` and
must use a different architecture identifier.
"""

from .config import ActionResidualConfig
from .action_safety import (
    ActionSafetyMasks,
    DirectionalPreTanhCaps,
    SafeResidualResult,
    apply_physical_residual,
    bound_raw_residual,
    directional_pre_tanh_caps,
    stable_atanh,
)
from .critic import (
    DEFAULT_VALUE_HEAD_NAMES,
    CentralCriticConfig,
    CentralMultiHeadCritic,
)
from .context_encoding import (
    GUITAR_SUPPORT_MANIFEST,
    PRIVILEGED_MANIFEST,
    READINESS_MANIFEST,
    AggregateSupportEncodingInput,
    EncodingBlockManifest,
    EncodingField,
    ExactContactEncodingInput,
    ExactTetherEncodingInput,
    GuitarSupportEncodingInput,
    GuitarSupportPacker,
    JointHistoryEncodingInput,
    JointHistoryPacker,
    PrivilegedEncodingInput,
    PrivilegedPacker,
    ReadinessEncodingInput,
    ReadinessPacker,
    SupportSiteEncodingInput,
    TetherEncodingInput,
)
from .context_pipeline import (
    CONTEXT_PIPELINE_ID,
    ActionResidualContextPacker,
    PackedActorContext,
    PackedCriticContext,
)
from .distribution import JointActionSample, MaskedJointTanhNormal
from .goal_encoder import (
    EventTokenEncoder,
    GoalScoreBatch,
    GoalScoreEncoder,
    GoalScoreEncoding,
)
from .manifest import (
    ACTION_RESIDUAL_ARCHITECTURE_ID,
    CURRENT_PROFILE_BODY_RESIDUAL_DIM,
    CURRENT_PROFILE_JOINT_DIM,
    ActionResidualManifest,
)
from .model import ActionResidualCoordinator, ActionResidualOutput
from .source_adapter import (
    RAW_SOURCE_OBSERVATION_ID,
    FrozenSourcePolicyAdapter,
    RawSourceObservation,
    SourceProposal,
)
from .source_projection import (
    PROJECTED_SOURCE_VIEW_ID,
    FrozenSourceObservationProjector,
    ProjectedSourceObservation,
    SourceProjectionManifest,
)
from .source_intent import (
    CALIBRATED,
    CALIBRATION_REQUIRED,
    SOURCE_INTENT_ENCODING_ID,
    SourceIntentCalibration,
    SourceIntentNormalizer,
    calibrate_source_intent,
)

__all__ = [
    "ACTION_RESIDUAL_ARCHITECTURE_ID",
    "ActionResidualConfig",
    "ActionResidualContextPacker",
    "ActionResidualCoordinator",
    "ActionResidualManifest",
    "ActionResidualOutput",
    "ActionSafetyMasks",
    "CentralCriticConfig",
    "CentralMultiHeadCritic",
    "CONTEXT_PIPELINE_ID",
    "CURRENT_PROFILE_BODY_RESIDUAL_DIM",
    "CURRENT_PROFILE_JOINT_DIM",
    "CALIBRATED",
    "CALIBRATION_REQUIRED",
    "DEFAULT_VALUE_HEAD_NAMES",
    "DirectionalPreTanhCaps",
    "EncodingBlockManifest",
    "EncodingField",
    "ExactContactEncodingInput",
    "ExactTetherEncodingInput",
    "FrozenSourcePolicyAdapter",
    "EventTokenEncoder",
    "GoalScoreBatch",
    "GoalScoreEncoder",
    "GoalScoreEncoding",
    "GUITAR_SUPPORT_MANIFEST",
    "GuitarSupportEncodingInput",
    "GuitarSupportPacker",
    "JointHistoryEncodingInput",
    "JointHistoryPacker",
    "JointActionSample",
    "MaskedJointTanhNormal",
    "PROJECTED_SOURCE_VIEW_ID",
    "RAW_SOURCE_OBSERVATION_ID",
    "PRIVILEGED_MANIFEST",
    "PackedActorContext",
    "PackedCriticContext",
    "PrivilegedEncodingInput",
    "PrivilegedPacker",
    "READINESS_MANIFEST",
    "ReadinessEncodingInput",
    "ReadinessPacker",
    "RawSourceObservation",
    "SOURCE_INTENT_ENCODING_ID",
    "FrozenSourceObservationProjector",
    "ProjectedSourceObservation",
    "SourceProposal",
    "SourceProjectionManifest",
    "SourceIntentCalibration",
    "SourceIntentNormalizer",
    "SafeResidualResult",
    "AggregateSupportEncodingInput",
    "SupportSiteEncodingInput",
    "TetherEncodingInput",
    "apply_physical_residual",
    "bound_raw_residual",
    "calibrate_source_intent",
    "directional_pre_tanh_caps",
    "stable_atanh",
]
